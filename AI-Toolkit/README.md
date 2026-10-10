# ai-toolkit

For developers who work on AI systems: writing prompts for Claude, training neural networks and reinforcement-learning agents, building pay-per-request APIs with x402, or running their own OpenClaw assistant. Six skills that Claude loads automatically when your request matches, plus four slash commands and two agents.

## Install

```
/plugin marketplace add Aznatkoiny/zAI-Skills
/plugin install ai-toolkit@zAI-Skills
```

Restart Claude Code after installing.

## Try it

| If you want to… | Try |
|---|---|
| Improve a prompt, system prompt, skill or CLAUDE.md | `/optimize-prompt ./prompts/support_bot.md`, or ask "why does my agent stop halfway through tasks?" |
| Start an RL project | `/rl-new-project inventory restocking with discrete actions` (or no arguments for a worked example) |
| Fix an agent that won't learn | "My PPO reward has been flat for 500k steps", and Claude hands it to the rl-debugger agent |
| Build a Keras model | "Build a Keras image classifier for my folder of cat and dog photos" |
| Charge for an API per request | `/x402-scaffold seller evm`, then `npm start` |
| Set up or check OpenClaw | "Help me install OpenClaw on my Mac mini", or `/openclaw-audit` for a read-only security check |

## What it needs

Nothing to use the prompt skill. The others need the tools for that kind of work:

| Area | Required | Optional |
|---|---|---|
| Prompt engineering | — | — |
| Reinforcement learning (Python) | Python 3.10+, `stable-baselines3>=2.4`, `gymnasium>=1.0` (the skill and `/rl-new-project` set these up in a project venv) | Optuna, TensorBoard, Atari or MuJoCo extras |
| Reinforcement learning (C++) | A C++20 compiler, CMake, LibTorch | CUDA, ONNX Runtime |
| Deep learning | Python, Keras 3 and one backend (JAX, TensorFlow or PyTorch) | A GPU |
| x402 payments | Node.js 22+ and a testnet wallet address (free test USDC from faucet.circle.com) | A CDP API key, only when you move to mainnet |
| OpenClaw | A Mac or a Linux VPS, and an Anthropic API key with a spend limit | Telegram bot token, an iMessage-capable Mac |

## Skills

| Skill | Use it for |
|---|---|
| `prompt-engineer` | Writing, reviewing, debugging and migrating prompts for current Claude models (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5), built on Anthropic's prompting docs. Includes the docs as references and a set of evaluation prompts. |
| `reinforcement-learning` | Python RL with Gymnasium and Stable-Baselines3: environments, algorithm choice, training, debugging, evaluation, ONNX export. Ships three scripts: `validate_env.py`, `pretrain_check.py` and `eval_report.py`. |
| `cpp-reinforcement-learning` | RL in C++ with LibTorch: DQN, PPO and SAC implementations, replay and rollout buffers, GPU memory, running Python-trained policies from C++. |
| `deep-learning` | Keras 3 on any backend: vision, text, time series, generative models, custom training, mixed precision, multi-GPU. |
| `x402-payments` | HTTP 402 stablecoin payments: paid endpoints, paying clients and agents with spending limits, MCP tools, testnet to mainnet. |
| `openclaw-setup` | Installing, securing and troubleshooting OpenClaw on a Mac or VPS, with Anthropic setup, Telegram and iMessage. |

## Commands

| Command | Does |
|---|---|
| `/optimize-prompt [file, pasted prompt, or description]` | Reviews and rewrites a prompt, or drafts one from a description: the improved prompt, a diff, what changed and why, API settings when relevant, and how to test it. |
| `/rl-new-project [what the agent should learn]` | Scaffolds a project: custom environment, SB3 training with evaluation and VecNormalize, Optuna stub, the validation scripts, and a Makefile. Runs the environment checks before handing over. |
| `/x402-scaffold [seller\|buyer] [evm\|svm]` | Generates a testnet starter (defaults to seller on EVM), installs it, and checks that it builds. |
| `/openclaw-audit [config path or compose dir]` | Read-only security check of an OpenClaw install, native or Docker, with a pass/fail table. Never prints secrets or changes anything without asking. |

## Agents

Claude delegates to these on its own when a request fits. Both use whatever model your session runs.

| Agent | Does |
|---|---|
| `rl-debugger` | Works out why an RL run isn't learning: reads code and logs, runs the validation scripts, and returns the likely cause with evidence and ordered fixes. |
| `prompt-rewriter` | Rewrites one long or high-stakes prompt in a clean context. |

## License

MIT
