# Testing and Debugging C++ RL Systems

## Deterministic Testing

### Seed Management

```cpp
#include <torch/torch.h>
#include <random>

class SeedManager {
public:
    static void set_global_seed(int seed) {
        // PyTorch seeds
        torch::manual_seed(seed);

        if (torch::cuda::is_available()) {
            torch::cuda::manual_seed(seed);
            torch::cuda::manual_seed_all(seed);  // Multi-GPU
        }

        // C++ random
        std::srand(seed);

        // Store for reproducibility logging
        current_seed_ = seed;
    }

    // Create seeded RNG for specific component
    static std::mt19937 create_rng(int seed) {
        return std::mt19937(seed);
    }

    // Get reproducible seed for child processes/threads
    static int get_worker_seed(int worker_id) {
        return current_seed_ + worker_id * 1000;
    }

private:
    static inline int current_seed_ = 0;
};

// CUDA deterministic settings (may impact performance)
void enable_deterministic_mode() {
    at::globalContext().setDeterministicCuDNN(true);
    at::globalContext().setBenchmarkCuDNN(false);
}
```

### Reproducible Experience Collection

```cpp
class DeterministicAgent {
public:
    DeterministicAgent(int seed) : rng_(seed), dist_(0.0, 1.0) {
        SeedManager::set_global_seed(seed);
    }

    int64_t select_action(torch::Tensor state, double epsilon) {
        if (dist_(rng_) < epsilon) {
            std::uniform_int_distribution<int64_t> action_dist(0, num_actions_ - 1);
            return action_dist(rng_);
        }

        torch::NoGradGuard no_grad;
        auto q_values = model_->forward(state);
        return q_values.argmax(1).item<int64_t>();
    }

private:
    std::mt19937 rng_;
    std::uniform_real_distribution<double> dist_;
    std::shared_ptr<DQNNet> model_;
    int64_t num_actions_;
};
```

## Unit Testing with Google Test

### Setting Up Google Test

```cmake
# CMakeLists.txt
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.1
)
FetchContent_MakeAvailable(googletest)

enable_testing()

add_executable(rl_tests
    tests/test_network.cpp
    tests/test_replay_buffer.cpp
    tests/test_agent.cpp
)

target_link_libraries(rl_tests
    GTest::gtest_main
    "${TORCH_LIBRARIES}"
)

include(GoogleTest)
gtest_discover_tests(rl_tests)
```

### Testing Neural Networks

```cpp
#include <gtest/gtest.h>
#include <torch/torch.h>
#include "dqn.h"

class DQNNetTest : public ::testing::Test {
protected:
    void SetUp() override {
        SeedManager::set_global_seed(42);
        model = std::make_shared<DQNNet>(4, 2);
    }

    std::shared_ptr<DQNNet> model;
};

TEST_F(DQNNetTest, ForwardPassShape) {
    auto input = torch::randn({32, 4});  // Batch of 32, state dim 4
    auto output = model->forward(input);

    EXPECT_EQ(output.sizes(), torch::IntArrayRef({32, 2}));
}

TEST_F(DQNNetTest, ForwardPassDeterministic) {
    SeedManager::set_global_seed(42);
    auto input = torch::randn({1, 4});

    auto output1 = model->forward(input);
    auto output2 = model->forward(input);

    EXPECT_TRUE(torch::allclose(output1, output2));
}

TEST_F(DQNNetTest, GradientFlow) {
    auto input = torch::randn({32, 4}, torch::requires_grad());
    auto output = model->forward(input);
    auto loss = output.sum();

    loss.backward();

    // Check all parameters have gradients
    for (const auto& param : model->parameters()) {
        EXPECT_TRUE(param.grad().defined());
        EXPECT_FALSE(torch::all(param.grad() == 0).item<bool>());
    }
}

TEST_F(DQNNetTest, ParameterCount) {
    size_t total_params = 0;
    for (const auto& param : model->parameters()) {
        total_params += param.numel();
    }

    // 4*128 + 128 + 128*128 + 128 + 128*2 + 2 = expected
    EXPECT_GT(total_params, 0);
}
```

### Testing Replay Buffer

