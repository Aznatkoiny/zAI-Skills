---
name: reinforcement-learning
description: |
  Reinforcement Learning best practices for Python using modern libraries (Stable-Baselines3, RLlib, Gymnasium).
  Use when:
  - Implementing RL algorithms (PPO, SAC, DQN, TD3, A2C)
  - Creating custom Gymnasium environments
  - Training, debugging, or evaluating RL agents
  - Setting up hyperparameter tuning for RL
  - Deploying RL models to production
---

# Reinforcement Learning Best Practices

## Overview

This skill provides comprehensive guidance for implementing reinforcement learning in Python using the modern ecosystem (2024-2025). Gymnasium has replaced OpenAI Gym as the standard environment interface. Stable-Baselines3 (SB3) is recommended for prototyping, RLlib for production/distributed training, and CleanRL for research.

## When to Use

- Building RL agents for discrete or continuous control tasks
- Creating custom simulation environments
- Tuning hyperparameters for RL algorithms
- Debugging training issues (reward curves, policy collapse, numerical instability)
- Deploying trained policies to production

## Library Selection

| Library | Best For | Ease | Flexibility | Production |
|---------|----------|------|-------------|------------|
| Stable-Baselines3 | Prototyping, learning | High | Medium | Good |
| RLlib | Production, distributed | Medium | High | Excellent |
| CleanRL | Research, understanding | High | Low | Poor |
| TorchRL | Custom implementations | Low | Highest | Good |

## Algorithm Decision Tree

```
Start
  |
  v
Action space type?
  |
  +-- Discrete --> Sample efficiency critical?
  |                  |
  |                  +-- Yes --> DQN (or Double/Dueling DQN)
  |                  +-- No  --> Stability critical?
  |                               |
  |                               +-- Yes --> PPO
  |                               +-- No  --> A2C (faster iterations)
  |
  +-- Continuous --> Sample efficiency critical?
                       |
                       +-- Yes --> SAC (auto entropy) or TD3
                       +-- No  --> PPO (more stable, less efficient)
```

**Quick Selection Table:**

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Discrete actions, getting started | PPO | Stable, good defaults |
| Continuous control | SAC or TD3 | Sample efficient, handles continuous well |
| Sample efficiency critical | SAC, DQN | Off-policy, reuses experience |
| Stability critical | PPO | Trust region, consistent |
| High-dimensional obs (images) | PPO + CNN | Handles visual input well |
| Fast iteration needed | A2C | Simpler, faster per update |

## Quick Start with Stable-Baselines3

### Basic Training

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# Create vectorized environment (4 parallel envs)
env = make_vec_env("CartPole-v1", n_envs=4)

# Initialize and train
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100_000)

# Save and load
model.save("ppo_cartpole")
loaded_model = PPO.load("ppo_cartpole")

# Evaluate
obs = env.reset()
for _ in range(1000):
    action, _ = loaded_model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
```

### Custom Environment Template

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self, render_mode=None):
        super().__init__()
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(2)
        self.render_mode = render_mode

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        return self.state.astype(np.float32), {}

    def step(self, action):
        # Implement environment dynamics here
        observation = self.state.astype(np.float32)
        reward = 1.0
        terminated = False  # Episode ended due to task completion/failure
        truncated = False   # Episode ended due to time limit
        info = {}
        return observation, reward, terminated, truncated, info

    def render(self):
        pass
```

### Hyperparameter Tuning with Optuna

```python
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

def objective(trial):
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
    n_steps = trial.suggest_categorical("n_steps", [256, 512, 1024, 2048])
    gamma = trial.suggest_float("gamma", 0.9, 0.9999)

    model = PPO(
        "MlpPolicy", "CartPole-v1",
        learning_rate=learning_rate,
        n_steps=n_steps,
        gamma=gamma,
        verbose=0
    )
    model.learn(total_timesteps=50_000)

    mean_reward, _ = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
    return mean_reward

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)
print(f"Best params: {study.best_params}")
```

## Core Workflow

1. **Define the environment** - Use Gymnasium API, validate spaces
2. **Select algorithm** - Based on action space and requirements
3. **Start simple** - Default hyperparameters, short training
4. **Monitor training** - TensorBoard, check reward curves
5. **Debug issues** - Use the debugging playbook
6. **Tune hyperparameters** - Optuna for systematic search
7. **Evaluate properly** - Separate eval env, multiple seeds
8. **Deploy** - Export to ONNX/TorchScript

## Reference Files

- [algorithms.md](references/algorithms.md) - Deep dive on DQN, PPO, SAC, A2C, TD3
- [environments.md](references/environments.md) - Gymnasium setup, custom envs, wrappers
- [training.md](references/training.md) - Hyperparameters, reward engineering, normalization
- [debugging.md](references/debugging.md) - Failure modes, diagnostics, sanity checks
- [evaluation.md](references/evaluation.md) - Metrics, logging, reproducibility
- [deployment.md](references/deployment.md) - ONNX export, inference optimization, safety

## Essential Dependencies

```bash
pip install gymnasium stable-baselines3 tensorboard optuna
# For Atari environments
pip install gymnasium[atari] gymnasium[accept-rom-license]
# For MuJoCo
pip install gymnasium[mujoco]
```

## Common Pitfalls to Avoid

1. **Not normalizing observations** - Use `VecNormalize` wrapper
2. **Wrong action space handling** - Check discrete vs continuous
3. **Ignoring seed management** - Set seeds for reproducibility
4. **Training and eval on same env** - Use separate eval environment
5. **Not monitoring entropy** - Low entropy = policy collapse
6. **Sparse rewards without shaping** - Add intermediate rewards
7. **Too large/small learning rate** - Start with 3e-4 for most algorithms
