# Gymnasium Environments Guide

## Overview

Gymnasium (the maintained fork of OpenAI Gym) is the standard API for RL environments. This guide covers setup, custom environments, vectorization, and essential wrappers.

## Installation

```bash
# Core gymnasium
pip install gymnasium

# Atari environments
pip install gymnasium[atari] gymnasium[accept-rom-license]

# MuJoCo environments
pip install gymnasium[mujoco]

# Box2D environments (LunarLander, etc.)
pip install gymnasium[box2d]

# All classic control
pip install gymnasium[classic-control]
```

## Migration from OpenAI Gym

### Key Changes

```python
# Old (gym)
import gym
env = gym.make("CartPole-v1")
obs = env.reset()
obs, reward, done, info = env.step(action)

# New (gymnasium)
import gymnasium as gym
env = gym.make("CartPole-v1")
obs, info = env.reset()  # Returns tuple now
obs, reward, terminated, truncated, info = env.step(action)  # 5 values
done = terminated or truncated
```

### Terminated vs Truncated

- **terminated**: Episode ended due to task completion or failure (e.g., pole fell, goal reached)
- **truncated**: Episode ended due to time limit or external condition (e.g., max steps)

```python
obs, reward, terminated, truncated, info = env.step(action)

if terminated:
    print("Task ended naturally")
if truncated:
    print("Episode cut short (time limit)")
if terminated or truncated:
    obs, info = env.reset()
```

---

## Custom Environment Template

### Complete Example

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Optional, Tuple, Dict, Any