```cpp
#include <gtest/gtest.h>
#include "replay_buffer.h"

class ReplayBufferTest : public ::testing::Test {
protected:
    void SetUp() override {
        buffer = std::make_unique<ReplayBuffer>(100);
    }

    Experience make_experience(int id) {
        return {
            torch::tensor({static_cast<float>(id)}),
            id % 4,
            static_cast<float>(id) * 0.1f,
            torch::tensor({static_cast<float>(id + 1)}),
            id % 10 == 0
        };
    }

    std::unique_ptr<ReplayBuffer> buffer;
};

TEST_F(ReplayBufferTest, InitiallyEmpty) {
    EXPECT_EQ(buffer->size(), 0);
    EXPECT_FALSE(buffer->can_sample(1));
}

TEST_F(ReplayBufferTest, PushAndSize) {
    for (int i = 0; i < 50; ++i) {
        buffer->push(make_experience(i));
    }

    EXPECT_EQ(buffer->size(), 50);
    EXPECT_TRUE(buffer->can_sample(32));
}

TEST_F(ReplayBufferTest, RingBufferOverwrite) {
    // Fill past capacity
    for (int i = 0; i < 150; ++i) {
        buffer->push(make_experience(i));
    }

    // Size should be capped at capacity
    EXPECT_EQ(buffer->size(), 100);
}

TEST_F(ReplayBufferTest, SampleBatchSize) {
    for (int i = 0; i < 100; ++i) {
        buffer->push(make_experience(i));
    }

    auto batch = buffer->sample(32);
    EXPECT_EQ(batch.size(), 32);
}

TEST_F(ReplayBufferTest, SampleContainsValidExperiences) {
    for (int i = 0; i < 100; ++i) {
        buffer->push(make_experience(i));
    }

    auto batch = buffer->sample(32);
    for (const auto& exp : batch) {
        EXPECT_EQ(exp.state.dim(), 1);
        EXPECT_GE(exp.action, 0);
        EXPECT_LT(exp.action, 4);
    }
}
```

### Testing Training Loop

```cpp
#include <gtest/gtest.h>
#include "dqn_agent.h"

TEST(DQNAgentTest, LossDecreases) {
    SeedManager::set_global_seed(42);

    DQNAgent agent(4, 2);
    ReplayBuffer buffer(1000);

    // Fill buffer with random experiences
    for (int i = 0; i < 500; ++i) {
        buffer.push({
            torch::randn({4}),
            rand() % 2,
            static_cast<float>(rand()) / RAND_MAX,
            torch::randn({4}),
            rand() % 10 == 0
        });
    }

    // Track loss over training
    std::vector<float> losses;

    for (int step = 0; step < 100; ++step) {
        auto batch = buffer.sample(32);
        float loss = agent.train_step(batch);
        losses.push_back(loss);
    }

    // Average loss should decrease
    float early_avg = std::accumulate(losses.begin(), losses.begin() + 20, 0.0f) / 20;
    float late_avg = std::accumulate(losses.end() - 20, losses.end(), 0.0f) / 20;

    EXPECT_LT(late_avg, early_avg);
}

TEST(DQNAgentTest, TargetNetworkUpdates) {
    SeedManager::set_global_seed(42);

    DQNAgent agent(4, 2);

    // Get initial target network output
    auto state = torch::randn({1, 4});
    auto initial_output = agent.get_target_values(state).clone();

    // Train for a while
    ReplayBuffer buffer(1000);
    for (int i = 0; i < 100; ++i) {
        buffer.push({torch::randn({4}), rand() % 2, 1.0f,
                    torch::randn({4}), false});
    }

    for (int i = 0; i < 50; ++i) {
        agent.train_step(buffer.sample(32));
    }

    // Update target network
    agent.update_target_network();

    auto updated_output = agent.get_target_values(state);

    EXPECT_FALSE(torch::allclose(initial_output, updated_output));
}
```

## Debugging Techniques

### Gradient Debugging

