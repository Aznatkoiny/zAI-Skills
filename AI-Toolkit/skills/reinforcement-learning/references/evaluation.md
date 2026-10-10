# RL Evaluation and Reproducibility

## Overview

Proper evaluation is critical in RL due to high variance. This guide covers metrics, evaluation procedures, logging, reproducibility, and statistical comparisons.

## Essential Metrics to Track

### During Training

| Metric | Purpose | Where to Find |
|--------|---------|---------------|
| Episode Return | Primary performance | `rollout/ep_rew_mean` |
| Episode Length | Task efficiency | `rollout/ep_len_mean` |
| Policy Loss | Learning progress | `train/policy_gradient_loss` |
| Value Loss | Value function quality | `train/value_loss` |
| Entropy | Exploration level (`entropy_loss` is *negative* entropy; rising toward 0 = collapse) | `train/entropy_loss` |
| Explained Variance | Value accuracy | `train/explained_variance` |
| Learning Rate | Schedule progress | `train/learning_rate` |
| Clip Fraction (PPO) | Update magnitude | `train/clip_fraction` |
| FPS | Training speed | `time/fps` |

### During Evaluation

> **Canonical runnable version: [`scripts/eval_report.py`](../scripts/eval_report.py).**
> It implements this exact evaluation loop (per-episode success read from the
> TERMINAL step's `info` dict, mean/std/95% CI, episode lengths) as a CLI and
> writes a Markdown report. Run it instead of re-deriving the loop:
>
> ```bash
> # Trained SB3 model
> python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/eval_report.py CartPole-v1 --model ppo_cartpole.zip --algo ppo \
>     --episodes 100 --output eval_report.md
>
> # Random-policy baseline (no model)
> python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/eval_report.py CartPole-v1 --episodes 50 --output baseline.md
> ```
>
> If the model was trained with VecNormalize, add `--vecnormalize models/vecnormalize.pkl`;
> without it the agent sees unnormalized observations and scores like a random policy.
>
> The pattern it implements, in short: read `is_success` from the **terminal** step's
> `info` (once per episode, never per step), always cap episode length, and report a
> confidence interval (`1.96 * std / sqrt(n)`) rather than a bare mean.

---

## Separate Evaluation from Training

### Why Separate?

1. **Training uses exploration** - Stochastic policy
2. **Evaluation should be deterministic** - Test true performance
3. **Training env may have wrappers** - Normalization stats differ
4. **Prevents data leakage** - Don't tune on test performance

### Implementation

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize
from stable_baselines3.common.callbacks import EvalCallback

# Training environment (with normalization)
train_env = make_vec_env("Pendulum-v1", n_envs=4)
train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True)

# Evaluation environment (separate, no reward normalization)
eval_env = make_vec_env("Pendulum-v1", n_envs=1)
eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

# Sync normalization stats (important!)
eval_env.obs_rms = train_env.obs_rms

# Evaluation callback
eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="./logs/best_model",
    log_path="./logs/eval",
    eval_freq=10000,
    n_eval_episodes=20,
    deterministic=True,
    render=False
)

# Train
model = PPO("MlpPolicy", train_env, verbose=1)
model.learn(total_timesteps=100_000, callback=eval_callback)
```

### Evaluation with Normalized Observations

```python
# After training, load model and normalization stats
model = PPO.load("best_model")
eval_env = make_vec_env("Pendulum-v1", n_envs=1)

# Load normalization stats
eval_env = VecNormalize.load("vec_normalize.pkl", eval_env)
eval_env.training = False  # Don't update running stats
eval_env.norm_reward = False  # Don't normalize rewards

# Evaluate
mean_reward, std_reward = evaluate_policy(
    model, eval_env, n_eval_episodes=50, deterministic=True
)
```

---

## Logging Frameworks

### TensorBoard

```python
from stable_baselines3 import PPO

# Enable TensorBoard logging
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    tensorboard_log="./tb_logs/"
)

model.learn(total_timesteps=100_000)

