# RL Training Best Practices

## Overview

Training RL agents effectively requires careful attention to hyperparameters, reward engineering, exploration, and normalization. This guide covers practical techniques for successful training.

## Hyperparameter Tuning

### Starting Point Strategy

1. **Start with defaults** - SB3 defaults are well-tuned for common cases
2. **Scale learning rate** - Adjust based on environment complexity
3. **Adjust rollout length** - Match to environment horizon
4. **Tune exploration** - Critical for hard exploration problems

### Optuna Integration

```python
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_util import make_vec_env

def objective(trial):
    """Optuna objective for PPO hyperparameter tuning."""

    # Suggest hyperparameters
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
    n_steps = trial.suggest_categorical("n_steps", [256, 512, 1024, 2048])
    batch_size = trial.suggest_categorical("batch_size", [32, 64, 128, 256])
    n_epochs = trial.suggest_int("n_epochs", 3, 30)
    gamma = trial.suggest_float("gamma", 0.9, 0.9999)
    gae_lambda = trial.suggest_float("gae_lambda", 0.8, 1.0)
    clip_range = trial.suggest_float("clip_range", 0.1, 0.4)
    ent_coef = trial.suggest_float("ent_coef", 1e-8, 0.1, log=True)

    # Ensure batch_size <= n_steps
    batch_size = min(batch_size, n_steps)

    # Create environment
    env = make_vec_env("CartPole-v1", n_envs=4)

    # Create model
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        verbose=0
    )

    # Train
    model.learn(total_timesteps=50_000)

    # Evaluate
    mean_reward, std_reward = evaluate_policy(
        model, model.get_env(), n_eval_episodes=10, deterministic=True
    )

    # Report intermediate value (for pruning)
    trial.report(mean_reward, step=50_000)

    return mean_reward

# Create study with pruning
study = optuna.create_study(
    direction="maximize",
    pruner=optuna.pruners.MedianPruner(n_warmup_steps=5)
)

# Optimize
study.optimize(objective, n_trials=100, timeout=3600)

# Results
print(f"Best trial: {study.best_trial.value}")
print(f"Best params: {study.best_params}")
```

### SAC Hyperparameter Tuning

```python
def sac_objective(trial):
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
    buffer_size = trial.suggest_categorical("buffer_size", [10000, 50000, 100000, 500000])
    batch_size = trial.suggest_categorical("batch_size", [64, 128, 256, 512])
    gamma = trial.suggest_float("gamma", 0.9, 0.9999)
    tau = trial.suggest_float("tau", 0.001, 0.05)

    model = SAC(
        "MlpPolicy", "Pendulum-v1",
        learning_rate=learning_rate,
        buffer_size=buffer_size,
        batch_size=batch_size,
        gamma=gamma,
        tau=tau,
        verbose=0
    )
    model.learn(total_timesteps=20_000)

    mean_reward, _ = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
    return mean_reward
```

### Key Hyperparameters by Algorithm

#### PPO
| Parameter | Start | Tune Range | Impact |
|-----------|-------|------------|--------|
| learning_rate | 3e-4 | 1e-5 to 1e-3 | High |
| n_steps | 2048 | 128-4096 | Medium |
| batch_size | 64 | 32-512 | Medium |
| n_epochs | 10 | 3-30 | Medium |
| clip_range | 0.2 | 0.1-0.4 | Medium |
| ent_coef | 0.0 | 0-0.1 | High for exploration |

#### SAC
| Parameter | Start | Tune Range | Impact |
|-----------|-------|------------|--------|
| learning_rate | 3e-4 | 1e-5 to 1e-3 | High |
| buffer_size | 1M | 10K-10M | Medium |
| batch_size | 256 | 64-512 | Low |
| tau | 0.005 | 0.001-0.05 | Medium |
| ent_coef | auto | auto or tune | High |

---

## Reward Engineering

### Principles

1. **Dense > Sparse** - More frequent feedback accelerates learning
2. **Shaped rewards** - Guide agent toward goal without changing optimal policy
3. **Potential-based shaping** - Guarantees policy invariance
4. **Normalize rewards** - Keep rewards in reasonable range

### Sparse Rewards Problem

```python
# Bad: Sparse reward (agent may never see positive reward)
def sparse_reward(achieved_goal, desired_goal):
    return 1.0 if np.allclose(achieved_goal, desired_goal) else 0.0

# Better: Distance-based shaping
def shaped_reward(achieved_goal, desired_goal, prev_distance=None):
    current_distance = np.linalg.norm(achieved_goal - desired_goal)

    # Terminal reward
    if current_distance < 0.1:
        return 10.0

    # Shaping reward (progress toward goal)
    if prev_distance is not None:
        progress = prev_distance - current_distance
        return progress  # Positive if getting closer

    return -0.1  # Small negative to encourage speed
```

