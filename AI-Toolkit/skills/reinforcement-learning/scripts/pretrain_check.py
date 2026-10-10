#!/usr/bin/env python3
"""Pre-training sanity check for a Gymnasium environment.

Run this AFTER validate_env.py passes and BEFORE launching training. It
establishes a random-policy baseline and flags environment properties that
commonly break or slow RL training:

- Random-policy baseline: mean/std episodic return (the number your trained
  agent must beat)
- Observation distribution stats (mean/std/min/max) and bounds
- Reward distribution stats (constant, sparse, huge-scale rewards)
- Episode-length sanity (always truncating, or degenerate 1-step episodes)
- Actionable warnings: unbounded observations, constant rewards, huge action
  ranges, reward scale issues

Usage:
    python pretrain_check.py CartPole-v1
    python pretrain_check.py my_package.envs:CustomEnv --episodes 30

Exits 0 on success (warnings are advisory), 1 if the environment cannot be
rolled out or produces NaN/Inf values.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    print("ERROR: gymnasium is not installed. Run: pip install gymnasium")
    sys.exit(2)


def make_env(spec: str) -> gym.Env:
    """Instantiate the environment from a gym id or 'module:Class' spec."""
    if ":" in spec:
        # Make `module.path:EnvClass` importable from the directory the user ran
        # the script in. Python puts the *script's* folder on sys.path, not the
        # current directory, so without this a project's own package can't be found.
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        module_name, class_name = spec.split(":", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)()
    return gym.make(spec)


def flatten_obs(obs) -> np.ndarray:
    if isinstance(obs, dict):
        parts = [np.asarray(v, dtype=np.float64).ravel() for v in obs.values()]
        return np.concatenate(parts) if parts else np.array([])
    if isinstance(obs, (tuple, list)):
        parts = [np.asarray(v, dtype=np.float64).ravel() for v in obs]
        return np.concatenate(parts) if parts else np.array([])
    return np.asarray(obs, dtype=np.float64).ravel()


def stats_line(name: str, values: np.ndarray) -> str:
    return (
        f"  {name}: mean={np.mean(values):.4g} std={np.std(values):.4g} "
        f"min={np.min(values):.4g} max={np.max(values):.4g}"
    )


def collect_rollouts(env: gym.Env, episodes: int, max_steps: int, seed: int):
    episode_returns: list[float] = []
    episode_lengths: list[int] = []
    terminated_count = 0
    truncated_count = 0
    all_obs: list[np.ndarray] = []
    all_rewards: list[float] = []

    env.action_space.seed(seed)
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        all_obs.append(flatten_obs(obs))
        total = 0.0
        steps = 0
        for _ in range(max_steps):
            obs, reward, terminated, truncated, _ = env.step(
                env.action_space.sample()
            )
            all_obs.append(flatten_obs(obs))
            all_rewards.append(float(reward))
            total += float(reward)
            steps += 1
            if terminated or truncated:
                if terminated:
                    terminated_count += 1
                if truncated:
                    truncated_count += 1
                break
        episode_returns.append(total)
        episode_lengths.append(steps)

    return (
        np.array(episode_returns),
        np.array(episode_lengths),
        np.array(all_rewards),
        np.stack(all_obs) if all_obs and all_obs[0].size else np.array([]),
        terminated_count,
        truncated_count,
    )


def space_warnings(env: gym.Env, warnings: list[str]) -> None:
    obs_space = env.observation_space
    act_space = env.action_space

    if isinstance(obs_space, spaces.Box):
        if not (np.all(np.isfinite(obs_space.low)) and np.all(np.isfinite(obs_space.high))):
            warnings.append(
                "Observation space has unbounded (+/-inf) dimensions. Use "
                "NormalizeObservation or SB3's VecNormalize so the network sees "
                "a reasonable input scale."
            )
    if isinstance(act_space, spaces.Box):
        if not (np.all(np.isfinite(act_space.low)) and np.all(np.isfinite(act_space.high))):
            warnings.append(
                "Action space has unbounded (+/-inf) dimensions. Bound it, or "
                "wrap with ClipAction / RescaleAction."
            )
        else:
            span = np.max(act_space.high - act_space.low)
            if span > 10:
                warnings.append(
                    f"Action range spans up to {span:.4g}. Most algorithms (SAC, "
                    "TD3, PPO with squashed Gaussian) expect roughly [-1, 1]; "
                    "wrap with RescaleAction(env, -1.0, 1.0)."
                )


def data_warnings(
    returns: np.ndarray,
    lengths: np.ndarray,
    rewards: np.ndarray,
    obs: np.ndarray,
    terminated_count: int,
    truncated_count: int,
    max_steps: int,
    warnings: list[str],
    image_obs: bool = False,
) -> None:
    if rewards.size:
        if np.std(rewards) == 0:
            warnings.append(
                f"All step rewards are constant ({rewards[0]:.4g}) under a random "
                "policy. If the informative reward is rare (sparse), consider "
                "reward shaping or intrinsic motivation; if the reward is truly "
                "constant, the agent has no learning signal at all."
            )
        else:
            nonzero_frac = float(np.mean(rewards != 0))
            if nonzero_frac < 0.01:
                warnings.append(
                    f"Only {nonzero_frac:.2%} of steps produce a nonzero reward "
                    "(sparse reward). Expect slow learning; consider shaping, "
                    "curriculum, or HER for goal-based tasks."
                )
        if np.max(np.abs(rewards)) > 100:
            warnings.append(
                f"Reward magnitudes reach {np.max(np.abs(rewards)):.4g}. Large "
                "reward scales destabilize value learning; wrap with "
                "NormalizeReward or clip rewards."
            )
    # Image observations (uint8 pixels, 0-255) are expected to be large; SB3's
    # CnnPolicy scales them itself, and VecNormalize on pixels hurts learning.
    if obs.size and not image_obs:
        max_abs_obs = float(np.max(np.abs(obs)))
        if max_abs_obs > 100:
            warnings.append(
                f"Observed observation magnitudes reach {max_abs_obs:.4g}. "
                "Normalize observations (NormalizeObservation / VecNormalize) "
                "before training."
            )
    if lengths.size:
        if terminated_count == 0 and truncated_count > 0:
            warnings.append(
                "No episode ended via terminated=True (all hit the time limit). "
                "Fine for pure time-limited tasks, but verify you are not "
                "signalling natural task endings as truncations - bootstrapping "
                "handles the two differently."
            )
        if terminated_count == 0 and truncated_count == 0:
            warnings.append(
                f"No episode ended within {max_steps} steps. Add a time limit "
                "(TimeLimit wrapper or max_episode_steps at registration)."
            )
        if np.max(lengths) <= 1:
            warnings.append(
                "Every episode ends after a single step. Check the termination "
                "condition - the agent never gets a chance to act."
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Random-policy baseline and sanity checks before RL training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "env_spec",
        help="Registered gym id (e.g. CartPole-v1) or module.path:EnvClass",
    )
    parser.add_argument("--episodes", type=int, default=20, help="rollout episodes")
    parser.add_argument(
        "--max-steps", type=int, default=10_000, help="step cap per episode"
    )
    parser.add_argument("--seed", type=int, default=42, help="base seed")
    args = parser.parse_args()

    try:
        env = make_env(args.env_spec)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not instantiate environment: {exc}")
        return 1

    print(f"Pre-training check: {args.env_spec}")
    print(f"  observation_space: {env.observation_space}")
    print(f"  action_space:      {env.action_space}\n")

    try:
        (
            returns,
            lengths,
            rewards,
            obs,
            terminated_count,
            truncated_count,
        ) = collect_rollouts(env, args.episodes, args.max_steps, args.seed)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: rollout failed: {type(exc).__name__}: {exc}")
        env.close()
        return 1
    finally:
        env.close()

    finite_ok = (
        (not obs.size or np.all(np.isfinite(obs)))
        and (not rewards.size or np.all(np.isfinite(rewards)))
    )
    if not finite_ok:
        print("ERROR: NaN/Inf encountered in observations or rewards.")
        return 1

    print(f"Random-policy baseline over {args.episodes} episodes:")
    print(stats_line("episodic return", returns))
    print(stats_line("episode length", lengths.astype(np.float64)))
    print(
        f"  endings: terminated={terminated_count} truncated={truncated_count} "
        f"neither(hit step cap)={args.episodes - terminated_count - truncated_count}"
    )
    print("\nStep-level distributions:")
    if rewards.size:
        print(stats_line("reward", rewards))
        print(f"  nonzero-reward steps: {np.mean(rewards != 0):.2%}")
    if obs.size:
        print(stats_line("observation (flattened)", obs))

    warnings: list[str] = []
    env2 = make_env(args.env_spec)
    try:
        space_warnings(env2, warnings)
        obs_space = env2.observation_space
        image_obs = (
            isinstance(obs_space, spaces.Box)
            and obs_space.dtype == np.uint8
            and len(obs_space.shape) >= 2
        )
    finally:
        env2.close()
    data_warnings(
        returns,
        lengths,
        rewards,
        obs,
        terminated_count,
        truncated_count,
        args.max_steps,
        warnings,
        image_obs=image_obs,
    )

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    else:
        print("\nNo warnings - environment looks ready for training.")

    print(
        "\nA trained agent must clearly beat the random-policy return of "
        f"{np.mean(returns):.2f} +/- {np.std(returns):.2f} to demonstrate learning."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
