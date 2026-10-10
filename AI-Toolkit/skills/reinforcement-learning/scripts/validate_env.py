#!/usr/bin/env python3
"""Validate a Gymnasium (>= 1.0) environment before training.

Runs the checks described in references/environments.md as a single CLI:

1. Gymnasium API compliance via ``gymnasium.utils.env_checker.check_env``
2. Observation / action space checks (reset and step outputs stay in-space)
3. Reward statistics over random rollouts, with NaN/Inf guards
4. Determinism: same seed + same action sequence -> identical trajectories
   (the corrected ``reset(seed=...)`` -> replay -> ``np.allclose`` pattern)
5. Episode termination within a bounded number of steps

Usage:
    python validate_env.py CartPole-v1
    python validate_env.py my_package.envs:CustomEnv
    python validate_env.py my_package.envs:CustomEnv --episodes 5 --seed 7

The environment spec is either a registered Gymnasium id (``CartPole-v1``)
or ``module.path:EnvClass`` for an unregistered custom environment class
importable from the current working directory (the script adds it to sys.path).

Exits 0 when every check passes, 1 when any check fails.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import traceback

import numpy as np

try:
    import gymnasium as gym
    from gymnasium.utils.env_checker import check_env
except ImportError:
    print("ERROR: gymnasium is not installed. Run: pip install gymnasium")
    sys.exit(2)


PASS = "PASS"
FAIL = "FAIL"


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
        env_class = getattr(module, class_name)
        return env_class()
    return gym.make(spec)


def flatten_obs(obs) -> np.ndarray:
    """Best-effort flatten of an observation into a float array for NaN checks."""
    if isinstance(obs, dict):
        parts = [np.asarray(v, dtype=np.float64).ravel() for v in obs.values()]
        return np.concatenate(parts) if parts else np.array([])
    if isinstance(obs, (tuple, list)):
        parts = [np.asarray(v, dtype=np.float64).ravel() for v in obs]
        return np.concatenate(parts) if parts else np.array([])
    return np.asarray(obs, dtype=np.float64).ravel()


class Validator:
    def __init__(self) -> None:
        self.results: list[tuple[str, str, str]] = []  # (name, status, detail)

    def record(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, PASS if ok else FAIL, detail))
        status = PASS if ok else FAIL
        line = f"[{status}] {name}"
        if detail:
            line += f" - {detail}"
        print(line)

    @property
    def failed(self) -> bool:
        return any(status == FAIL for _, status, _ in self.results)


def check_api_compliance(validator: Validator, spec: str) -> None:
    """Run gymnasium's official env checker."""
    try:
        env = make_env(spec)
        # check_env expects the raw environment; unwrap ordering/time-limit
        # wrappers added by gym.make(). Skip the render check so validation
        # works headless (no pygame/display needed) - rendering is irrelevant
        # to training correctness.
        check_env(env.unwrapped, skip_render_check=True)
        env.close()
        validator.record("gymnasium check_env", True)
    except Exception as exc:  # noqa: BLE001 - report any checker failure
        validator.record("gymnasium check_env", False, f"{type(exc).__name__}: {exc}")


def check_spaces_and_step(validator: Validator, env: gym.Env, seed: int) -> None:
    """Reset/step return shapes, space containment, and type checks."""
    try:
        ok = env.observation_space is not None and env.action_space is not None
        validator.record("spaces defined", ok)

        obs, info = env.reset(seed=seed)
        validator.record(
            "reset() returns (obs, info)",
            isinstance(info, dict),
            "" if isinstance(info, dict) else f"info is {type(info).__name__}",
        )
        validator.record(
            "reset() obs in observation_space",
            env.observation_space.contains(obs),
            "" if env.observation_space.contains(obs) else f"obs={obs!r}",
        )

        action = env.action_space.sample()
        result = env.step(action)
        if len(result) != 5:
            validator.record(
                "step() returns 5-tuple", False, f"got {len(result)} values"
            )
            return
        validator.record("step() returns 5-tuple", True)

        obs, reward, terminated, truncated, info = result
        validator.record(
            "step() obs in observation_space", env.observation_space.contains(obs)
        )
        validator.record(
            "reward is numeric",
            isinstance(reward, (int, float, np.integer, np.floating)),
            f"type={type(reward).__name__}",
        )
        validator.record(
            "terminated/truncated are bool",
            isinstance(terminated, (bool, np.bool_))
            and isinstance(truncated, (bool, np.bool_)),
        )
        validator.record("step() info is dict", isinstance(info, dict))
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        validator.record("spaces / step API", False, f"{type(exc).__name__}: {exc}")