### Potential-Based Shaping

```python
def potential(state):
    """Potential function based on distance to goal."""
    goal = np.array([0, 0])
    return -np.linalg.norm(state - goal)

def shaped_reward(state, next_state, base_reward, gamma=0.99):
    """Add potential-based shaping that preserves optimal policy."""
    shaping = gamma * potential(next_state) - potential(state)
    return base_reward + shaping
```

### Reward Normalization

```python
from stable_baselines3.common.vec_env import VecNormalize

# Automatic reward normalization
env = make_vec_env("Pendulum-v1", n_envs=4)
env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_reward=10.0)

# Manual running average
class RewardNormalizer:
    def __init__(self, gamma=0.99):
        self.return_rms = RunningMeanStd()
        self.returns = 0
        self.gamma = gamma

    def normalize(self, reward, done):
        self.returns = self.returns * self.gamma + reward
        self.return_rms.update(np.array([self.returns]))
        normalized = reward / (np.sqrt(self.return_rms.var) + 1e-8)
        if done:
            self.returns = 0
        return normalized
```

### Common Reward Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Reward too sparse | Agent never learns | Add shaping rewards |
| Reward too complex | Agent exploits loopholes | Simplify, test extensively |
| Wrong scale | Gradient issues | Normalize to [-10, 10] |
| Rewarding wrong thing | Agent learns wrong behavior | Carefully define success |

---

## Exploration Strategies

### Entropy Bonus

Encourages policy to maintain exploration by penalizing deterministic policies.

```python
# PPO with entropy bonus
model = PPO(
    "MlpPolicy", "CartPole-v1",
    ent_coef=0.01,  # Entropy coefficient
    verbose=1
)

# Monitor entropy during training (via TensorBoard)
# Look for "train/entropy_loss" - should not drop to 0
```

### Epsilon-Greedy (DQN)

```python
# DQN exploration schedule
model = DQN(
    "MlpPolicy", "CartPole-v1",
    exploration_fraction=0.2,      # Fraction of training for decay
    exploration_initial_eps=1.0,   # Start with full random
    exploration_final_eps=0.05,    # End with 5% random
    verbose=1
)
```

### Action Noise (Continuous)

```python
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
import numpy as np

n_actions = env.action_space.shape[-1]

# Gaussian noise
action_noise = NormalActionNoise(
    mean=np.zeros(n_actions),
    sigma=0.1 * np.ones(n_actions)
)

# Ornstein-Uhlenbeck noise (temporally correlated)
action_noise = OrnsteinUhlenbeckActionNoise(
    mean=np.zeros(n_actions),
    sigma=0.1 * np.ones(n_actions),
    theta=0.15,  # Rate of mean reversion
    dt=1e-2
)

model = TD3("MlpPolicy", env, action_noise=action_noise)
```

### Curiosity-Driven Exploration

For environments with very sparse rewards:

```python
# Using stable-baselines3-contrib
from sb3_contrib import RecurrentPPO

# Or implement intrinsic motivation
class ICMReward:
    """Intrinsic Curiosity Module reward."""

    def __init__(self, feature_dim=64, lr=1e-3):
        self.forward_model = ...  # Predicts next state encoding
        self.inverse_model = ...  # Predicts action from states

    def compute_intrinsic_reward(self, obs, action, next_obs):
        # Reward based on prediction error
        predicted_next = self.forward_model(obs, action)
        actual_next = self.encode(next_obs)
        intrinsic_reward = torch.mean((predicted_next - actual_next) ** 2)
        return intrinsic_reward.item()
```

---

## Normalization Techniques

### Observation Normalization

```python
from stable_baselines3.common.vec_env import VecNormalize

env = make_vec_env("Pendulum-v1", n_envs=4)

# Normalize observations with running statistics
env = VecNormalize(
    env,
    norm_obs=True,
    norm_reward=False,
    clip_obs=10.0,       # Clip normalized obs to [-10, 10]
    gamma=0.99
)

# Train
model = PPO("MlpPolicy", env)
model.learn(total_timesteps=100_000)

# Important: Save normalization stats with model
env.save("vec_normalize.pkl")
model.save("ppo_model")

# Load for evaluation
eval_env = make_vec_env("Pendulum-v1", n_envs=1)
eval_env = VecNormalize.load("vec_normalize.pkl", eval_env)
eval_env.training = False  # Don't update stats during eval
eval_env.norm_reward = False  # Don't normalize rewards during eval
```