class CustomEnv(gym.Env):
    """
    Custom Environment following Gymnasium API.

    Description:
        A simple environment where an agent must reach a goal position.

    Observation Space:
        Box(4,) - [agent_x, agent_y, goal_x, goal_y]

    Action Space:
        Discrete(4) - [up, down, left, right]

    Rewards:
        -1 per step, +10 for reaching goal
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 30
    }

    def __init__(self, render_mode: Optional[str] = None, grid_size: int = 10):
        super().__init__()

        self.grid_size = grid_size
        self.render_mode = render_mode

        # Define observation space
        self.observation_space = spaces.Box(
            low=0,
            high=grid_size,
            shape=(4,),
            dtype=np.float32
        )

        # Define action space
        self.action_space = spaces.Discrete(4)

        # Action mappings
        self._action_to_direction = {
            0: np.array([0, 1]),   # up
            1: np.array([0, -1]),  # down
            2: np.array([-1, 0]),  # left
            3: np.array([1, 0])    # right
        }

        # State
        self.agent_pos = None
        self.goal_pos = None
        self.steps = 0
        self.max_steps = 100

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to initial state."""
        super().reset(seed=seed)

        # Initialize positions randomly
        self.agent_pos = self.np_random.integers(0, self.grid_size, size=2).astype(np.float32)
        self.goal_pos = self.np_random.integers(0, self.grid_size, size=2).astype(np.float32)

        # Ensure agent and goal are not at same position
        while np.array_equal(self.agent_pos, self.goal_pos):
            self.goal_pos = self.np_random.integers(0, self.grid_size, size=2).astype(np.float32)

        self.steps = 0

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one step in the environment."""
        # Move agent
        direction = self._action_to_direction[action]
        self.agent_pos = np.clip(
            self.agent_pos + direction,
            0,
            self.grid_size - 1
        ).astype(np.float32)

        self.steps += 1

        # Check termination
        reached_goal = np.array_equal(self.agent_pos, self.goal_pos)
        terminated = reached_goal
        truncated = self.steps >= self.max_steps

        # Compute reward
        if reached_goal:
            reward = 10.0
        else:
            reward = -1.0

        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, truncated, info

    def _get_obs(self) -> np.ndarray:
        """Construct observation from state."""
        return np.concatenate([self.agent_pos, self.goal_pos]).astype(np.float32)

    def _get_info(self) -> Dict[str, Any]:
        """Return auxiliary info."""
        return {
            "distance": np.linalg.norm(self.agent_pos - self.goal_pos),
            "steps": self.steps
        }

    def render(self):
        """Render the environment."""
        if self.render_mode == "human":
            self._render_human()
        elif self.render_mode == "rgb_array":
            return self._render_rgb_array()

    def _render_human(self):
        """Render to screen."""
        print(f"Agent: {self.agent_pos}, Goal: {self.goal_pos}")

    def _render_rgb_array(self) -> np.ndarray:
        """Return RGB array of current state."""
        # Create simple grid visualization
        img = np.zeros((self.grid_size * 10, self.grid_size * 10, 3), dtype=np.uint8)
        # Add agent (blue) and goal (green)
        ax, ay = (self.agent_pos * 10).astype(int)
        gx, gy = (self.goal_pos * 10).astype(int)
        img[ay:ay+10, ax:ax+10] = [0, 0, 255]  # Agent blue
        img[gy:gy+10, gx:gx+10] = [0, 255, 0]  # Goal green
        return img

    def close(self):
        """Clean up resources."""
        pass
```

### Registering Custom Environment

```python
from gymnasium.envs.registration import register

register(
    id="CustomEnv-v0",
    entry_point="my_module:CustomEnv",
    max_episode_steps=100,
)

# Now can use:
env = gym.make("CustomEnv-v0")
```

---

## Environment Validation Checklist

Before training, validate your custom environment:

```python
from gymnasium.utils.env_checker import check_env

env = CustomEnv()
check_env(env, warn=True)  # Raises errors if API violated
```

### Manual Checks

```python
def validate_environment(env_class):
    """Comprehensive environment validation."""
    env = env_class()

    # 1. Check spaces are defined
    assert env.observation_space is not None, "observation_space not defined"
    assert env.action_space is not None, "action_space not defined"

    # 2. Check reset returns correct format
    obs, info = env.reset(seed=42)
    assert env.observation_space.contains(obs), f"Reset obs not in space: {obs}"
    assert isinstance(info, dict), "Info must be dict"

    # 3. Check step returns correct format
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    assert env.observation_space.contains(obs), f"Step obs not in space: {obs}"
    assert isinstance(reward, (int, float)), "Reward must be numeric"
    assert isinstance(terminated, bool), "Terminated must be bool"
    assert isinstance(truncated, bool), "Truncated must be bool"
    assert isinstance(info, dict), "Info must be dict"

    # 4. Check determinism with seed
    env.reset(seed=42)
    actions = [env.action_space.sample() for _ in range(10)]
    env.reset(seed=42)
    obs1, _ = env.reset(seed=123)
    for a in actions[:5]:
        obs1, _, _, _, _ = env.step(a)

    env.reset(seed=123)
    obs2, _ = env.reset(seed=123)
    for a in actions[:5]:
        obs2, _, _, _, _ = env.step(a)

    assert np.allclose(obs1, obs2), "Environment not deterministic with same seed"

    # 5. Check episode termination
    env.reset()
    for _ in range(10000):
        _, _, terminated, truncated, _ = env.step(env.action_space.sample())
        if terminated or truncated:
            break
    else:
        print("Warning: Episode did not terminate in 10000 steps")

    print("All checks passed!")
    env.close()

validate_environment(CustomEnv)
```

---

## Vectorized Environments

Vectorized environments run multiple instances in parallel for faster training.

### Types

```python
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env

# DummyVecEnv - Sequential (single process, good for debugging)
env = DummyVecEnv([lambda: gym.make("CartPole-v1") for _ in range(4)])

# SubprocVecEnv - Parallel (separate processes, faster)
env = SubprocVecEnv([lambda: gym.make("CartPole-v1") for _ in range(4)])

# Convenience function
env = make_vec_env("CartPole-v1", n_envs=4, vec_env_cls=SubprocVecEnv)
```

### When to Use Each

| Type | Use Case | Overhead | Speed |
|------|----------|----------|-------|
| DummyVecEnv | Debugging, simple envs | Low | Moderate |
| SubprocVecEnv | Complex envs, production | High (process creation) | Fast |

### Custom Environment with Vectorization

```python
def make_env(env_id, rank, seed=0):
    """Create a wrapped, monitored environment."""
    def _init():
        env = gym.make(env_id)
        env.reset(seed=seed + rank)
        return env
    return _init

# Create vectorized environment
n_envs = 4
env = SubprocVecEnv([make_env("CartPole-v1", i) for i in range(n_envs)])
```

---

## Essential Wrappers

### Observation Wrappers

```python
from gymnasium.wrappers import (
    NormalizeObservation,
    TransformObservation,
    FrameStack,
    GrayScaleObservation,
    ResizeObservation
)

# Normalize observations (running mean/std)
env = NormalizeObservation(env)

# Custom transformation
env = TransformObservation(env, lambda obs: obs / 255.0)

# Stack frames (for temporal info)
env = FrameStack(env, num_stack=4)

# Image preprocessing
env = GrayScaleObservation(env)
env = ResizeObservation(env, shape=(84, 84))
```

### Reward Wrappers

```python
from gymnasium.wrappers import (
    NormalizeReward,
    ClipReward,
    TransformReward
)

# Normalize rewards (running stats)
env = NormalizeReward(env, gamma=0.99)

# Clip rewards to range
env = ClipReward(env, min_reward=-1, max_reward=1)

# Custom reward transformation
env = TransformReward(env, lambda r: np.sign(r))
```

### Action Wrappers

```python
from gymnasium.wrappers import (
    ClipAction,
    RescaleAction
)

# Clip actions to valid range
env = ClipAction(env)

# Rescale actions
env = RescaleAction(env, min_action=-1.0, max_action=1.0)
```

### Monitoring Wrappers

```python
from gymnasium.wrappers import RecordVideo, RecordEpisodeStatistics

# Record videos
env = RecordVideo(env, video_folder="./videos", episode_trigger=lambda x: x % 100 == 0)

# Track episode statistics
env = RecordEpisodeStatistics(env)
# Access via info["episode"]["r"], info["episode"]["l"], info["episode"]["t"]
```

### SB3 Wrappers

```python
from stable_baselines3.common.vec_env import VecNormalize, VecFrameStack

# Normalize observations and rewards for vectorized envs
env = make_vec_env("Pendulum-v1", n_envs=4)
env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

# Stack frames
env = VecFrameStack(env, n_stack=4)

# Save and load normalization stats
env.save("vec_normalize.pkl")
env = VecNormalize.load("vec_normalize.pkl", env)
```

---

## Common Space Types

```python
from gymnasium import spaces
import numpy as np

# Discrete - single integer action
action_space = spaces.Discrete(4)  # 0, 1, 2, or 3

# MultiDiscrete - multiple discrete values
action_space = spaces.MultiDiscrete([3, 2, 4])  # [0-2, 0-1, 0-3]

# Box - continuous values
obs_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)
obs_space = spaces.Box(low=np.array([0, -np.inf]), high=np.array([1, np.inf]), dtype=np.float32)

# Dict - structured observations
obs_space = spaces.Dict({
    "position": spaces.Box(low=-10, high=10, shape=(2,)),
    "velocity": spaces.Box(low=-1, high=1, shape=(2,)),
    "target": spaces.Discrete(5)
})

# Tuple - multiple spaces
obs_space = spaces.Tuple([
    spaces.Box(low=0, high=255, shape=(84, 84, 3), dtype=np.uint8),
    spaces.Discrete(10)
])

# MultiBinary - binary flags
obs_space = spaces.MultiBinary(8)  # 8 binary values
```

---

## Environment Testing Script

```python
import gymnasium as gym
import numpy as np

def test_environment(env_or_id, n_episodes=5, render=False):
    """Test environment with random policy."""
    if isinstance(env_or_id, str):
        env = gym.make(env_or_id, render_mode="human" if render else None)
    else:
        env = env_or_id

    episode_rewards = []
    episode_lengths = []

    for ep in range(n_episodes):
        obs, info = env.reset()
        total_reward = 0
        steps = 0

        while True:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1

            if render:
                env.render()

            if terminated or truncated:
                break

        episode_rewards.append(total_reward)
        episode_lengths.append(steps)
        print(f"Episode {ep+1}: reward={total_reward:.2f}, length={steps}")

    print(f"\nSummary over {n_episodes} episodes:")
    print(f"  Mean reward: {np.mean(episode_rewards):.2f} +/- {np.std(episode_rewards):.2f}")
    print(f"  Mean length: {np.mean(episode_lengths):.1f} +/- {np.std(episode_lengths):.1f}")

    env.close()
    return episode_rewards, episode_lengths

# Usage
test_environment("CartPole-v1", n_episodes=10)
```
