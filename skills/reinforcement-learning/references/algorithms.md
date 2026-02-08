# RL Algorithms Deep Dive

## Overview

This reference covers the most important RL algorithms, when to use each, and key hyperparameters.

## Algorithm Categories

### On-Policy vs Off-Policy

- **On-Policy** (PPO, A2C): Learn from current policy's experience only. More stable but less sample efficient.
- **Off-Policy** (DQN, SAC, TD3): Learn from replay buffer of past experience. More sample efficient but can be unstable.

### Value-Based vs Policy-Based

- **Value-Based** (DQN): Learn Q-values, derive policy by taking argmax. Only works for discrete actions.
- **Policy-Based** (PPO, SAC): Directly optimize the policy. Works for both discrete and continuous.

---

## DQN (Deep Q-Network)

### When to Use
- Discrete action spaces
- Sample efficiency is important
- Can tolerate some instability

### How It Works
1. Maintain Q-network that estimates Q(s, a)
2. Store transitions in replay buffer
3. Sample mini-batches and minimize TD error
4. Use target network for stability (soft or hard updates)

### Key Variants

**Double DQN**: Addresses overestimation bias by decoupling action selection and evaluation.
```python
# Standard DQN (overestimates)
target = r + gamma * max(Q_target(s'))

# Double DQN (less bias)
a_best = argmax(Q_online(s'))
target = r + gamma * Q_target(s', a_best)
```

**Dueling DQN**: Separates value and advantage streams.
```python
Q(s, a) = V(s) + A(s, a) - mean(A(s, :))
```

### Key Hyperparameters

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| learning_rate | 1e-4 | 1e-5 to 1e-3 | Lower for stability |
| buffer_size | 1e6 | 1e4 to 1e7 | Larger = more diverse experience |
| batch_size | 32 | 32 to 256 | Larger = more stable gradients |
| gamma | 0.99 | 0.9 to 0.999 | Higher for long-horizon tasks |
| target_update_interval | 10000 | 1000 to 50000 | Steps between target network updates |
| exploration_fraction | 0.1 | 0.05 to 0.3 | Fraction of training for epsilon decay |
| exploration_final_eps | 0.05 | 0.01 to 0.1 | Final exploration rate |

### SB3 Example

```python
from stable_baselines3 import DQN

model = DQN(
    "MlpPolicy",
    "CartPole-v1",
    learning_rate=1e-4,
    buffer_size=100_000,
    learning_starts=1000,
    batch_size=32,
    gamma=0.99,
    target_update_interval=1000,
    exploration_fraction=0.1,
    exploration_final_eps=0.05,
    verbose=1
)
model.learn(total_timesteps=100_000)
```

---

## PPO (Proximal Policy Optimization)

### When to Use
- General purpose, good default choice
- Stability is important
- Discrete or continuous actions
- Parallel environments available

### How It Works
1. Collect rollouts using current policy
2. Compute advantages (GAE)
3. Optimize clipped surrogate objective
4. Repeat

### Key Innovation
Clips the policy ratio to prevent too large updates:
```python
ratio = pi_new(a|s) / pi_old(a|s)
clipped_ratio = clip(ratio, 1 - epsilon, 1 + epsilon)
loss = -min(ratio * A, clipped_ratio * A)
```

### Key Hyperparameters

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| learning_rate | 3e-4 | 1e-5 to 1e-3 | Often schedule to decay |
| n_steps | 2048 | 128 to 4096 | Steps per rollout per env |
| batch_size | 64 | 32 to 512 | Mini-batch size for updates |
| n_epochs | 10 | 3 to 30 | Passes over collected data |
| gamma | 0.99 | 0.9 to 0.999 | Discount factor |
| gae_lambda | 0.95 | 0.9 to 1.0 | GAE parameter |
| clip_range | 0.2 | 0.1 to 0.3 | PPO clipping parameter |
| ent_coef | 0.0 | 0.0 to 0.1 | Entropy bonus coefficient |
| vf_coef | 0.5 | 0.25 to 1.0 | Value function loss weight |
| max_grad_norm | 0.5 | 0.3 to 1.0 | Gradient clipping |

### SB3 Example

```python
from stable_baselines3 import PPO

model = PPO(
    "MlpPolicy",
    "CartPole-v1",
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,  # Add entropy bonus for exploration
    verbose=1,
    tensorboard_log="./ppo_logs/"
)
model.learn(total_timesteps=100_000)
```

---

## SAC (Soft Actor-Critic)

### When to Use
- Continuous action spaces
- Sample efficiency is critical
- Can handle entropy tuning automatically

### How It Works
1. Maximize expected return + entropy bonus
2. Learn Q-function, V-function, and policy
3. Automatic entropy coefficient tuning
4. Off-policy with replay buffer

### Key Innovation
Maximizes entropy-augmented reward:
```python
J(pi) = E[sum(r + alpha * H(pi(.|s)))]
```
This encourages exploration and robustness.

