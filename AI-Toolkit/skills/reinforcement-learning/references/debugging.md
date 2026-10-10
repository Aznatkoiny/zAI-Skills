# RL Debugging Playbook

## Overview

Debugging RL is notoriously difficult due to high variance, delayed feedback, and complex interactions between components. This guide provides systematic approaches to diagnosing and fixing common issues.

## Pre-Training Sanity Checks

### Before Training

Run the bundled scripts rather than an inline checklist; they cover the same ground and are tested:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/validate_env.py src.env:MyEnv     # API, spaces, NaNs, determinism
python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/pretrain_check.py src.env:MyEnv   # random baseline, scales, sparse rewards
```

Run them from the project directory so `src.env:MyEnv` imports. Then confirm the model runs a forward pass on one observation (`model.predict(obs)`) before launching a long job.

---

## Common Failure Modes

### 1. Reward Not Improving

**Symptoms:**
- Flat reward curve
- No learning progress after many timesteps

**Diagnostics:**
```python
# Check if policy is updating
# In TensorBoard, look for:
# - policy_gradient_loss changing
# - value_loss changing
# - learning_rate (if scheduled)
```

**Causes and Solutions:**

| Cause | Diagnostic | Solution |
|-------|------------|----------|
| Learning rate too low | Losses barely change | Increase LR by 10x |
| Learning rate too high | Losses spike/NaN | Decrease LR by 10x |
| Not enough exploration | Policy entropy near 0 | Increase ent_coef |
| Sparse rewards | Few nonzero rewards | Add reward shaping |
| Bug in environment | Random agent gets 0 | Check env implementation |
| Wrong observation | Obs doesn't contain needed info | Add relevant features |

### 2. Reward Improves Then Collapses

**Symptoms:**
- Initial improvement
- Sudden drop in performance
- Never recovers

**Diagnostics:**
```python
# Monitor these in TensorBoard:
# - entropy: dropping to near 0 = policy collapse
# - value_loss: spiking = value function issues
# - clip_fraction (PPO): high = updates too aggressive
```

**Causes and Solutions:**

| Cause | Diagnostic | Solution |
|-------|------------|----------|
| Policy collapse | Entropy drops to 0 | Increase ent_coef |
| Learning rate too high | Large policy changes | Decrease LR, smaller clip_range |
| Overfitting to replay | Off-policy algorithms | Smaller batch, more exploration |
| Environment non-stationarity | Sudden reward change | Check env for bugs |

### 3. High Variance / Unstable Training

**Symptoms:**
- Reward oscillates wildly
- Different seeds give very different results
- Hard to reproduce results

**Diagnostics:**
```python
# Run multiple seeds
results = []
for seed in [0, 1, 2, 3, 4]:
    model = PPO("MlpPolicy", env, seed=seed, verbose=0)
    model.learn(total_timesteps=100_000)
    mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=10)
    results.append(mean_reward)

print(f"Mean: {np.mean(results):.2f}, Std: {np.std(results):.2f}")
# Std > 50% of mean indicates high variance
```

**Causes and Solutions:**

| Cause | Diagnostic | Solution |
|-------|------------|----------|
| Too few environments | n_envs < 4 | Increase parallel envs |
| High-variance returns | Long episodes | Use GAE, normalize rewards |
| Aggressive updates | Large policy changes | Smaller LR, clip_range |
| Noisy gradients | Small batch size | Larger batch, more n_steps |

### 4. NaN or Numerical Instability

**Symptoms:**
- Loss becomes NaN
- Actions become NaN/Inf
- Training crashes

**Diagnostics:**
```python
# Add NaN checks
import torch

def check_for_nan(model, name=""):
    for param_name, param in model.policy.named_parameters():
        if torch.isnan(param).any():
            print(f"NaN in {name} {param_name}")
        if torch.isinf(param).any():
            print(f"Inf in {name} {param_name}")
