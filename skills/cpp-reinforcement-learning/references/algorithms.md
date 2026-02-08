# RL Algorithm Implementations in C++

## Deep Q-Network (DQN)

### Network Architecture

```cpp
#include <torch/torch.h>

struct DQNNet : torch::nn::Module {
    torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr};

    DQNNet(int64_t state_dim, int64_t action_dim) {
        fc1 = register_module("fc1", torch::nn::Linear(state_dim, 128));
        fc2 = register_module("fc2", torch::nn::Linear(128, 128));
        fc3 = register_module("fc3", torch::nn::Linear(128, action_dim));
    }

    torch::Tensor forward(torch::Tensor x) {
        x = torch::relu(fc1->forward(x));
        x = torch::relu(fc2->forward(x));
        return fc3->forward(x);
    }
};
```

### Dueling DQN Architecture

```cpp
struct DuelingDQN : torch::nn::Module {
    torch::nn::Linear feature{nullptr};
    torch::nn::Linear value_stream{nullptr};
    torch::nn::Linear advantage_stream{nullptr};

    DuelingDQN(int64_t state_dim, int64_t action_dim) {
        feature = register_module("feature", torch::nn::Linear(state_dim, 128));
        value_stream = register_module("value", torch::nn::Linear(128, 1));
        advantage_stream = register_module("advantage", torch::nn::Linear(128, action_dim));
    }

    torch::Tensor forward(torch::Tensor x) {
        x = torch::relu(feature->forward(x));
        auto value = value_stream->forward(x);
        auto advantage = advantage_stream->forward(x);
        // Q = V + (A - mean(A))
        return value + advantage - advantage.mean(1, true);
    }
};
```

### DQN Agent Class

```cpp
class DQNAgent {
public:
    DQNAgent(int64_t state_dim, int64_t action_dim, double lr = 1e-3,
             double gamma = 0.99, double epsilon_start = 1.0,
             double epsilon_end = 0.01, int64_t epsilon_decay = 10000)
        : state_dim_(state_dim), action_dim_(action_dim), gamma_(gamma),
          epsilon_(epsilon_start), epsilon_end_(epsilon_end),
          epsilon_decay_(epsilon_decay), step_count_(0) {

        device_ = torch::cuda::is_available() ? torch::kCUDA : torch::kCPU;

        policy_net_ = std::make_shared<DQNNet>(state_dim, action_dim);
        target_net_ = std::make_shared<DQNNet>(state_dim, action_dim);
        policy_net_->to(device_);
        target_net_->to(device_);

        // Copy weights to target
        update_target_network();

        optimizer_ = std::make_unique<torch::optim::Adam>(
            policy_net_->parameters(), torch::optim::AdamOptions(lr));
    }

    int64_t select_action(torch::Tensor state) {
        // Epsilon-greedy action selection
        epsilon_ = epsilon_end_ + (epsilon_ - epsilon_end_) *
                   std::exp(-1.0 * step_count_ / epsilon_decay_);
        step_count_++;

        if (dist_(rng_) < epsilon_) {
            return action_dist_(rng_);
        }

        torch::NoGradGuard no_grad;
        policy_net_->eval();
        auto q_values = policy_net_->forward(state.to(device_));
        policy_net_->train();
        return q_values.argmax(1).item<int64_t>();
    }

    void train_step(const std::vector<Experience>& batch) {
        // Stack batch into tensors
        std::vector<torch::Tensor> states, next_states;
        std::vector<int64_t> actions;
        std::vector<float> rewards;
        std::vector<float> dones;

        for (const auto& exp : batch) {
            states.push_back(exp.state);
            actions.push_back(exp.action);
            rewards.push_back(exp.reward);
            next_states.push_back(exp.next_state);
            dones.push_back(exp.done ? 1.0f : 0.0f);
        }

        auto state_batch = torch::stack(states).to(device_);
        auto action_batch = torch::tensor(actions).to(device_).unsqueeze(1);
        auto reward_batch = torch::tensor(rewards).to(device_);
        auto next_state_batch = torch::stack(next_states).to(device_);
        auto done_batch = torch::tensor(dones).to(device_);

        // Compute Q(s, a)
        auto q_values = policy_net_->forward(state_batch).gather(1, action_batch).squeeze();

        // Compute target: r + gamma * max_a' Q_target(s', a')
        torch::Tensor next_q_values;
        {
            torch::NoGradGuard no_grad;
            next_q_values = target_net_->forward(next_state_batch).max(1).values;
        }
        auto target = reward_batch + gamma_ * next_q_values * (1 - done_batch);

        // Huber loss (more stable than MSE)
        auto loss = torch::smooth_l1_loss(q_values, target.detach());

        // Optimize
        optimizer_->zero_grad();
        loss.backward();
        // Gradient clipping
        torch::nn::utils::clip_grad_norm_(policy_net_->parameters(), 1.0);
        optimizer_->step();
    }

    void update_target_network() {
        auto policy_params = policy_net_->named_parameters();
        auto target_params = target_net_->named_parameters();

        torch::NoGradGuard no_grad;
        for (auto& param : target_params) {
            auto& name = param.key();
            param.value().copy_(policy_params[name]);
        }
    }

    void soft_update_target(double tau = 0.005) {
        auto policy_params = policy_net_->named_parameters();
        auto target_params = target_net_->named_parameters();

        torch::NoGradGuard no_grad;
        for (auto& param : target_params) {
            auto& name = param.key();
            param.value().copy_(
                tau * policy_params[name] + (1 - tau) * param.value()
            );
        }
    }

private:
    std::shared_ptr<DQNNet> policy_net_;
    std::shared_ptr<DQNNet> target_net_;
    std::unique_ptr<torch::optim::Adam> optimizer_;
    torch::Device device_{torch::kCPU};

    int64_t state_dim_, action_dim_;
    double gamma_, epsilon_, epsilon_end_;
    int64_t epsilon_decay_, step_count_;

    std::mt19937 rng_{std::random_device{}()};
    std::uniform_real_distribution<double> dist_{0.0, 1.0};
    std::uniform_int_distribution<int64_t> action_dist_{0, action_dim_ - 1};
};
```