# View logs
# tensorboard --logdir ./tb_logs/
```

### Weights & Biases

```python
import wandb
from wandb.integration.sb3 import WandbCallback

# Initialize W&B
wandb.init(
    project="rl-experiments",
    config={
        "algorithm": "PPO",
        "env": "CartPole-v1",
        "learning_rate": 3e-4,
    },
    sync_tensorboard=True
)

model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=f"runs/{wandb.run.id}")

model.learn(
    total_timesteps=100_000,
    callback=WandbCallback(
        gradient_save_freq=1000,
        model_save_path=f"models/{wandb.run.id}",
        verbose=2
    )
)

wandb.finish()
```

### Custom Logging Callback

```python
from stable_baselines3.common.callbacks import BaseCallback
import json
from datetime import datetime

class DetailedLoggingCallback(BaseCallback):
    """Log detailed metrics to JSON file."""

    def __init__(self, log_path, verbose=0):
        super().__init__(verbose)
        self.log_path = log_path
        self.logs = []

    def _on_step(self):
        # Log every 1000 steps
        if self.n_calls % 1000 == 0:
            log_entry = {
                "timestep": self.num_timesteps,
                "time": datetime.now().isoformat(),
            }

            # Episode info
            if len(self.model.ep_info_buffer) > 0:
                ep_rewards = [ep['r'] for ep in self.model.ep_info_buffer]
                ep_lengths = [ep['l'] for ep in self.model.ep_info_buffer]
                log_entry["mean_reward"] = np.mean(ep_rewards)
                log_entry["std_reward"] = np.std(ep_rewards)
                log_entry["mean_length"] = np.mean(ep_lengths)

            self.logs.append(log_entry)

        return True

    def _on_training_end(self):
        # Save all logs
        with open(self.log_path, 'w') as f:
            json.dump(self.logs, f, indent=2)
        print(f"Logs saved to {self.log_path}")
```

### MLflow

```python
import mlflow
from stable_baselines3 import PPO

# Start MLflow run
mlflow.set_experiment("rl-experiments")

with mlflow.start_run():
    # Log parameters
    mlflow.log_params({
        "algorithm": "PPO",
        "learning_rate": 3e-4,
        "n_steps": 2048,
        "env": "CartPole-v1"
    })

    # Train
    model = PPO("MlpPolicy", env, learning_rate=3e-4, n_steps=2048)
    model.learn(total_timesteps=100_000)

    # Evaluate and log metrics
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=100)
    mlflow.log_metrics({
        "mean_reward": mean_reward,
        "std_reward": std_reward
    })

    # Save model as artifact
    model.save("ppo_model")
    mlflow.log_artifact("ppo_model.zip")
```

---

## Seed Management and Determinism

### Setting Seeds Properly

```python
import random
import numpy as np
import torch
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.utils import set_random_seed