### Key Hyperparameters

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| learning_rate | 3e-4 | 1e-5 to 1e-3 | Same for all networks |
| buffer_size | 1e6 | 1e5 to 1e7 | Replay buffer size |
| batch_size | 256 | 64 to 512 | Mini-batch size |
| gamma | 0.99 | 0.9 to 0.999 | Discount factor |
| tau | 0.005 | 0.001 to 0.05 | Soft update coefficient |
| ent_coef | "auto" | "auto" or float | Entropy coefficient |
| target_entropy | "auto" | "auto" or float | Target entropy |
| learning_starts | 100 | 100 to 10000 | Steps before learning |

### SB3 Example

```python
from stable_baselines3 import SAC

model = SAC(
    "MlpPolicy",
    "Pendulum-v1",
    learning_rate=3e-4,
    buffer_size=1_000_000,
    batch_size=256,
    gamma=0.99,
    tau=0.005,
    ent_coef="auto",  # Automatic entropy tuning
    verbose=1,
    tensorboard_log="./sac_logs/"
)
model.learn(total_timesteps=100_000)
```

---

## TD3 (Twin Delayed DDPG)

### When to Use
- Continuous action spaces
- Alternative to SAC
- When SAC's entropy bonus causes issues

### How It Works
1. Twin Q-networks (take minimum to reduce overestimation)
2. Delayed policy updates (update policy less frequently than Q)
3. Target policy smoothing (add noise to target actions)

### Key Improvements Over DDPG
```python
# Twin Q-networks
target_Q = min(Q1_target(s', a'), Q2_target(s', a'))

# Target policy smoothing
noise = clip(N(0, sigma), -c, c)
a' = clip(pi_target(s') + noise, a_low, a_high)

# Delayed policy updates
if step % policy_delay == 0:
    update_policy()
```

### Key Hyperparameters

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| learning_rate | 1e-3 | 1e-4 to 1e-3 | Same for actor and critic |
| buffer_size | 1e6 | 1e5 to 1e7 | Replay buffer size |
| batch_size | 100 | 64 to 256 | Mini-batch size |
| gamma | 0.99 | 0.9 to 0.999 | Discount factor |
| tau | 0.005 | 0.001 to 0.05 | Soft update coefficient |
| policy_delay | 2 | 1 to 4 | Update policy every N critic updates |
| target_policy_noise | 0.2 | 0.1 to 0.5 | Noise added to target actions |
| target_noise_clip | 0.5 | 0.1 to 1.0 | Noise clipping range |

### SB3 Example

```python
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise
import numpy as np

env = gym.make("Pendulum-v1")
n_actions = env.action_space.shape[-1]
action_noise = NormalActionNoise(
    mean=np.zeros(n_actions),
    sigma=0.1 * np.ones(n_actions)
)

model = TD3(
    "MlpPolicy",
    env,
    learning_rate=1e-3,
    buffer_size=1_000_000,
    batch_size=100,
    gamma=0.99,
    tau=0.005,
    policy_delay=2,
    action_noise=action_noise,
    verbose=1
)
model.learn(total_timesteps=100_000)
```

---

## A2C (Advantage Actor-Critic)

### When to Use
- Simpler alternative to PPO
- Fast iteration needed
- Many parallel environments available
- Lower sample efficiency is acceptable

### How It Works
1. Synchronous version of A3C
2. Multiple parallel environments
3. Actor-critic with advantage estimation
4. No replay buffer (on-policy)

### Key Hyperparameters

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| learning_rate | 7e-4 | 1e-4 to 1e-3 | Often higher than PPO |
| n_steps | 5 | 5 to 128 | Steps per rollout (shorter than PPO) |
| gamma | 0.99 | 0.9 to 0.999 | Discount factor |
| gae_lambda | 1.0 | 0.9 to 1.0 | GAE parameter |
| ent_coef | 0.0 | 0.0 to 0.1 | Entropy bonus |
| vf_coef | 0.5 | 0.25 to 1.0 | Value function loss weight |
| max_grad_norm | 0.5 | 0.3 to 1.0 | Gradient clipping |

### SB3 Example

```python
from stable_baselines3 import A2C

model = A2C(
    "MlpPolicy",
    "CartPole-v1",
    learning_rate=7e-4,
    n_steps=5,
    gamma=0.99,
    gae_lambda=1.0,
    ent_coef=0.01,
    vf_coef=0.5,
    verbose=1
)
model.learn(total_timesteps=100_000)
```

---

## Algorithm Comparison Summary

| Algorithm | Action Space | On/Off Policy | Sample Efficiency | Stability | Complexity |
|-----------|--------------|---------------|-------------------|-----------|------------|
| DQN | Discrete | Off | High | Medium | Medium |
| PPO | Both | On | Low | High | Medium |
| SAC | Continuous | Off | High | High | High |
| TD3 | Continuous | Off | High | Medium | High |
| A2C | Both | On | Low | Medium | Low |

## Decision Flowchart

```
Need to train an RL agent?
│
├─ Discrete actions?
│  ├─ Sample efficiency critical? → DQN (Double/Dueling)
│  ├─ Stability critical? → PPO
│  └─ Fast prototyping? → A2C
│
└─ Continuous actions?
   ├─ Sample efficiency critical?
   │  ├─ Want automatic entropy? → SAC
   │  └─ Prefer deterministic policy? → TD3
   └─ Stability critical? → PPO
```