## Proximal Policy Optimization (PPO)

### Actor-Critic Network

```cpp
struct ActorCritic : torch::nn::Module {
    torch::nn::Linear shared1{nullptr}, shared2{nullptr};
    torch::nn::Linear policy_mean{nullptr};
    torch::nn::Linear policy_log_std{nullptr};
    torch::nn::Linear value_head{nullptr};

    int64_t action_dim_;

    ActorCritic(int64_t state_dim, int64_t action_dim, int64_t hidden_dim = 64)
        : action_dim_(action_dim) {
        shared1 = register_module("shared1", torch::nn::Linear(state_dim, hidden_dim));
        shared2 = register_module("shared2", torch::nn::Linear(hidden_dim, hidden_dim));
        policy_mean = register_module("policy_mean", torch::nn::Linear(hidden_dim, action_dim));
        policy_log_std = register_module("policy_log_std", torch::nn::Linear(hidden_dim, action_dim));
        value_head = register_module("value", torch::nn::Linear(hidden_dim, 1));
    }

    torch::Tensor forward_shared(torch::Tensor x) {
        x = torch::tanh(shared1->forward(x));
        x = torch::tanh(shared2->forward(x));
        return x;
    }

    std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> forward(torch::Tensor x) {
        auto features = forward_shared(x);
        auto mean = policy_mean->forward(features);
        auto log_std = policy_log_std->forward(features).clamp(-20, 2);
        auto value = value_head->forward(features);
        return {mean, log_std, value};
    }

    torch::Tensor get_value(torch::Tensor x) {
        auto features = forward_shared(x);
        return value_head->forward(features);
    }

    std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> evaluate_actions(
        torch::Tensor states, torch::Tensor actions) {
        auto [mean, log_std, value] = forward(states);
        auto std = log_std.exp();

        // Compute log probability of actions
        auto var = std.pow(2);
        auto log_prob = -0.5 * (((actions - mean).pow(2) / var) +
                                2 * log_std + std::log(2 * M_PI));
        log_prob = log_prob.sum(-1, true);

        // Entropy for exploration bonus
        auto entropy = 0.5 * (1 + std::log(2 * M_PI) + 2 * log_std).sum(-1).mean();

        return {log_prob, value, entropy};
    }

    std::pair<torch::Tensor, torch::Tensor> sample_action(torch::Tensor state) {
        auto [mean, log_std, value] = forward(state);
        auto std = log_std.exp();

        // Sample from Gaussian
        auto noise = torch::randn_like(mean);
        auto action = mean + std * noise;

        // Compute log probability
        auto var = std.pow(2);
        auto log_prob = -0.5 * (((action - mean).pow(2) / var) +
                                2 * log_std + std::log(2 * M_PI));
        log_prob = log_prob.sum(-1, true);

        return {action, log_prob};
    }
};
```

### PPO Update