```cpp
class GradientDebugger {
public:
    static void check_gradients(torch::nn::Module& model, const std::string& name) {
        std::cout << "=== Gradient Check: " << name << " ===\n";

        for (const auto& pair : model.named_parameters()) {
            const auto& param_name = pair.key();
            const auto& param = pair.value();

            if (!param.grad().defined()) {
                std::cout << param_name << ": NO GRADIENT\n";
                continue;
            }

            auto grad = param.grad();
            float grad_norm = grad.norm().item<float>();
            float grad_mean = grad.mean().item<float>();
            float grad_std = grad.std().item<float>();

            std::cout << param_name
                      << " | norm: " << grad_norm
                      << " | mean: " << grad_mean
                      << " | std: " << grad_std;

            // Warn about potential issues
            if (grad_norm == 0) {
                std::cout << " [ZERO GRADIENT]";
            } else if (grad_norm > 100) {
                std::cout << " [EXPLODING]";
            } else if (std::isnan(grad_norm)) {
                std::cout << " [NaN]";
            }

            std::cout << "\n";
        }
    }

    static void numerical_gradient_check(
        torch::nn::Module& model,
        torch::Tensor input,
        torch::Tensor target,
        double epsilon = 1e-5
    ) {
        auto loss_fn = [&](torch::Tensor in) {
            return torch::mse_loss(model.forward(in), target);
        };

        auto analytical_grad = torch::autograd::grad(
            {loss_fn(input)}, {input})[0];

        // Numerical gradient
        auto numerical_grad = torch::zeros_like(input);
        auto flat_input = input.flatten();

        for (int i = 0; i < flat_input.numel(); ++i) {
            auto input_plus = input.clone();
            auto input_minus = input.clone();

            input_plus.flatten()[i] += epsilon;
            input_minus.flatten()[i] -= epsilon;

            float loss_plus = loss_fn(input_plus).item<float>();
            float loss_minus = loss_fn(input_minus).item<float>();

            numerical_grad.flatten()[i] = (loss_plus - loss_minus) / (2 * epsilon);
        }

        auto diff = (analytical_grad - numerical_grad).abs().max().item<float>();
        std::cout << "Max gradient difference: " << diff << "\n";

        if (diff > 1e-4) {
            std::cout << "WARNING: Gradients may be incorrect!\n";
        }
    }
};
```

### Value Debugging

```cpp
class ValueDebugger {
public:
    static void log_q_values(const DQNAgent& agent, torch::Tensor states) {
        torch::NoGradGuard no_grad;
        auto q_values = agent.get_q_values(states);

        std::cout << "=== Q-Value Statistics ===\n";
        std::cout << "Mean: " << q_values.mean().item<float>() << "\n";
        std::cout << "Std:  " << q_values.std().item<float>() << "\n";
        std::cout << "Min:  " << q_values.min().item<float>() << "\n";
        std::cout << "Max:  " << q_values.max().item<float>() << "\n";

        // Check for issues
        if (std::abs(q_values.mean().item<float>()) > 1000) {
            std::cout << "WARNING: Q-values may be exploding\n";
        }
    }

    static void log_action_distribution(
        const std::vector<int64_t>& actions,
        int num_actions
    ) {
        std::vector<int> counts(num_actions, 0);
        for (auto action : actions) {
            counts[action]++;
        }

        std::cout << "=== Action Distribution ===\n";
        for (int i = 0; i < num_actions; ++i) {
            float pct = 100.0f * counts[i] / actions.size();
            std::cout << "Action " << i << ": " << pct << "%\n";
        }
    }
};
```

### Memory Leak Detection

```cpp
#include <iostream>

class MemoryTracker {
public:
    static void start() {
        if (torch::cuda::is_available()) {
            initial_allocated_ = torch::cuda::memory_allocated();
            initial_reserved_ = torch::cuda::memory_reserved();
        }
    }

    static void check(const std::string& label) {
        if (torch::cuda::is_available()) {
            size_t allocated = torch::cuda::memory_allocated();
            size_t reserved = torch::cuda::memory_reserved();

            std::cout << "=== Memory: " << label << " ===\n";
            std::cout << "Allocated: " << (allocated - initial_allocated_) / 1e6
                      << " MB change\n";
            std::cout << "Reserved:  " << (reserved - initial_reserved_) / 1e6
                      << " MB change\n";
        }
    }

    static void assert_no_leak(const std::string& label, size_t tolerance_bytes = 1e6) {
        if (torch::cuda::is_available()) {
            torch::cuda::synchronize();

            size_t current = torch::cuda::memory_allocated();
            size_t diff = current > initial_allocated_ ?
                         current - initial_allocated_ : 0;

            if (diff > tolerance_bytes) {
                std::cerr << "MEMORY LEAK at " << label
                          << ": " << diff / 1e6 << " MB\n";
            }
        }
    }

private:
    static inline size_t initial_allocated_ = 0;
    static inline size_t initial_reserved_ = 0;
};

// Usage in tests
TEST(MemoryTest, NoLeakDuringTraining) {
    MemoryTracker::start();

    for (int episode = 0; episode < 100; ++episode) {
        train_one_episode();
    }

    MemoryTracker::assert_no_leak("100 episodes");
}
```

