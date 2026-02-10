# zAI-Skills

A Claude Code plugin marketplace with two plugins:

- **AI-Toolkit** — Skills for Deep Learning, Reinforcement Learning, Prompt Engineering, and Web3 Payments
- **consulting-toolkit** — Multi-agent consulting system with 5 agents, 15 slash commands, strategy frameworks, and a Financial Intelligence MCP server

## Installation

### Via [skills.sh](https://skills.sh)

```bash
npx skills add Aznatkoiny/zAI-Skills
```

### Via Claude Code

```bash
# Add the marketplace
/plugin marketplace add Aznatkoiny/zAI-Skills

# Install either or both plugins
/plugin install AI-Toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
```

Then restart Claude Code.

---

## AI-Toolkit

### Skills

#### deep-learning

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

#### reinforcement-learning

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

#### cpp-reinforcement-learning

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

#### prompt-optimizer

Optimize prompts for Claude 4.x models using Anthropic's official best practices. Use when:
- Improving or creating effective prompts for Claude
- Fixing underperforming prompts or reducing verbosity
- Creating system prompts or controlling output formatting
- Enhancing agentic and tool-use behaviors

**Reference Materials:**
- Prompt patterns and techniques
- Agentic prompt design
- Output formatting controls

#### x402-payments

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

### Projects

Example applications built using the deep-learning skill:

| Project | Description |
|---------|-------------|
| [stock_predictor](projects/stock_predictor/) | LSTM-based stock price forecasting with technical indicators |

---

## consulting-toolkit

Multi-agent consulting system with an Engagement Manager orchestrating Research, Finance, Deck, and Due Diligence agents. Includes 15 consulting slash commands, strategy frameworks, and a Financial Intelligence MCP server.

### Agents

| Agent | Role |
|-------|------|
| **Engagement Manager** | Orchestrator and quality gate — decomposes briefs into MECE workstreams, delegates to specialists, synthesizes outputs |
| **Research Analyst** | Market research, competitive intelligence, company profiling with rigorous source tracking |
| **Financial Modeler** | Builds Excel models (NPV/IRR/ROI) with 5-sheet architecture and sensitivity analysis |
| **Deck Builder** | Converts analysis into Pyramid Principle storylines and client-ready PowerPoint decks |
| **Due Diligence** | Systematic commercial, financial, and operational investigation with red flag detection |

### Slash Commands

**Research**

| Command | Description |
|---------|-------------|
| `/market-size` | Structured market sizing with top-down and bottom-up approaches (TAM/SAM/SOM) |
| `/competitive-landscape` | Competitive arena mapping with player profiles, positioning map, and Porter's Five Forces |
| `/company-profile` | One-page company profile covering business model, competitive position, and key risks |

**Structured Thinking**

| Command | Description |
|---------|-------------|
| `/issue-tree` | MECE decomposition of a business problem into testable sub-questions |
| `/hypothesis` | Generate 3-5 testable hypotheses with supporting/refuting evidence and kill criteria |
| `/so-what` | Extract strategic implications from raw analysis (DATA → SO WHAT → NOW WHAT) |
| `/size-the-prize` | Estimate the financial impact of an opportunity with risk adjustment and sensitivity |

**Deliverables**

| Command | Description |
|---------|-------------|
| `/storyline` | Create a Pyramid Principle slide storyline with governing thought and action titles |
| `/exec-summary` | Write an SCR (Situation-Complication-Resolution) executive summary |
| `/steerco-update` | Generate a steering committee status update with RAG rating and decisions needed |

**Engagement Management**

| Command | Description |
|---------|-------------|
| `/workplan` | Decompose an objective into MECE workstreams with owners, dependencies, and critical path |
| `/business-case` | Full business case with strategic rationale, options analysis, financial model, and risks |
| `/raci` | Generate a RACI matrix with validation (exactly one Accountable per activity) |
| `/risk-log` | Create or update a risk register with likelihood × impact matrix and mitigation plans |
| `/benchmark` | Benchmarking analysis with peer set rationale, gap analysis, and actionable insights |

### Consulting Frameworks Skill

Procedural guidance on applying standard consulting frameworks, organized by domain:

- **Structuring** — MECE decomposition, Issue Trees, Hypothesis-Driven Analysis
- **Communication** — Pyramid Principle, SCR Framework, Action Titles
- **Strategy** — Porter's Five Forces, TAM/SAM/SOM, Value Chain Analysis, 3 Horizons, Ansoff Matrix
- **Financial** — NPV/IRR, Build/Buy/Partner, Zero-Based Budgeting, Should-Cost Model
- **Operational** — RACI Matrix, Operating Model Canvas, Spans & Layers, Lean/Six Sigma

### Financial Intelligence MCP Server

A TypeScript MCP server providing real-time financial data from SEC EDGAR, FRED, and Yahoo Finance.

| Tool | Source | Purpose |
|------|--------|---------|
| `fin_get_company_financials` | SEC EDGAR | Revenue, EBITDA, margins, growth rates |
| `fin_get_filing_text` | SEC EDGAR | Full 10-K, 10-Q, 8-K filing text |
| `fin_get_stock_data` | Yahoo Finance | Price history, market cap, P/E, key stats |
| `fin_get_macro_indicators` | FRED | GDP, CPI, interest rates, unemployment |
| `fin_get_earnings_transcript` | SEC EDGAR | Earnings-related filings (8-K) |
| `fin_compare_companies` | SEC EDGAR | Side-by-side comparison of 2-5 companies |
| `fin_get_industry_benchmarks` | SEC EDGAR | Median/mean/quartile metrics by SIC code |

Requires `FRED_API_KEY` and `EDGAR_USER_AGENT` environment variables.

---

## Local Development

To test locally:

```bash
# Add local marketplace
/plugin marketplace add /path/to/this/repo

# Install from local
/plugin install AI-Toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
```

## License

MIT
