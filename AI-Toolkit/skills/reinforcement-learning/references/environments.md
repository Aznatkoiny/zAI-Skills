# Gymnasium Environments Guide

## Overview

Gymnasium (the maintained fork of OpenAI Gym) is the standard API for RL environments. This guide covers setup, custom environments, vectorization, and essential wrappers.

## Installation

```bash
# Core gymnasium
pip install gymnasium

# Atari environments (ROMs ship inside ale-py >= 0.9; the old accept-rom-license extra is gone)
pip install "gymnasium[atari]"
# then, in code: import ale_py; gym.register_envs(ale_py)

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

> **Canonical runnable version: [`scripts/validate_env.py`](../scripts/validate_env.py).**
> It packages every check below (plus reward stats and NaN/Inf guards) as a CLI
> that exits nonzero on failure:
>
> ```bash
> python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/validate_env.py CartPole-v1
> python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/validate_env.py my_package.envs:CustomEnv --episodes 5 --seed 7
> ```
>
> The snippets below show the underlying patterns for reference — prefer the
> script over re-deriving them.

Before training, validate your custom environment:

```python
from gymnasium.utils.env_checker import check_env

env = CustomEnv()
check_env(env, warn=True)  # Raises errors if API violated
```

### Manual Checks (pattern reference)

The two checks people most often get wrong, in condensed form:

```python
# Determinism: sample the action sequence ONCE, then replay it twice
# from reset(seed=...) and compare observations with np.allclose.
actions = [env.action_space.sample() for _ in range(5)]

def rollout():
    obs, _ = env.reset(seed=123)
    trajectory = [obs]
    for a in actions:
        obs, _, terminated, truncated, _ = env.step(a)
        trajectory.append(obs)
        if terminated or truncated:
            break
    return trajectory

traj1, traj2 = rollout(), rollout()
assert len(traj1) == len(traj2), "Not deterministic with same seed"
for o1, o2 in zip(traj1, traj2):
    assert np.allclose(o1, o2), "Not deterministic with same seed"

# Episode termination: random actions must end the episode in bounded steps
obs, _ = env.reset(seed=42)
for _ in range(10_000):
    _, _, terminated, truncated, _ = env.step(env.action_space.sample())
    if terminated or truncated:
        break
else:
    print("Warning: episode did not terminate in 10000 steps")
```

`scripts/validate_env.py` additionally verifies: spaces are defined, `reset()`
returns `(obs, info)` with `obs` in the observation space, `step()` returns a
5-tuple with correct types, rewards are numeric and finite, and observations
never contain NaN/Inf under random rollouts.

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

Names below are for Gymnasium >= 1.0, which renamed `FrameStack` ->
`FrameStackObservation` and `GrayScaleObservation` -> `GrayscaleObservation`.

These are alternatives for different kinds of observation, not one chain to apply in order.

```python
import numpy as np
import gymnasium as gym
from gymnasium.wrappers import (
    NormalizeObservation,
    TransformObservation,
    FrameStackObservation,
    GrayscaleObservation,
    ResizeObservation,
)

# Vector observations: running mean/std normalization
env = NormalizeObservation(env)

# Custom transformation (Gymnasium >= 1.0 requires the resulting observation space)
env = TransformObservation(
    env,
    lambda obs: (obs / 10.0).astype(np.float32),
    gym.spaces.Box(low=-np.inf, high=np.inf, shape=env.observation_space.shape, dtype=np.float32),
)
```

For image observations the order matters: grayscale and resize the raw uint8 frame first, then stack frames. Grayscale fails on already-stacked frames, and don't add `NormalizeObservation` to pixels (SB3's `CnnPolicy` scales uint8 images itself).

```python
env = gym.make("ALE/Pong-v5")
env = GrayscaleObservation(env)                  # (210, 160, 3) uint8 -> (210, 160)
env = ResizeObservation(env, shape=(84, 84))     # -> (84, 84)
env = FrameStackObservation(env, stack_size=4)   # -> (4, 84, 84)
```

`ResizeObservation` needs OpenCV (`pip install "gymnasium[other]"`; `stable-baselines3[extra]` includes it). For standard Atari preprocessing, `gymnasium.wrappers.AtariPreprocessing` or SB3's `make_atari_env` do all of this in one step.

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

> **Canonical runnable version: [`scripts/pretrain_check.py`](../scripts/pretrain_check.py).**
> It runs random-policy rollouts and reports the baseline return, observation
> and reward distribution stats, episode-length sanity, and actionable warnings
> (unbounded observations, constant/sparse rewards, huge action ranges):
>
> ```bash
> python3 ${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/pretrain_check.py CartPole-v1 --episodes 20
> ```
>
> The mean random-policy return it prints is the number a trained agent must
> clearly beat.