def check_random_rollouts(
    validator: Validator, env: gym.Env, episodes: int, max_steps: int, seed: int
) -> None:
    """Random rollouts: reward stats, NaN/Inf guards, episode termination."""
    rewards: list[float] = []
    lengths: list[int] = []
    nan_obs = 0
    nan_reward = 0
    unterminated = 0
    try:
        env.action_space.seed(seed)
        for ep in range(episodes):
            obs, _ = env.reset(seed=seed + ep)
            total = 0.0
            steps = 0
            for _ in range(max_steps):
                obs, reward, terminated, truncated, _ = env.step(
                    env.action_space.sample()
                )
                flat = flatten_obs(obs)
                if flat.size and not np.all(np.isfinite(flat)):
                    nan_obs += 1
                if not np.isfinite(float(reward)):
                    nan_reward += 1
                total += float(reward)
                steps += 1
                if terminated or truncated:
                    break
            else:
                unterminated += 1
            rewards.append(total)
            lengths.append(steps)

        validator.record(
            "no NaN/Inf in observations", nan_obs == 0, f"{nan_obs} bad steps"
        )
        validator.record(
            "no NaN/Inf in rewards", nan_reward == 0, f"{nan_reward} bad steps"
        )
        validator.record(
            f"episodes end within {max_steps} steps",
            unterminated == 0,
            f"{unterminated}/{episodes} episodes never terminated or truncated",
        )
        print(
            f"       random-policy return over {episodes} episodes: "
            f"mean={np.mean(rewards):.2f} std={np.std(rewards):.2f} "
            f"min={np.min(rewards):.2f} max={np.max(rewards):.2f}"
        )
        print(
            f"       episode length: mean={np.mean(lengths):.1f} "
            f"min={np.min(lengths)} max={np.max(lengths)}"
        )
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        validator.record("random rollouts", False, f"{type(exc).__name__}: {exc}")


def check_determinism(
    validator: Validator, env: gym.Env, seed: int, n_actions: int
) -> None:
    """Same seed + same actions must reproduce the same trajectory.

    This is the corrected pattern from references/environments.md: sample the
    action sequence once, then run it twice from ``reset(seed=...)`` and
    compare with ``np.allclose``.
    """
    try:
        env.action_space.seed(seed)
        actions = [env.action_space.sample() for _ in range(n_actions)]

        def rollout() -> list[np.ndarray]:
            obs, _ = env.reset(seed=seed)
            trajectory = [flatten_obs(obs)]
            for action in actions:
                obs, _, terminated, truncated, _ = env.step(action)
                trajectory.append(flatten_obs(obs))
                if terminated or truncated:
                    break
            return trajectory

        traj1 = rollout()
        traj2 = rollout()

        if len(traj1) != len(traj2):
            validator.record(
                "determinism (same seed, same actions)",
                False,
                f"trajectory lengths differ: {len(traj1)} vs {len(traj2)}",
            )
            return
        for i, (a, b) in enumerate(zip(traj1, traj2)):
            if a.shape != b.shape or not np.allclose(a, b):
                validator.record(
                    "determinism (same seed, same actions)",
                    False,
                    f"observations diverge at step {i}",
                )
                return
        validator.record("determinism (same seed, same actions)", True)
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        validator.record("determinism", False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Gymnasium environment before training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "env_spec",
        help="Registered gym id (e.g. CartPole-v1) or module.path:EnvClass",
    )
    parser.add_argument(
        "--episodes", type=int, default=3, help="random-rollout episodes"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10_000,
        help="max steps per episode before flagging a never-ending episode",
    )
    parser.add_argument("--seed", type=int, default=42, help="base seed")
    parser.add_argument(
        "--determinism-actions",
        type=int,
        default=20,
        help="actions replayed in the determinism check",
    )
    args = parser.parse_args()

    validator = Validator()
    print(f"Validating environment: {args.env_spec}\n")

    check_api_compliance(validator, args.env_spec)

    try:
        env = make_env(args.env_spec)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not instantiate environment: {exc}")
        return 1

    try:
        check_spaces_and_step(validator, env, args.seed)
        check_random_rollouts(
            validator, env, args.episodes, args.max_steps, args.seed
        )
        check_determinism(validator, env, args.seed, args.determinism_actions)
    finally:
        env.close()

    n_fail = sum(1 for _, status, _ in validator.results if status == FAIL)
    print(
        f"\n{'All checks passed.' if n_fail == 0 else f'{n_fail} check(s) FAILED.'}"
    )
    return 1 if validator.failed else 0


if __name__ == "__main__":
    sys.exit(main())
