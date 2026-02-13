# AI-Toolkit

Skills for Deep Learning, Reinforcement Learning, Prompt Engineering, and Web3 Payments.

## Installation

```bash
/plugin install AI-Toolkit@zAI-Skills
```

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

Optimize prompts for Claude 4.x models using Anthropic's official best practices. Use when:
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

## License

MIT
