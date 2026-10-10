---
name: reinforcement-learning
description: Reinforcement learning in Python with Gymnasium and Stable-Baselines3 (PPO, SAC, DQN, TD3, A2C). Use when the user is building a custom Gymnasium environment, choosing an algorithm, training or tuning an agent, debugging an agent that won't learn (flat reward, collapse, NaNs), evaluating a policy, or exporting one to ONNX. Includes runnable scripts that validate an environment, sanity-check it before training, and write an evaluation report. Not for RL in C++/libtorch (use cpp-reinforcement-learning), RLHF or LLM post-training (GRPO, DPO), or supervised deep learning (use deep-learning).
---

# Reinforcement learning (Python)

Help the user get an agent that actually learns, and show that it did. Most RL failures come from the environment and the setup (observation scale, reward design, termination flags, evaluation mistakes) rather than from the algorithm, so check those before reaching for exotic fixes.

The ecosystem moves: Gymnasium 1.x replaced OpenAI Gym, and SB3 changes defaults between releases. Before writing code against a specific API, check what the user has installed (`pip show gymnasium stable-baselines3`) and match it. If a web or docs tool is available, look up any API you're unsure of rather than relying on the snippets here. Current as of October 2026: Gymnasium 1.4, Stable-Baselines3 2.9 (Gymnasium 1.x support needs SB3 2.4 or later).

## Choosing a library and algorithm

Stable-Baselines3 is the default here: reliable implementations, good defaults, and the bundled scripts target it. CleanRL suits users who want to read and modify a single-file implementation; TorchRL suits custom research algorithms. For distributed training at scale, Ray RLlib is the usual choice, but this skill doesn't cover it.

| Situation | Start with | Why |
|---|---|---|
| Discrete actions, getting started | PPO | Stable with default settings |
| Discrete actions, environment steps are expensive | DQN | Off-policy, reuses experience |
| Continuous control | SAC (or TD3) | Sample-efficient; SAC tunes its own exploration |
| Image observations | PPO with `CnnPolicy` | Handles pixels well |
| Need fast iterations on a simple task | A2C | Simple, quick updates |

SB3's DQN is the vanilla algorithm; it has no Double or Dueling options. If the user needs those, they need a custom policy or `sb3-contrib` (which has QR-DQN).

## Quick start

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy

train_env = make_vec_env("CartPole-v1", n_envs=4, seed=0)
model = PPO("MlpPolicy", train_env, verbose=1, seed=0)
model.learn(total_timesteps=100_000)
model.save("ppo_cartpole")

eval_env = make_vec_env("CartPole-v1", n_envs=1, seed=123)   # separate env for evaluation
mean, std = evaluate_policy(model, eval_env, n_eval_episodes=20, deterministic=True)
print(f"{mean:.1f} +/- {std:.1f}")
```

## Custom environment template

```python
import gymnasium as gym
import numpy as np
from gymnasium import spaces

class CustomEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self, render_mode=None):
        super().__init__()
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.render_mode = render_mode

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)                      # seeds self.np_random
        self.state = self.np_random.uniform(-0.05, 0.05, size=(4,)).astype(np.float32)
        self.steps = 0
        return self.state, {}

    def step(self, action):
        self.steps += 1
        # update self.state from the action here
        reward = 0.0
        terminated = False                # the task ended (success or failure)
        truncated = self.steps >= 500     # a time limit cut the episode short
        return self.state, reward, terminated, truncated, {}