```

**Causes and Solutions:**

| Cause | Diagnostic | Solution |
|-------|------------|----------|
| Exploding gradients | Large gradient norms | Reduce LR; tighten clipping by *lowering* `max_grad_norm` (e.g. 0.5 → 0.3) |
| Large observations | \|obs\| > ~100 | Normalize observations (`VecNormalize`), except uint8 images |
| Large rewards | \|reward\| > ~100 | Normalize or clip rewards |
| Log of zero | In policy distribution | Add epsilon to probabilities |
| Division by std~0 | In normalization | Add epsilon to denominator |

---

## Reward Curve Interpretation

### Healthy Training Curves

```
Good PPO curve:
    ^
    |           ____----
    |      ____/
reward|  __/
    | /
    |/
    +-----------------------> timesteps

Characteristics:
- Gradual improvement
- May have plateaus
- Some variance is normal
```

### Problem Patterns

```
Policy Collapse:
    ^
    |    ___
    |   /   \
reward| /     \___
    |/           \_______
    +-----------------------> timesteps

Diagnosis: Entropy dropping, increase ent_coef


Reward Hacking:
    ^
    |                 ____
    |            ____/
reward|       ____/
    |  ____/
    |_/
    +-----------------------> timesteps

But evaluation performance is poor!
Diagnosis: Agent exploiting reward, fix reward function


No Learning:
    ^
    |
    |  ~~~~~~~~~~~~~~~~~~~~~~~~
reward|
    |
    +-----------------------> timesteps

Diagnosis: Check LR, exploration, reward sparsity
```

---

## Policy Entropy Monitoring

### Why Entropy Matters

- **High entropy**: Policy is stochastic, exploring
- **Low entropy**: Policy is deterministic, exploiting
- **Zero entropy**: Policy collapse, stuck on single action

### Monitoring Entropy

You don't need a custom callback: PPO and A2C log `train/entropy_loss` to TensorBoard every update. It is the **negative** of the policy's mean entropy, so a healthy discrete policy shows a value like -0.7, and collapse shows as the value rising toward 0. Read entropy as `-entropy_loss` when comparing with the table below. For continuous (Gaussian) policies entropy can legitimately be negative, so watch the trend rather than a fixed threshold.

### Entropy Guidelines by Algorithm

| Algorithm | Healthy entropy (= -entropy_loss) | Concern |
|-----------|----------------------|-------------------|
| PPO (discrete) | 0.3 - 2.0 | below ~0.1 early in training |
| PPO (continuous) | depends on action dimension and scale | a steady fall toward its minimum before reward improves |
| SAC | auto-tuned | `ent_coef` stuck near 0 or exploding |
| A2C | 0.3 - 2.0 | below ~0.1 early in training |

---

## Value Function Diagnostics

### Explained Variance

Measures how well value function predicts returns.

```python
# SB3 logs this as "train/explained_variance"
# In TensorBoard, look for values:
# - Near 1.0: Value function very accurate (good)
# - Near 0.0: Value function no better than mean (needs tuning)
# - Negative: Value function worse than mean (problem!)
```

### Manual Value Function Check

```python
def diagnose_value_function(model, env, n_episodes=10):
    """Check if value function predictions are reasonable."""

    all_values = []
    all_returns = []

    for _ in range(n_episodes):
        obs = env.reset()
        episode_rewards = []
        episode_values = []

        done = False
        while not done:
            # Get value prediction
            obs_tensor = torch.tensor(obs).float().unsqueeze(0)
            with torch.no_grad():
                value = model.policy.predict_values(obs_tensor).item()
            episode_values.append(value)

            # Take step
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_rewards.append(reward)

        # Compute actual returns (discounted)
        gamma = model.gamma
        returns = []
        G = 0
        for r in reversed(episode_rewards):
            G = r + gamma * G
            returns.insert(0, G)

        all_values.extend(episode_values)
        all_returns.extend(returns)

    values = np.array(all_values)
    returns = np.array(all_returns)

    # Compute correlation
    correlation = np.corrcoef(values, returns)[0, 1]

    # Compute explained variance
    var_returns = np.var(returns)
    var_unexplained = np.var(returns - values)
    explained_var = 1 - var_unexplained / var_returns if var_returns > 0 else 0

    print(f"Value-Return Correlation: {correlation:.3f}")
    print(f"Explained Variance: {explained_var:.3f}")
    print(f"Value range: [{values.min():.2f}, {values.max():.2f}]")
    print(f"Return range: [{returns.min():.2f}, {returns.max():.2f}]")

    if explained_var < 0:
        print("WARNING: Negative explained variance - value function is harmful")
    elif explained_var < 0.5:
        print("WARNING: Low explained variance - consider tuning vf_coef or network")

    return explained_var, correlation