def make_deterministic(seed):
    """Set all seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # PyTorch deterministic operations
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def train_with_seed(env_id, seed, total_timesteps):
    """Train model with specific seed."""
    make_deterministic(seed)

    # Create environment with seed
    env = gym.make(env_id)
    env.reset(seed=seed)

    # For vectorized envs
    # env = make_vec_env(env_id, n_envs=4, seed=seed)

    # Create model with seed
    model = PPO("MlpPolicy", env, seed=seed, verbose=0)

    # Train
    model.learn(total_timesteps=total_timesteps)

    return model

# Run multiple seeds
results = {}
for seed in [0, 42, 123, 456, 789]:
    model = train_with_seed("CartPole-v1", seed, 50_000)
    mean_reward, _ = evaluate_policy(model, model.get_env(), n_eval_episodes=50)
    results[seed] = mean_reward
    print(f"Seed {seed}: {mean_reward:.2f}")

print(f"\nMean across seeds: {np.mean(list(results.values())):.2f}")
print(f"Std across seeds: {np.std(list(results.values())):.2f}")
```

### Reproducibility Checklist

- [ ] Set random seed for Python's `random`
- [ ] Set numpy seed
- [ ] Set PyTorch seed (CPU and CUDA)
- [ ] Set environment seed in `reset()`
- [ ] Pass seed to model constructor
- [ ] Use deterministic PyTorch operations
- [ ] Document all library versions
- [ ] Log hardware information

### Saving Experiment Configuration

```python
import json
import sys

import gymnasium as gym
import numpy as np
import stable_baselines3
import torch

def save_experiment_config(filepath, model, env, seed, hyperparams):
    """Save complete experiment configuration."""
    config = {
        "seed": seed,
        "environment": {
            "id": env.spec.id if hasattr(env, 'spec') else str(type(env)),
            "observation_space": str(env.observation_space),
            "action_space": str(env.action_space),
        },
        "hyperparameters": hyperparams,
        "versions": {
            "python": sys.version,
            "torch": torch.__version__,
            "stable_baselines3": stable_baselines3.__version__,
            "numpy": np.__version__,
            "gymnasium": gym.__version__,
        },
        "hardware": {
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    }

    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)

    return config
```

---

## Statistical Comparison Methods

### Comparing Two Algorithms

```python
from scipy import stats
import numpy as np

def compare_algorithms(rewards_a, rewards_b, alpha=0.05):
    """
    Statistical comparison of two algorithms.

    Args:
        rewards_a: List of episode rewards for algorithm A
        rewards_b: List of episode rewards for algorithm B
        alpha: Significance level

    Returns:
        Dictionary with comparison results
    """
    rewards_a = np.array(rewards_a)
    rewards_b = np.array(rewards_b)

    # Basic statistics
    results = {
        "algo_a": {
            "mean": np.mean(rewards_a),
            "std": np.std(rewards_a),
            "median": np.median(rewards_a),
            "n": len(rewards_a)
        },
        "algo_b": {
            "mean": np.mean(rewards_b),
            "std": np.std(rewards_b),
            "median": np.median(rewards_b),
            "n": len(rewards_b)
        }
    }

    # Welch's t-test (doesn't assume equal variance)
    t_stat, p_value = stats.ttest_ind(rewards_a, rewards_b, equal_var=False)
    results["welch_ttest"] = {
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": p_value < alpha
    }

    # Mann-Whitney U test (non-parametric)
    u_stat, p_value_mw = stats.mannwhitneyu(rewards_a, rewards_b, alternative='two-sided')
    results["mann_whitney"] = {
        "u_statistic": u_stat,
        "p_value": p_value_mw,
        "significant": p_value_mw < alpha
    }

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((rewards_a.std()**2 + rewards_b.std()**2) / 2)
    cohens_d = (rewards_a.mean() - rewards_b.mean()) / pooled_std
    results["effect_size"] = {
        "cohens_d": cohens_d,
        "interpretation": interpret_cohens_d(cohens_d)
    }

    # 95% confidence interval for difference
    diff_mean = rewards_a.mean() - rewards_b.mean()
    diff_se = np.sqrt(rewards_a.var()/len(rewards_a) + rewards_b.var()/len(rewards_b))
    results["difference"] = {
        "mean": diff_mean,
        "ci_lower": diff_mean - 1.96 * diff_se,
        "ci_upper": diff_mean + 1.96 * diff_se
    }

    return results

def interpret_cohens_d(d):
    """Interpret Cohen's d effect size."""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"

# Example usage
ppo_rewards = [195, 200, 198, 188, 200, 195, 192, 200, 197, 199]  # 10 eval episodes
dqn_rewards = [180, 175, 190, 185, 178, 182, 188, 179, 183, 186]