```cpp
struct PPOConfig {
    double clip_epsilon = 0.2;
    double value_loss_coef = 0.5;
    double entropy_coef = 0.01;
    double max_grad_norm = 0.5;
    int64_t ppo_epochs = 10;
    int64_t mini_batch_size = 64;
    double gae_lambda = 0.95;
    double gamma = 0.99;
};

class PPOAgent {
public:
    PPOAgent(int64_t state_dim, int64_t action_dim, const PPOConfig& config)
        : config_(config) {
        device_ = torch::cuda::is_available() ? torch::kCUDA : torch::kCPU;

        actor_critic_ = std::make_shared<ActorCritic>(state_dim, action_dim);
        actor_critic_->to(device_);

        optimizer_ = std::make_unique<torch::optim::Adam>(
            actor_critic_->parameters(), torch::optim::AdamOptions(3e-4));
    }

    void update(RolloutBuffer& buffer) {
        auto [states, actions, old_log_probs, returns, advantages] =
            buffer.get_tensors(device_);

        // Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8);

        for (int64_t epoch = 0; epoch < config_.ppo_epochs; ++epoch) {
            auto indices = torch::randperm(states.size(0));

            for (int64_t start = 0; start < states.size(0); start += config_.mini_batch_size) {
                auto end = std::min(start + config_.mini_batch_size, states.size(0));
                auto batch_indices = indices.slice(0, start, end);

                auto batch_states = states.index_select(0, batch_indices);
                auto batch_actions = actions.index_select(0, batch_indices);
                auto batch_old_log_probs = old_log_probs.index_select(0, batch_indices);
                auto batch_returns = returns.index_select(0, batch_indices);
                auto batch_advantages = advantages.index_select(0, batch_indices);

                // Evaluate actions with current policy
                auto [log_probs, values, entropy] =
                    actor_critic_->evaluate_actions(batch_states, batch_actions);

                // Policy loss with clipping
                auto ratio = (log_probs - batch_old_log_probs).exp();
                auto surr1 = ratio * batch_advantages;
                auto surr2 = ratio.clamp(1 - config_.clip_epsilon,
                                         1 + config_.clip_epsilon) * batch_advantages;
                auto policy_loss = -torch::min(surr1, surr2).mean();

                // Value loss
                auto value_loss = torch::mse_loss(values.squeeze(), batch_returns);

                // Total loss
                auto loss = policy_loss +
                           config_.value_loss_coef * value_loss -
                           config_.entropy_coef * entropy;

                // Optimize
                optimizer_->zero_grad();
                loss.backward();
                torch::nn::utils::clip_grad_norm_(actor_critic_->parameters(),
                                                   config_.max_grad_norm);
                optimizer_->step();
            }
        }
    }

    // Compute Generalized Advantage Estimation
    std::vector<float> compute_gae(
        const std::vector<float>& rewards,
        const std::vector<float>& values,
        const std::vector<bool>& dones,
        float last_value
    ) {
        std::vector<float> advantages(rewards.size());
        float gae = 0;

        for (int64_t t = rewards.size() - 1; t >= 0; --t) {
            float next_value = (t == rewards.size() - 1) ? last_value : values[t + 1];
            float next_non_terminal = dones[t] ? 0.0f : 1.0f;

            float delta = rewards[t] + config_.gamma * next_value * next_non_terminal - values[t];
            gae = delta + config_.gamma * config_.gae_lambda * next_non_terminal * gae;
            advantages[t] = gae;
        }

        return advantages;
    }

private:
    std::shared_ptr<ActorCritic> actor_critic_;
    std::unique_ptr<torch::optim::Adam> optimizer_;
    torch::Device device_{torch::kCPU};
    PPOConfig config_;
};
```

## Soft Actor-Critic (SAC)

### SAC Networks

