---
description: Scaffold a Python RL project — custom Gymnasium environment, Stable-Baselines3 training with evaluation and VecNormalize, an Optuna tuning stub, and Makefile targets that validate the environment before training
argument-hint: "[what the agent should learn, e.g. 'inventory restocking, discrete actions']"
---
Scaffold a new Python reinforcement-learning project with the reinforcement-learning skill bundled with this plugin.

## What the user wants the agent to learn

$ARGUMENTS

If that's empty, ask one question: what should the agent learn, roughly what it observes, what it can do, and what success looks like. In the same message, offer to scaffold a worked example right away (a small grid-world "reach the goal" environment) so they can see the pieces run first. If they pick the example, go ahead without further questions.

If the description is thin, fill the gaps with sensible choices, mark them with `TODO`, and say what you assumed rather than asking a series of questions.

## Get the guidance

Read `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/SKILL.md`. Consult `references/environments.md` (environment template and checks), `references/algorithms.md` (for the algorithm choice) and `references/training.md` (starting hyperparameters, reward design) under `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/` as needed.

Choose the algorithm from the skill's table: action-space type first, then whether environment steps are expensive. Default to PPO when nothing points elsewhere, since it's the most forgiving. Say which you chose and why in one or two sentences.

## Create the project

Create it in a new subfolder named after the task (kebab-case), unless the user asked for the current directory. If the target folder exists and isn't empty, ask before writing.

```
<task-name>/
├── requirements.txt     stable-baselines3[extra]>=2.4, gymnasium>=1.0, optuna
├── .gitignore           .venv/, models/, runs/, __pycache__/
├── Makefile
├── README.md            what each target does, first-run order
├── src/
│   ├── __init__.py
│   ├── env.py           the custom Gymnasium environment
│   ├── train.py         training entry point
│   └── tune.py          Optuna stub
├── scripts/             copies of the skill's validate_env.py, pretrain_check.py, eval_report.py
└── models/              checkpoints and VecNormalize statistics (gitignored)
```

What goes in each:

- **`src/env.py`:** follow the skill's custom environment template exactly: `reset(seed=None, options=None)` calls `super().reset(seed=seed)` and returns `(obs, info)`; `step` returns `(obs, reward, terminated, truncated, info)` with terminated and truncated kept distinct; explicit spaces; a step limit so episodes always end. Put `info["is_success"]` on the final step if the task has a success condition. Fill in plausible dynamics and rewards, with `TODO` where the user must supply real logic.
- **`src/train.py`:** `make_vec_env` with 4 or more envs, `VecNormalize` on the training env (skip observation normalization for image observations, as the skill explains), an `EvalCallback` on a separate eval env that is also VecNormalize-wrapped with `training=False` and `norm_reward=False` and kept in sync with the training statistics, TensorBoard logging to `runs/`, a fixed seed, and the model plus `models/vecnormalize.pkl` saved at the end.
- **`src/tune.py`:** the skill's Optuna example adapted to the chosen algorithm, scoring on a separate eval env.
- **`scripts/`:** copy the three scripts from `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/` rather than writing new ones; they're tested.
- **`Makefile`:** run everything from the project root with `PYTHONPATH=.` so `src.env:<Class>` imports, and through the project venv:
  - `install`: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
  - `check-env`: `.venv/bin/python scripts/validate_env.py src.env:<Class>`
  - `sanity`: `.venv/bin/python scripts/pretrain_check.py src.env:<Class>`
  - `train`, `tune`, `tensorboard`
  - `eval`: `.venv/bin/python scripts/eval_report.py src.env:<Class> --model models/best_model.zip --algo <algo> --vecnormalize models/vecnormalize.pkl`

  Use a `justfile` instead only if the user asks or the repo already uses one.

## Check it

If Python 3 is available, run `make install`, `make check-env` and `make sanity`, and fix whatever fails, so the user starts from a project whose environment passes its own checks. Don't run `make train` yourself unless the user asks; training takes their time and compute.

## Hand off

Tell the user:

1. The algorithm and why.
2. The run order: `make train`, watch `make tensorboard`, then `make eval` (the setup checks already passed, or here's what's left).
3. The `TODO`s in `src/env.py` they need to fill in.
4. Where to look if it doesn't learn: `references/training.md` for reward design and hyperparameters, and the rl-debugger agent for diagnosis.