comparison = compare_algorithms(ppo_rewards, dqn_rewards)
print(f"PPO mean: {comparison['algo_a']['mean']:.2f} +/- {comparison['algo_a']['std']:.2f}")
print(f"DQN mean: {comparison['algo_b']['mean']:.2f} +/- {comparison['algo_b']['std']:.2f}")
print(f"Significant difference: {comparison['welch_ttest']['significant']}")
print(f"Effect size: {comparison['effect_size']['interpretation']}")
```

### Multiple Seeds Comparison

```python
def multi_seed_comparison(algo_results):
    """
    Compare algorithms across multiple seeds.

    Args:
        algo_results: Dict mapping algorithm name to list of (seed, reward) tuples

    Returns:
        Comparison results
    """
    # Aggregate by algorithm
    algo_rewards = {}
    for algo, results in algo_results.items():
        algo_rewards[algo] = [r for _, r in results]

    # Kruskal-Wallis test (non-parametric ANOVA)
    groups = list(algo_rewards.values())
    h_stat, p_value = stats.kruskal(*groups)

    print("=" * 50)
    print("Multi-Seed Algorithm Comparison")
    print("=" * 50)

    for algo, rewards in algo_rewards.items():
        print(f"\n{algo}:")
        print(f"  Seeds: {len(rewards)}")
        print(f"  Mean: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
        print(f"  Min/Max: {np.min(rewards):.2f} / {np.max(rewards):.2f}")

    print(f"\nKruskal-Wallis test:")
    print(f"  H-statistic: {h_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Significant (p<0.05): {p_value < 0.05}")

    return algo_rewards, (h_stat, p_value)

# Example
results = {
    "PPO": [(0, 195), (1, 198), (2, 192), (3, 200), (4, 197)],
    "DQN": [(0, 180), (1, 175), (2, 185), (3, 178), (4, 182)],
    "A2C": [(0, 188), (1, 190), (2, 185), (3, 192), (4, 187)]
}

multi_seed_comparison(results)
```

---

## Checkpointing Strategies

### Basic Checkpointing

```python
from stable_baselines3.common.callbacks import CheckpointCallback

checkpoint_callback = CheckpointCallback(
    save_freq=10000,  # Save every 10k steps
    save_path="./checkpoints/",
    name_prefix="rl_model",
    save_replay_buffer=True,  # For off-policy
    save_vecnormalize=True    # Save normalization stats
)

model.learn(total_timesteps=100_000, callback=checkpoint_callback)
```

### Best Model Saving

```python
from stable_baselines3.common.callbacks import EvalCallback

eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="./best_model/",
    log_path="./logs/",
    eval_freq=5000,
    n_eval_episodes=10,
    deterministic=True
)

model.learn(total_timesteps=100_000, callback=eval_callback)

# Load best model
best_model = PPO.load("./best_model/best_model")
```

### Complete Checkpoint with Normalization

```python
def save_complete_checkpoint(model, env, path):
    """Save model, normalization stats, and config."""
    import os
    os.makedirs(path, exist_ok=True)

    # Save model
    model.save(os.path.join(path, "model"))

    # Save normalization stats if using VecNormalize
    if isinstance(env, VecNormalize):
        env.save(os.path.join(path, "vec_normalize.pkl"))

    # Save config
    config = {
        "algorithm": type(model).__name__,
        "policy": model.policy_class.__name__,
        "n_envs": model.n_envs,
        "gamma": model.gamma,
    }
    with open(os.path.join(path, "config.json"), 'w') as f:
        json.dump(config, f)

def load_complete_checkpoint(path, env_fn):
    """Load model with normalization stats."""
    import os

    # Load config
    with open(os.path.join(path, "config.json"), 'r') as f:
        config = json.load(f)

    # Create environment
    env = env_fn()

    # Load normalization stats if they exist
    norm_path = os.path.join(path, "vec_normalize.pkl")
    if os.path.exists(norm_path):
        env = VecNormalize.load(norm_path, env)
        env.training = False      # freeze the running statistics
        env.norm_reward = False   # report raw rewards

    # Load model
    model_path = os.path.join(path, "model")
    model = PPO.load(model_path, env=env)

    return model, env
```

---

## Evaluation Report Template

> **Runnable version: [`scripts/eval_report.py`](../scripts/eval_report.py)** —
> generates this report (plus success rate and episode-length rows) from the
> command line for any registered env or `module:EnvClass` spec.