```cpp
// Soft Q-Network (two Q-networks for stability)
struct SoftQNetwork : torch::nn::Module {
    torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr};

    SoftQNetwork(int64_t state_dim, int64_t action_dim, int64_t hidden_dim = 256) {
        fc1 = register_module("fc1", torch::nn::Linear(state_dim + action_dim, hidden_dim));
        fc2 = register_module("fc2", torch::nn::Linear(hidden_dim, hidden_dim));
        fc3 = register_module("fc3", torch::nn::Linear(hidden_dim, 1));
    }

    torch::Tensor forward(torch::Tensor state, torch::Tensor action) {
        auto x = torch::cat({state, action}, 1);
        x = torch::relu(fc1->forward(x));
        x = torch::relu(fc2->forward(x));
        return fc3->forward(x);
    }
};

// Gaussian Policy for SAC
struct GaussianPolicy : torch::nn::Module {
    torch::nn::Linear fc1{nullptr}, fc2{nullptr};
    torch::nn::Linear mean_head{nullptr}, log_std_head{nullptr};

    float log_std_min_ = -20.0f;
    float log_std_max_ = 2.0f;
    float action_scale_;

    GaussianPolicy(int64_t state_dim, int64_t action_dim,
                   int64_t hidden_dim = 256, float action_scale = 1.0f)
        : action_scale_(action_scale) {
        fc1 = register_module("fc1", torch::nn::Linear(state_dim, hidden_dim));
        fc2 = register_module("fc2", torch::nn::Linear(hidden_dim, hidden_dim));
        mean_head = register_module("mean", torch::nn::Linear(hidden_dim, action_dim));
        log_std_head = register_module("log_std", torch::nn::Linear(hidden_dim, action_dim));
    }

    std::tuple<torch::Tensor, torch::Tensor> forward(torch::Tensor state) {
        auto x = torch::relu(fc1->forward(state));
        x = torch::relu(fc2->forward(x));
        auto mean = mean_head->forward(x);
        auto log_std = log_std_head->forward(x).clamp(log_std_min_, log_std_max_);
        return {mean, log_std};
    }

    std::tuple<torch::Tensor, torch::Tensor> sample(torch::Tensor state) {
        auto [mean, log_std] = forward(state);
        auto std = log_std.exp();

        // Reparameterization trick
        auto noise = torch::randn_like(mean);
        auto x_t = mean + std * noise;

        // Squash through tanh
        auto action = torch::tanh(x_t) * action_scale_;

        // Compute log probability with correction for tanh squashing
        auto log_prob = -0.5 * (noise.pow(2) + 2 * log_std + std::log(2 * M_PI));
        log_prob = log_prob.sum(-1, true);
        // Jacobian correction for tanh
        log_prob -= (2 * (std::log(2.0) - x_t - torch::softplus(-2 * x_t))).sum(-1, true);

        return {action, log_prob};
    }
};
```

### SAC Agent

