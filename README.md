# zAI-Skills

A Claude Code plugin marketplace with three plugins.

## Installation

### Via [skills.sh](https://skills.sh)

```bash
npx skills add Aznatkoiny/zAI-Skills
```

### Via Claude Code

```bash
# Add the marketplace
/plugin marketplace add Aznatkoiny/zAI-Skills

# Install any or all plugins
/plugin install AI-Toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
/plugin install real-estate-investment@zAI-Skills
```

Then restart Claude Code.

---

## Plugins

### [AI-Toolkit](AI-Toolkit/)

Skills for building AI/ML systems and optimizing prompts.

| Skill | Description |
|-------|-------------|
| **deep-learning** | Keras 3 (JAX/TF/PyTorch) — CNNs, RNNs, Transformers, GANs, custom training loops |
| **reinforcement-learning** | Python RL with Stable-Baselines3, RLlib, Gymnasium (PPO, SAC, DQN, TD3, A2C) |
| **cpp-reinforcement-learning** | C++ RL with libtorch and modern C++17/20 for performance-critical applications |
| **prompt-optimizer** | Optimize prompts for Claude 4.x using Anthropic's official best practices |
| **x402-payments** | Build x402 protocol apps — HTTP-native USDC payments on Base (EVM) and Solana (SVM) |
| **openclaw-setup** | Set up and configure OpenClaw with Anthropic auth, messaging channels, and VPS deployment |

### [consulting-toolkit](consulting-toolkit/)

Multi-agent consulting system replicating top-tier strategy engagement structure.

| Component | Details |
|-----------|---------|
| **Agents** | Engagement Manager, Research Analyst, Financial Modeler, Deck Builder, Due Diligence |
| **Commands** | 15 slash commands across Research, Structured Thinking, Deliverables, and Engagement Management |
| **Skill** | Consulting frameworks — MECE, Pyramid Principle, Porter's Five Forces, TAM/SAM/SOM, and more |
| **MCP Server** | Financial Intelligence — 7 tools for SEC EDGAR, FRED, and Yahoo Finance data |

### [real-estate-investment](real-estate-investment/)

End-to-end real estate investment analysis — from deal screening through financial modeling to investor-ready reports. Covers all property types with live data integrations.

| Component | Details |
|-----------|---------|
| **Skill** | Core analysis hub with 5 reference files — financial metrics (12 metrics with Python/Excel), advanced analysis (Monte Carlo, sensitivity, waterfalls), property types (BRRRR, commercial, STR, land), market data (6 API integrations), tax strategy (depreciation, 1031, cost seg, 2025-2026 law) |
| **Agents** | Deal Analyzer (autonomous pro forma + sensitivity), Market Researcher (API-driven market scoring), Tax Optimizer (depreciation, cost seg, 1031, entity structure), Portfolio Reviewer (multi-property assessment) |
| **Commands** | `/analyze-deal` `/compare-markets` `/pro-forma` `/brrrr` `/waterfall` `/str-revenue` |
| **MCP Server** | 11 tools across 6 APIs — Census Bureau, Redfin, Rentcast (free tier), Mashvisor, AirDNA, ATTOM |
| **Output Styles** | Investor Report (formal memo), Quick Screen (rapid deal screening) |
| **Hooks** | Tax disclaimer on write operations |

---

## Local Development

```bash
# Add local marketplace
/plugin marketplace add /path/to/this/repo

# Install from local
/plugin install AI-Toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
/plugin install real-estate-investment@zAI-Skills
```

## License

MIT