```

---

## The Deadly Triad

The deadly triad in RL refers to the combination that can cause instability:
1. **Function approximation** (neural networks)
2. **Bootstrapping** (using value estimates to update value estimates)
3. **Off-policy learning** (learning from old experience)

### Mitigation Strategies

```python
# 1. Target networks (for off-policy)
# DQN, SAC, TD3 use target networks by default
model = DQN("MlpPolicy", env, target_update_interval=1000)

# 2. Gradient clipping
model = PPO("MlpPolicy", env, max_grad_norm=0.5)

# 3. Conservative value updates
model = PPO("MlpPolicy", env, vf_coef=0.5)  # Weight value loss less

# 4. Double Q-learning (DQN)
# Decouples action selection from value estimation

# 5. Soft updates (SAC, TD3)
model = SAC("MlpPolicy", env, tau=0.005)  # Slow target updates
```

---

## Debugging Workflow

### Step-by-Step Process

```
1. Verify environment works
   └─ Run random policy, check rewards

2. Check observations
   └─ Appropriate scale? Contains needed info?

3. Test with simple baseline
   └─ Does DQN/PPO work on CartPole?

4. Start with defaults
   └─ Only tune after confirming learning

5. Monitor training
   └─ TensorBoard: reward, losses, entropy

6. If no learning:
   ├─ Check learning rate (try 10x higher/lower)
   ├─ Check exploration (entropy, epsilon)
   ├─ Check reward sparsity
   └─ Verify environment determinism

7. If unstable:
   ├─ Reduce learning rate
   ├─ Increase batch size
   ├─ Add normalization
   └─ Try different seeds

8. If NaN:
   ├─ Check observation/reward scale
   ├─ Reduce learning rate
   └─ Tighten gradient clipping (lower max_grad_norm)
```

### Minimal Reproducible Example

When debugging, reduce to simplest case:

```python
import gymnasium as gym
from stable_baselines3 import PPO

# 1. Start with known-working environment
env = gym.make("CartPole-v1")

# 2. Default parameters
model = PPO("MlpPolicy", env, verbose=1)

# 3. Short training
model.learn(total_timesteps=10_000)

# 4. Quick evaluation
obs, _ = env.reset()
for _ in range(100):
    action, _ = model.predict(obs)
    obs, reward, done, truncated, info = env.step(action)
    if done or truncated:
        break

# If this works, incrementally add complexity
# If this fails, environment issue or installation problem
```

---

## Logging for Debugging

```python
from stable_baselines3.common.logger import configure

# Set up detailed logging
logger = configure("./logs", ["stdout", "tensorboard", "csv"])

model = PPO("MlpPolicy", env, verbose=1)
model.set_logger(logger)

# Custom logging in callbacks
class DebugCallback(BaseCallback):
    def _on_step(self):
        # Log custom metrics
        self.logger.record("debug/custom_metric", some_value)

        # Log histograms (TensorBoard)
        self.logger.record("debug/actions", self.locals["actions"], exclude="stdout")

        return True
```

### Key TensorBoard Metrics

| Metric | What It Shows | Warning Signs |
|--------|---------------|---------------|
| rollout/ep_rew_mean | Episode reward | Flat, declining |
| train/entropy_loss | Negative entropy (policy randomness) | Rising toward 0 early in training (collapse) |
| train/policy_gradient_loss | Policy update magnitude | Very large/small |
| train/value_loss | Value function error | Increasing |
| train/explained_variance | Value function quality | Negative |
| train/clip_fraction | PPO clipping | > 0.3 consistently |
| train/approx_kl | Policy change | > 0.1 (PPO) |