```

Keep `terminated` and `truncated` distinct: algorithms bootstrap the value of a truncated state but not a terminated one, and mixing them up quietly biases learning. Give every environment a time limit, or evaluation can loop forever.

## The workflow, with the bundled scripts

The scripts live in this skill's `scripts/` folder, which after install is `${CLAUDE_PLUGIN_ROOT}/skills/reinforcement-learning/scripts/`. Run them from the user's project directory so a `module.path:EnvClass` spec such as `src.env:MyEnv` can be imported (the scripts add the current directory to the import path). Each also accepts a registered id such as `CartPole-v1`.

1. **Validate the environment** after creating or changing it: `python3 …/validate_env.py src.env:MyEnv`. It checks Gymnasium API compliance, spaces, NaNs, determinism and termination, and exits nonzero on failure (usable in CI).
2. **Sanity-check before training:** `python3 …/pretrain_check.py src.env:MyEnv`. It reports a random-policy baseline and warns about observation and reward scales, sparse rewards, and termination patterns. The trained agent has to beat this baseline clearly.
3. **Train simply first:** default hyperparameters, a short run, TensorBoard on (`tensorboard_log="runs/"`). Save the VecNormalize statistics alongside the model if you normalize (`env.save("models/vecnormalize.pkl")`).
4. **Debug** with `references/debugging.md` if learning stalls.
5. **Tune** with Optuna once a baseline works (below).
6. **Evaluate:** `python3 …/eval_report.py src.env:MyEnv --model models/best.zip --algo ppo --vecnormalize models/vecnormalize.pkl`. Pass `--vecnormalize` whenever training used VecNormalize: without the statistics the agent sees unnormalized inputs and scores like a random policy, which looks exactly like "it learned nothing". It writes a Markdown report (to `--output`, default `eval_report.md`).
7. **Export** for deployment: `references/deployment.md` (ONNX is the main path).

## Tuning with Optuna

```python
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy

def objective(trial):
    params = {
        "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
        "n_steps": trial.suggest_categorical("n_steps", [256, 512, 1024, 2048]),
        "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
    }
    model = PPO("MlpPolicy", make_vec_env("CartPole-v1", n_envs=4, seed=trial.number), verbose=0, **params)
    model.learn(total_timesteps=50_000)
    # Score on a separate env: scoring on the training env rewards overfitting to it.
    eval_env = make_vec_env("CartPole-v1", n_envs=1, seed=10_000 + trial.number)
    mean_reward, _ = evaluate_policy(model, eval_env, n_eval_episodes=10, deterministic=True)
    return mean_reward

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)
print(study.best_params)
```

If training uses VecNormalize, evaluate with a VecNormalize-wrapped eval env that loads the training statistics with `training=False` and `norm_reward=False`. For pruning of bad trials, see `references/training.md`.

## Pitfalls worth checking first

1. **Observation scale.** Vector observations on very different scales slow or stop learning; wrap with `VecNormalize`. The exception is image observations (uint8 pixels): `CnnPolicy` scales them to [0, 1] itself, and normalizing pixels with running statistics hurts.
2. **Learning rate.** Start from SB3's default for the algorithm (they differ: DQN 1e-4, PPO and SAC 3e-4, TD3 1e-3) and change one thing at a time.
3. **Sparse rewards.** Prefer potential-based shaping, a curriculum, or HER for goal-based tasks. Naive intermediate rewards are a common cause of reward hacking, where the agent maximizes the bonus instead of solving the task.
4. **Evaluating on the training env**, or without the VecNormalize statistics (see step 6).
5. **Seeds.** Set them for reproducibility, and compare algorithms or settings across several seeds; single runs are noisy.
6. **Entropy collapse** in PPO/A2C. SB3 logs `train/entropy_loss`, which is the *negative* of the policy's entropy, so collapse shows as `entropy_loss` rising toward 0.

## Reference files

- `references/algorithms.md`: DQN, PPO, SAC, A2C, TD3 in depth, with SB3 defaults
- `references/environments.md`: Gymnasium setup, custom environments, wrappers, Atari and MuJoCo
- `references/training.md`: hyperparameters, reward design, normalization, callbacks
- `references/debugging.md`: symptoms and fixes for agents that don't learn
- `references/evaluation.md`: metrics, logging, reproducibility
- `references/deployment.md`: ONNX export, `torch.export`, quantization, inference safety

## Installing

```bash
pip install "stable-baselines3[extra]>=2.4" "gymnasium>=1.0" optuna   # [extra] adds TensorBoard, progress bars, Atari wrappers
pip install "gymnasium[atari]"     # Atari: ROMs ship with ale-py now; call gym.register_envs(ale_py) after import ale_py
pip install "gymnasium[mujoco]"    # MuJoCo
```

Use a project virtual environment (`python3 -m venv .venv` or `uv venv`) rather than the system Python.