## Integration Testing

### End-to-End Training Test

```cpp
TEST(IntegrationTest, CartPoleLearning) {
    SeedManager::set_global_seed(42);

    // Simple environment mock
    auto env = std::make_unique<CartPoleEnv>();
    DQNAgent agent(4, 2);
    ReplayBuffer buffer(10000);

    std::vector<float> episode_rewards;

    for (int episode = 0; episode < 200; ++episode) {
        auto state = env->reset();
        float total_reward = 0;

        for (int step = 0; step < 500; ++step) {
            auto action = agent.select_action(state);
            auto [next_state, reward, done, info] = env->step(action);

            buffer.push({state, action, reward, next_state, done});
            total_reward += reward;

            if (buffer.can_sample(32)) {
                agent.train_step(buffer.sample(32));
            }

            if (done) break;
            state = next_state;
        }

        episode_rewards.push_back(total_reward);

        if (episode % 10 == 0) {
            agent.update_target_network();
        }
    }

    // Check learning progress
    float early_avg = std::accumulate(
        episode_rewards.begin(),
        episode_rewards.begin() + 20, 0.0f) / 20;
    float late_avg = std::accumulate(
        episode_rewards.end() - 20,
        episode_rewards.end(), 0.0f) / 20;

    EXPECT_GT(late_avg, early_avg * 1.5);  // Should improve significantly
    EXPECT_GT(late_avg, 100);  // Should achieve reasonable performance
}
```

### Model Save/Load Test

```cpp
TEST(SerializationTest, SaveAndLoadModel) {
    SeedManager::set_global_seed(42);

    auto original = std::make_shared<DQNNet>(4, 2);
    auto input = torch::randn({10, 4});
    auto original_output = original->forward(input);

    // Save
    torch::save(original, "test_model.pt");

    // Load into new model
    auto loaded = std::make_shared<DQNNet>(4, 2);
    torch::load(loaded, "test_model.pt");

    auto loaded_output = loaded->forward(input);

    EXPECT_TRUE(torch::allclose(original_output, loaded_output));

    // Cleanup
    std::remove("test_model.pt");
}
```

## Logging Best Practices

### Structured Training Logger

```cpp
#include <fstream>
#include <nlohmann/json.hpp>

class TrainingLogger {
public:
    explicit TrainingLogger(const std::string& log_path)
        : log_file_(log_path) {}

    void log_step(int step, float loss, float q_mean, float epsilon) {
        nlohmann::json entry;
        entry["step"] = step;
        entry["loss"] = loss;
        entry["q_mean"] = q_mean;
        entry["epsilon"] = epsilon;
        entry["timestamp"] = std::time(nullptr);

        log_file_ << entry.dump() << "\n";
        log_file_.flush();
    }

    void log_episode(int episode, float reward, int steps) {
        nlohmann::json entry;
        entry["episode"] = episode;
        entry["reward"] = reward;
        entry["steps"] = steps;
        entry["timestamp"] = std::time(nullptr);

        log_file_ << entry.dump() << "\n";
        log_file_.flush();
    }

    void log_checkpoint(int step, const std::string& path) {
        nlohmann::json entry;
        entry["checkpoint"] = true;
        entry["step"] = step;
        entry["path"] = path;

        log_file_ << entry.dump() << "\n";
        log_file_.flush();
    }

private:
    std::ofstream log_file_;
};
```