```cpp
class SACAgent {
public:
    SACAgent(int64_t state_dim, int64_t action_dim,
             double lr = 3e-4, double gamma = 0.99, double tau = 0.005,
             double alpha = 0.2, bool auto_entropy = true)
        : gamma_(gamma), tau_(tau), alpha_(alpha), auto_entropy_(auto_entropy) {

        device_ = torch::cuda::is_available() ? torch::kCUDA : torch::kCPU;

        // Initialize networks
        policy_ = std::make_shared<GaussianPolicy>(state_dim, action_dim);
        q1_ = std::make_shared<SoftQNetwork>(state_dim, action_dim);
        q2_ = std::make_shared<SoftQNetwork>(state_dim, action_dim);
        q1_target_ = std::make_shared<SoftQNetwork>(state_dim, action_dim);
        q2_target_ = std::make_shared<SoftQNetwork>(state_dim, action_dim);

        policy_->to(device_);
        q1_->to(device_);
        q2_->to(device_);
        q1_target_->to(device_);
        q2_target_->to(device_);

        // Copy to targets
        hard_update(q1_target_, q1_);
        hard_update(q2_target_, q2_);

        // Optimizers
        policy_optimizer_ = std::make_unique<torch::optim::Adam>(
            policy_->parameters(), torch::optim::AdamOptions(lr));
        q_optimizer_ = std::make_unique<torch::optim::Adam>(
            concat_params(q1_->parameters(), q2_->parameters()),
            torch::optim::AdamOptions(lr));

        // Automatic entropy tuning
        if (auto_entropy_) {
            target_entropy_ = -static_cast<float>(action_dim);
            log_alpha_ = torch::zeros({1}, torch::requires_grad()).to(device_);
            alpha_optimizer_ = std::make_unique<torch::optim::Adam>(
                std::vector<torch::Tensor>{log_alpha_},
                torch::optim::AdamOptions(lr));
        }
    }

    torch::Tensor select_action(torch::Tensor state, bool deterministic = false) {
        torch::NoGradGuard no_grad;
        auto state_t = state.to(device_);

        if (deterministic) {
            auto [mean, _] = policy_->forward(state_t);
            return torch::tanh(mean) * policy_->action_scale_;
        } else {
            auto [action, _] = policy_->sample(state_t);
            return action;
        }
    }

    void update(ReplayBuffer& buffer, int64_t batch_size) {
        auto batch = buffer.sample(batch_size);

        // Convert to tensors
        auto states = stack_experiences(batch, &Experience::state).to(device_);
        auto actions = stack_experiences(batch, &Experience::action).to(device_);
        auto rewards = stack_experiences(batch, &Experience::reward).to(device_);
        auto next_states = stack_experiences(batch, &Experience::next_state).to(device_);
        auto dones = stack_experiences(batch, &Experience::done).to(device_);

        // Update Q-functions
        torch::Tensor q1_loss, q2_loss;
        {
            torch::NoGradGuard no_grad;
            auto [next_actions, next_log_probs] = policy_->sample(next_states);
            auto q1_next = q1_target_->forward(next_states, next_actions);
            auto q2_next = q2_target_->forward(next_states, next_actions);
            auto min_q_next = torch::min(q1_next, q2_next) - alpha_ * next_log_probs;
            auto q_target = rewards + gamma_ * (1 - dones) * min_q_next;
        }

        auto q1_pred = q1_->forward(states, actions);
        auto q2_pred = q2_->forward(states, actions);
        q1_loss = torch::mse_loss(q1_pred, q_target.detach());
        q2_loss = torch::mse_loss(q2_pred, q_target.detach());

        q_optimizer_->zero_grad();
        (q1_loss + q2_loss).backward();
        q_optimizer_->step();

        // Update policy
        auto [new_actions, log_probs] = policy_->sample(states);
        auto q1_new = q1_->forward(states, new_actions);
        auto q2_new = q2_->forward(states, new_actions);
        auto min_q_new = torch::min(q1_new, q2_new);
        auto policy_loss = (alpha_ * log_probs - min_q_new).mean();

        policy_optimizer_->zero_grad();
        policy_loss.backward();
        policy_optimizer_->step();

        // Update temperature
        if (auto_entropy_) {
            auto alpha_loss = -(log_alpha_ * (log_probs + target_entropy_).detach()).mean();
            alpha_optimizer_->zero_grad();
            alpha_loss.backward();
            alpha_optimizer_->step();
            alpha_ = log_alpha_.exp().item<double>();
        }

        // Soft update targets
        soft_update(q1_target_, q1_, tau_);
        soft_update(q2_target_, q2_, tau_);
    }

private:
    void hard_update(std::shared_ptr<SoftQNetwork>& target,
                     std::shared_ptr<SoftQNetwork>& source) {
        torch::NoGradGuard no_grad;
        auto target_params = target->named_parameters();
        auto source_params = source->named_parameters();
        for (auto& param : target_params) {
            param.value().copy_(source_params[param.key()]);
        }
    }

    void soft_update(std::shared_ptr<SoftQNetwork>& target,
                     std::shared_ptr<SoftQNetwork>& source, double tau) {
        torch::NoGradGuard no_grad;
        auto target_params = target->named_parameters();
        auto source_params = source->named_parameters();
        for (auto& param : target_params) {
            param.value().copy_(
                tau * source_params[param.key()] + (1 - tau) * param.value()
            );
        }
    }

    std::shared_ptr<GaussianPolicy> policy_;
    std::shared_ptr<SoftQNetwork> q1_, q2_, q1_target_, q2_target_;
    std::unique_ptr<torch::optim::Adam> policy_optimizer_, q_optimizer_, alpha_optimizer_;
    torch::Device device_{torch::kCPU};

    double gamma_, tau_, alpha_;
    bool auto_entropy_;
    float target_entropy_;
    torch::Tensor log_alpha_;
};
```

## Algorithm Selection Guide

| Algorithm | Use Case | Action Space | Sample Efficiency |
|-----------|----------|--------------|-------------------|
| DQN | Discrete actions, simple environments | Discrete | Medium |
| PPO | General purpose, continuous/discrete | Both | Low (needs many samples) |
| SAC | Continuous control, sample efficiency | Continuous | High |

### Hyperparameter Starting Points

**DQN**:
- Learning rate: 1e-4 to 1e-3
- Batch size: 32-128
- Replay buffer: 100k-1M
- Target update: Every 1000 steps or tau=0.005
- Epsilon decay: 10k-100k steps

**PPO**:
- Learning rate: 3e-4
- Clip epsilon: 0.1-0.2
- GAE lambda: 0.95
- PPO epochs: 4-10
- Mini-batch size: 64-256
- Rollout length: 128-2048

**SAC**:
- Learning rate: 3e-4
- Tau (soft update): 0.005
- Alpha (entropy): 0.2 or auto-tuned
- Batch size: 256
- Replay buffer: 1M
