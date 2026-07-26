# AI-Toolkit

Skills for Deep Learning, Reinforcement Learning (Python & C++), Prompt Engineering, Web3 Payments, and OpenClaw Setup — plus slash commands and agents that operationalize them.

## Installation

```bash
/plugin install ai-toolkit@zAI-Skills
```

## Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/optimize-prompt` | `[prompt file path or pasted prompt]` | Diagnose and rewrite a prompt using the prompt-optimizer skill's workflow — before/after diff, parameter recommendations (model, effort, thinking), per-change rationale, and an offer to A/B-measure the result |
| `/rl-new-project` | `[environment or task description]` | Scaffold a Python RL project: custom Gymnasium (>=1.0) env, SB3 training script with EvalCallback + VecNormalize, Optuna tuning stub, and the RL skill's validation scripts wired into a Makefile |
| `/x402-scaffold` | `[seller \| buyer] [evm \| svm]` | Generate an x402 payment starter — seller (paid endpoint with the 402 flow) or buyer (paying client) — with testnet-only defaults; mainnet keys/config are always the user's explicit opt-in |
| `/openclaw-audit` | *(none — audits the local install)* | Run the openclaw-setup skill's security checklist: version (CVE-2026-25253), gateway binding, auth, DM policy, file permissions, and more — pass/fail table with remediations |

## Agents

| Agent | Model | Description |
|-------|-------|-------------|
| `rl-debugger` | sonnet | Diagnoses RL training failures using the debugging playbook — pre-training sanity checks via the skill's validation scripts, entropy/value-loss diagnostics, and the common failure-mode tables (flat reward, policy collapse, high variance, NaN) |
| `prompt-rewriter` | opus | Rewrites a target prompt in an isolated context, applying the prompt-optimizer references end-to-end: symptom diagnosis, core-principle checks, proven snippets, and parameter recommendations |

## Skills

### deep-learning

Comprehensive guide for Deep Learning with Keras 3 (Multi-Backend: JAX, TensorFlow, PyTorch). Use when:
- Building neural networks (Sequential, Functional, Subclassing APIs)
- Working with CNNs for computer vision
- Implementing RNNs/Transformers for NLP
- Time series forecasting
- Generative models (VAEs, GANs)
- Custom training loops and callbacks

**Reference Materials:**
- Keras 3 migration notes
- Computer vision patterns
- NLP & Transformer architectures
- Time series techniques
- Generative deep learning
- Best practices for production

**Utility Scripts:**
- `quick_train.py` - Reusable training template
- `visualize_filters.py` - Convnet filter visualization

### reinforcement-learning

Reinforcement Learning best practices for Python using modern libraries (Stable-Baselines3, RLlib, Gymnasium). Use when:
- Implementing RL algorithms (PPO, SAC, DQN, TD3, A2C)
- Creating custom Gymnasium environments
- Training, debugging, or evaluating RL agents
- Setting up hyperparameter tuning for RL
- Deploying RL models to production

**Reference Materials:**
- Algorithm implementations (PPO, SAC, DQN, TD3, A2C)
- Custom environment creation
- Training and debugging patterns
- Evaluation and benchmarking
- Production deployment

### cpp-reinforcement-learning

C++ Reinforcement Learning using libtorch (PyTorch C++ frontend) and modern C++17/20. Use when:
- Implementing RL algorithms in C++ for performance-critical applications
- Building production RL systems with libtorch
- Creating replay buffers and experience storage
- Optimizing RL training with GPU acceleration
- Deploying RL models with ONNX Runtime

**Reference Materials:**
- Algorithm implementations with libtorch
- Memory management patterns
- Performance optimization
- Testing strategies

### prompt-optimizer

Optimize prompts for Claude's latest models using Anthropic's official best practices. Use when:
- Improving or creating effective prompts for Claude
- Fixing underperforming prompts or reducing verbosity
- Creating system prompts or controlling output formatting
- Enhancing agentic and tool-use behaviors

**Reference Materials:**
- Prompt patterns and techniques
- Agentic prompt design
- Output formatting controls

### x402-payments

Build applications using the x402 protocol — Coinbase's open standard for HTTP-native stablecoin payments using the HTTP 402 status code. Use when:
- Creating APIs that require USDC payments per request (seller/server side)
- Building clients or AI agents that pay for x402-protected resources (buyer/client side)
- Implementing MCP servers with paid tools for Claude Desktop
- Adding payment middleware to Express, Hono, or Next.js applications
- Working with Base (EVM) or Solana (SVM) payment flows
- Building machine-to-machine or agent-to-agent payment systems

**Reference Materials:**
- Protocol specification (headers, payloads, CAIP-2 IDs)
- Server patterns (Express, Hono, Next.js middleware)
- Client patterns (fetch, axios, wallet setup)
- Agentic patterns (AI agent payments, MCP server integration)
- Deployment guide (testnet to mainnet migration)

### openclaw-setup

Set up, configure, secure, and deploy OpenClaw — the open-source personal AI assistant that connects to your messaging channels. Use when:
- Installing OpenClaw from scratch on macOS or Linux
- Configuring Anthropic auth, model selection, and cost controls
- Connecting messaging channels (Telegram, iMessage)
- Applying security hardening and safe defaults
- Deploying to a Hostinger VPS with Docker
- Running health checks (`openclaw doctor`, `openclaw security audit`)

**Reference Materials:**
- Mac mini local deployment walkthrough
- Hostinger VPS Docker deployment guide
- Anthropic auth, cost control, and smart model routing
- Telegram and iMessage channel setup
- Security defaults, hardening, and incident response

## License

MIT