### Advantage Normalization

PPO and A2C automatically normalize advantages:

```python
# In PPO, advantages are normalized by default
# (advantage - mean) / (std + eps)

# This happens inside the algorithm, but you can control via:
model = PPO(
    "MlpPolicy", env,
    normalize_advantage=True  # Default
)
```

### Manual Normalization

```python
class RunningMeanStd:
    """Running mean and standard deviation."""

    def __init__(self, epsilon=1e-4, shape=()):
        self.mean = np.zeros(shape, dtype=np.float64)
        self.var = np.ones(shape, dtype=np.float64)
        self.count = epsilon

    def update(self, batch):
        batch_mean = np.mean(batch, axis=0)
        batch_var = np.var(batch, axis=0)
        batch_count = batch.shape[0]
        self._update_from_moments(batch_mean, batch_var, batch_count)

    def _update_from_moments(self, batch_mean, batch_var, batch_count):
        delta = batch_mean - self.mean
        tot_count = self.count + batch_count

        new_mean = self.mean + delta * batch_count / tot_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + np.square(delta) * self.count * batch_count / tot_count
        new_var = m2 / tot_count

        self.mean = new_mean
        self.var = new_var
        self.count = tot_count

    def normalize(self, x):
        return (x - self.mean) / (np.sqrt(self.var) + 1e-8)
```

---

## Learning Rate Schedules

### Linear Decay

```python
from stable_baselines3.common.callbacks import BaseCallback

def linear_schedule(initial_value):
    """Linear learning rate schedule."""
    def func(progress_remaining):
        return progress_remaining * initial_value
    return func

model = PPO(
    "MlpPolicy", "CartPole-v1",
    learning_rate=linear_schedule(3e-4),  # Will decay from 3e-4 to 0
    verbose=1
)
```

### Custom Schedules

```python
def exponential_schedule(initial_value, decay_rate=0.99):
    """Exponential decay."""
    def func(progress_remaining):
        return initial_value * (decay_rate ** (1 - progress_remaining))
    return func

def warmup_schedule(initial_value, warmup_fraction=0.1):
    """Linear warmup then constant."""
    def func(progress_remaining):
        # progress_remaining goes from 1 to 0
        progress = 1 - progress_remaining
        if progress < warmup_fraction:
            return initial_value * (progress / warmup_fraction)
        return initial_value
    return func

def cosine_schedule(initial_value, min_value=1e-6):
    """Cosine annealing."""
    def func(progress_remaining):
        return min_value + 0.5 * (initial_value - min_value) * (1 + np.cos(np.pi * (1 - progress_remaining)))
    return func
```

---

## Batch Size and Buffer Guidelines

### On-Policy (PPO, A2C)

| Environment Type | n_steps | batch_size | n_envs |
|------------------|---------|------------|--------|
| Simple (CartPole) | 2048 | 64 | 4-8 |
| Medium (LunarLander) | 2048 | 128 | 8-16 |
| Complex (MuJoCo) | 2048 | 256 | 16-32 |
| Visual (Atari) | 128 | 256 | 8-16 |

**Total timesteps per update** = n_steps * n_envs

### Off-Policy (DQN, SAC, TD3)

| Environment Type | buffer_size | batch_size | learning_starts |
|------------------|-------------|------------|-----------------|
| Simple | 100,000 | 64 | 1,000 |
| Medium | 500,000 | 128 | 10,000 |
| Complex | 1,000,000 | 256 | 25,000 |

**Guidelines:**
- Buffer should hold at least 10x the episode length
- Larger buffers improve stability but use more memory
- `learning_starts` should allow for some exploration first

---

## Training Loop Best Practices

```python
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env

# Separate training and evaluation environments
train_env = make_vec_env("CartPole-v1", n_envs=4)
eval_env = make_vec_env("CartPole-v1", n_envs=1)

# Callbacks
eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="./logs/best_model",
    log_path="./logs/eval",
    eval_freq=10000,
    n_eval_episodes=10,
    deterministic=True
)

checkpoint_callback = CheckpointCallback(
    save_freq=50000,
    save_path="./logs/checkpoints",
    name_prefix="ppo_model"
)

# Create model
model = PPO(
    "MlpPolicy",
    train_env,
    verbose=1,
    tensorboard_log="./logs/tensorboard"
)

# Train with callbacks
model.learn(
    total_timesteps=500_000,
    callback=[eval_callback, checkpoint_callback],
    progress_bar=True
)

# Final save
model.save("final_model")
```
