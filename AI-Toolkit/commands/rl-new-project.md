---
description: Scaffold a Python RL project — custom Gymnasium env, SB3 training script with EvalCallback + VecNormalize, Optuna tuning stub, and validation targets in a Makefile
argument-hint: "[environment or task description]"
---
You are scaffolding a new Python reinforcement learning project using the reinforcement-learning skill.

## Arguments

$ARGUMENTS

The arguments describe the environment or task (e.g. "inventory management with discrete restock actions", "2D drone hover, continuous thrust"). If no arguments were given, ask the user what they want the agent to learn — specifically the observation the agent sees, the actions it can take (discrete or continuous), and what success looks like — before scaffolding anything.

## Step 1: Load the skill

Read `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/SKILL.md` first. Then read:

- `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/references/environments.md` — custom env template, validation checklist, wrappers, and the environment testing script.
- `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/references/algorithms.md` — algorithm deep-dives, for justifying the algorithm choice.
- `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/references/training.md` — hyperparameter starting points, reward engineering, normalization.
- `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/references/debugging.md` — the pre-training sanity checklist to turn into a validation script.

## Step 2: Choose the algorithm

Apply the SKILL.md Algorithm Decision Tree to the task description: action space type first (discrete vs. continuous), then sample-efficiency and stability requirements. State the chosen algorithm and cite the decision-tree branch and the relevant section of `references/algorithms.md` that justifies it. Default to PPO when the task description leaves the tradeoffs ambiguous — it is the stable choice per the skill's quick-selection table.

## Step 3: Generate the project

Create this layout in the current directory (ask before writing if the directory is not empty):

```
<project>/
├── pyproject.toml            # or requirements.txt — gymnasium>=1.0, stable-baselines3>=2.0, tensorboard, optuna
├── Makefile
├── src/
│   ├── __init__.py
│   ├── env.py                # custom Gymnasium environment
│   ├── train.py              # SB3 training entry point
│   └── tune.py               # Optuna tuning stub
├── scripts/
│   ├── check_env.py          # Gymnasium API validation
│   └── sanity_checks.py      # pre-training sanity checklist
└── models/                   # checkpoints + VecNormalize stats (gitignored)
```

Content requirements:

1. **`src/env.py`** — a custom env following the Gymnasium >= 1.0 API exactly as shown in the skill's Custom Environment Template: `reset(self, seed=None, options=None)` returning `(obs, info)` and calling `super().reset(seed=seed)`; `step` returning the 5-tuple `(obs, reward, terminated, truncated, info)` with terminated/truncated kept distinct; explicit `observation_space` and `action_space` matching the user's task; `metadata` with render modes. Fill in plausible dynamics and rewards from the task description, marked with `TODO` comments where the user must supply real logic.
2. **`src/train.py`** — SB3 training script with:
   - `make_vec_env` with 4+ parallel envs,
   - `VecNormalize` wrapping the training env (per the skill's pitfall #1: always normalize observations),
   - an `EvalCallback` using a **separate** eval env (pitfall #4), with the eval env also VecNormalize-wrapped sharing the training statistics (`training=False`, `norm_reward=False`) and stats synced before evaluation,
   - `VecNormalize` statistics saved alongside the model checkpoint — a model saved without its normalization stats is unusable,
   - TensorBoard logging and seed handling (pitfall #3).
3. **`src/tune.py`** — Optuna stub following the skill's Hyperparameter Tuning example: an `objective(trial)` suggesting learning rate (log scale), n_steps/batch size, and gamma for the chosen algorithm, short training budget, `evaluate_policy` scoring, and a `study.optimize` entry point.
4. **`scripts/check_env.py`** — instantiate the custom env and run `gymnasium.utils.env_checker.check_env` on it, plus the space/reset/step assertions from the Environment Validation Checklist in `references/environments.md`.
5. **`scripts/sanity_checks.py`** — the pre-training checklist from `references/debugging.md` adapted to this project: environment validation, random-policy baseline reward, observation statistics (warn if `|obs| > 100`), reward statistics (warn on very sparse rewards), action-space report, and a model forward pass.
   - If `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/` exists (check with Glob or `ls`), copy its validation scripts into the project's `scripts/` dir and wire those instead of writing your own adaptations.
6. **`Makefile`** — targets wiring it all together: `install`, `check-env` (runs `scripts/check_env.py`), `sanity` (runs `scripts/sanity_checks.py`), `train`, `tune`, `tensorboard`, and `eval`. Use a `justfile` instead only if the user asks or the repo already uses one.

## Step 4: Hand off

After scaffolding, tell the user:

1. The chosen algorithm and why (decision-tree citation).
2. The recommended first run order: `make install` → `make check-env` → `make sanity` → `make train` — do not skip the validation targets; they catch most failures before any compute is spent.
3. The `TODO` markers in `env.py` they must fill in (dynamics, reward).
4. That reward shaping and hyperparameter guidance lives in `references/training.md`, and if training misbehaves, the rl-debugger agent encodes the debugging playbook.
