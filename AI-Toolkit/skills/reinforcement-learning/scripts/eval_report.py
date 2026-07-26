#!/usr/bin/env python3
"""Comprehensive policy evaluation with a Markdown report.

Implements the corrected evaluation loop from references/evaluation.md:
per-episode success is read from the TERMINAL step's ``info`` dict (one
``is_success`` flag per episode, not per step), and reports mean/std return,
95% confidence interval, success rate, and episode-length statistics.

Evaluates either a trained Stable-Baselines3 model or (without --model) a
random policy - useful as a baseline and for testing the report pipeline.

Usage:
    # Random-policy baseline report
    python eval_report.py CartPole-v1 --episodes 50 --output eval_report.md

    # Trained SB3 model
    python eval_report.py CartPole-v1 --model ppo_cartpole.zip --algo ppo \
        --episodes 100 --output eval_report.md

Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import sys

import numpy as np

try:
    import gymnasium as gym
except ImportError:
    print("ERROR: gymnasium is not installed. Run: pip install gymnasium")
    sys.exit(2)

SB3_ALGOS = ("ppo", "sac", "dqn", "td3", "a2c")


def make_env(spec: str) -> gym.Env:
    """Instantiate the environment from a gym id or 'module:Class' spec."""
    if ":" in spec:
        module_name, class_name = spec.split(":", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)()
    return gym.make(spec)


def load_model(path: str, algo: str):
    """Load a Stable-Baselines3 model of the given algorithm."""
    try:
        import stable_baselines3 as sb3
    except ImportError:
        print(
            "ERROR: stable-baselines3 is not installed but --model was given. "
            "Run: pip install stable-baselines3"
        )
        sys.exit(2)
    algo_class = {
        "ppo": sb3.PPO,
        "sac": sb3.SAC,
        "dqn": sb3.DQN,
        "td3": sb3.TD3,
        "a2c": sb3.A2C,
    }[algo]
    return algo_class.load(path)


def evaluate(
    env: gym.Env,
    model,
    n_episodes: int,
    deterministic: bool,
    seed: int,
) -> dict:
    """Run n_episodes and compute metrics.

    Success is tracked once per episode, from the info dict of the TERMINAL
    step - the pattern documented in references/evaluation.md. Counting
    'is_success' on every step double-counts and inflates the rate.
    """
    episode_rewards: list[float] = []
    episode_lengths: list[int] = []
    success_count = 0
    success_defined = False

    env.action_space.seed(seed)
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        episode_reward = 0.0
        episode_length = 0
        done = False
        info: dict = {}

        while not done:
            if model is not None:
                action, _ = model.predict(obs, deterministic=deterministic)
            else:
                action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += float(reward)
            episode_length += 1
            done = terminated or truncated

        # Success flag comes from the terminal step's info (one per episode)
        if "is_success" in info:
            success_defined = True
            if info["is_success"]:
                success_count += 1

        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)

    rewards = np.array(episode_rewards)
    lengths = np.array(episode_lengths)

    metrics = {
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "min_reward": float(np.min(rewards)),
        "max_reward": float(np.max(rewards)),
        "median_reward": float(np.median(rewards)),
        "mean_length": float(np.mean(lengths)),
        "std_length": float(np.std(lengths)),
        "min_length": int(np.min(lengths)),
        "max_length": int(np.max(lengths)),
        "success_rate": (success_count / n_episodes) if success_defined else None,
        "n_episodes": n_episodes,
    }
    ci = 1.96 * metrics["std_reward"] / np.sqrt(n_episodes)
    metrics["ci_95"] = float(ci)
    metrics["ci_lower"] = metrics["mean_reward"] - ci
    metrics["ci_upper"] = metrics["mean_reward"] + ci
    return metrics


def render_report(
    metrics: dict,
    env_spec: str,
    policy_desc: str,
    deterministic: bool,
    seed: int,
) -> str:
    success_row = (
        f"| Success Rate | {metrics['success_rate']:.2%} |\n"
        if metrics["success_rate"] is not None
        else "| Success Rate | n/a (env does not report `is_success`) |\n"
    )
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    return f"""# RL Evaluation Report

## Summary

- **Environment**: {env_spec}
- **Policy**: {policy_desc}
- **Episodes**: {metrics['n_episodes']}
- **Deterministic actions**: {deterministic}
- **Base seed**: {seed}
- **Generated**: {timestamp}

## Performance Metrics

| Metric | Value |
|--------|-------|
| Mean Reward | {metrics['mean_reward']:.2f} |
| Std Reward | {metrics['std_reward']:.2f} |
| 95% CI | [{metrics['ci_lower']:.2f}, {metrics['ci_upper']:.2f}] |
| Min Reward | {metrics['min_reward']:.2f} |
| Max Reward | {metrics['max_reward']:.2f} |
| Median Reward | {metrics['median_reward']:.2f} |
{success_row}| Mean Episode Length | {metrics['mean_length']:.1f} |
| Std Episode Length | {metrics['std_length']:.1f} |
| Min/Max Episode Length | {metrics['min_length']} / {metrics['max_length']} |

## Interpretation

The policy achieves a mean episodic return of **{metrics['mean_reward']:.2f}**
(std {metrics['std_reward']:.2f}) over {metrics['n_episodes']} episodes. The
95% confidence interval for the true mean is
[{metrics['ci_lower']:.2f}, {metrics['ci_upper']:.2f}].

## Notes

- Success is counted once per episode, from the terminal step's `info` dict
  (`is_success`), never per step.
- Every episode ran to completion (terminated or truncated).
- Compare against the random-policy baseline from `pretrain_check.py` to
  confirm the agent actually learned.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a policy and write a Markdown report.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "env_spec",
        help="Registered gym id (e.g. CartPole-v1) or module.path:EnvClass",
    )
    parser.add_argument(
        "--model", default=None, help="path to an SB3 model .zip (omit for random policy)"
    )
    parser.add_argument(
        "--algo",
        default="ppo",
        choices=SB3_ALGOS,
        help="SB3 algorithm class used to load --model",
    )
    parser.add_argument("--episodes", type=int, default=100, help="eval episodes")
    parser.add_argument("--seed", type=int, default=42, help="base seed")
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="sample stochastic actions instead of deterministic ones",
    )
    parser.add_argument(
        "--output", default="eval_report.md", help="Markdown report output path"
    )
    args = parser.parse_args()

    deterministic = not args.stochastic
    model = None
    policy_desc = "random policy (no model provided)"
    if args.model:
        model = load_model(args.model, args.algo)
        policy_desc = f"{args.algo.upper()} model from {args.model}"

    try:
        env = make_env(args.env_spec)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not instantiate environment: {exc}")
        return 1

    try:
        metrics = evaluate(env, model, args.episodes, deterministic, args.seed)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: evaluation failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        env.close()

    print(
        f"Mean reward: {metrics['mean_reward']:.2f} +/- {metrics['std_reward']:.2f} "
        f"(95% CI [{metrics['ci_lower']:.2f}, {metrics['ci_upper']:.2f}])"
    )
    if metrics["success_rate"] is not None:
        print(f"Success rate: {metrics['success_rate']:.2%}")
    print(
        f"Episode length: {metrics['mean_length']:.1f} +/- {metrics['std_length']:.1f}"
    )

    report = render_report(
        metrics, args.env_spec, policy_desc, deterministic, args.seed
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
