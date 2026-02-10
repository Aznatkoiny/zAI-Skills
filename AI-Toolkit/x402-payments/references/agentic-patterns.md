# Agentic Payment Patterns

## Table of Contents

1. [MCP Server for Claude Desktop](#mcp-server-for-claude-desktop)
2. [Anthropic Tool-Use Agent](#anthropic-tool-use-agent)
3. [Bazaar Discovery Agent](#bazaar-discovery-agent)
4. [Budget-Controlled Agent Wallet](#budget-controlled-agent-wallet)
5. [Multi-Agent Payment Orchestration](#multi-agent-payment-orchestration)

## MCP Server for Claude Desktop

Source: `examples/typescript/clients/mcp/`

Build an MCP (Model Context Protocol) server that wraps x402-protected APIs as tools for Claude Desktop.

```bash
npm install @modelcontextprotocol/sdk @x402/axios @x402/core @x402/evm @x402/svm viem @solana/kit @scure/base axios
```

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios from "axios";
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { registerExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

const EVM_PRIVATE_KEY = process.env.EVM_PRIVATE_KEY as `0x${string}`;
const SVM_PRIVATE_KEY = process.env.SVM_PRIVATE_KEY!;
const RESOURCE_SERVER_URL = process.env.RESOURCE_SERVER_URL || "http://localhost:4021";

// Create x402 client with payment schemes
const client = new x402Client();

// Register EVM scheme
const evmSigner = privateKeyToAccount(EVM_PRIVATE_KEY);
registerExactEvmScheme(client, { signer: evmSigner });

// Register SVM scheme (optional — omit if EVM only)
const svmSigner = await createKeyPairSignerFromBytes(base58.decode(SVM_PRIVATE_KEY));
registerExactSvmScheme(client, { signer: svmSigner });

// Create Axios instance with payment handling
const api = wrapAxiosWithPayment(
  axios.create({ baseURL: RESOURCE_SERVER_URL }),
  client,
);

// Define MCP server with tools
const mcpServer = new McpServer({
  name: "x402-weather",
  version: "1.0.0",
});

mcpServer.tool("get_weather", "Get weather (costs $0.001 USDC)", {}, async () => {
  const response = await api.get("/weather");
  return {
    content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }],
  };
});

mcpServer.tool(
  "get_forecast",
  "Get 5-day forecast (costs $0.01 USDC)",
  { city: { type: "string", description: "City name" } },
  async ({ city }) => {
    const response = await api.get(`/forecast?city=${encodeURIComponent(city)}`);
    return {
      content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }],
    };
  },
);

// Start stdio transport
const transport = new StdioServerTransport();
await mcpServer.connect(transport);
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/claude/claude_desktop_config.json` (Linux):

```json
{
  "mcpServers": {
    "x402-weather": {
      "command": "node",
      "args": ["--experimental-modules", "/path/to/mcp-server.js"],
      "env": {
        "EVM_PRIVATE_KEY": "0x...",
        "SVM_PRIVATE_KEY": "...",
        "RESOURCE_SERVER_URL": "http://localhost:4021"
      }
    }
  }
}
```

## Anthropic Tool-Use Agent

Build an AI agent that autonomously decides when to call paid APIs using Anthropic's tool-use.

```bash
npm install @anthropic-ai/sdk @x402/fetch @x402/core @x402/evm viem
```

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

// Set up x402 payment client
const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const x402 = new x402Client();
registerExactEvmScheme(x402, { signer });
const fetchWithPayment = wrapFetchWithPayment(fetch, x402);

// Define tools for the agent
const tools: Anthropic.Messages.Tool[] = [
  {
    name: "get_weather",
    description: "Get current weather data. Costs $0.001 USDC per call.",
    input_schema: {
      type: "object" as const,
      properties: {
        city: { type: "string", description: "City name" },
      },
      required: ["city"],
    },
  },
];

// Execute tool calls — payment handled automatically
async function executeTool(name: string, input: Record<string, unknown>) {
  switch (name) {
    case "get_weather": {
      const response = await fetchWithPayment(
        `http://localhost:4021/weather?city=${encodeURIComponent(input.city as string)}`,
      );
      return await response.json();
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// Agent loop
const anthropic = new Anthropic();

async function runAgent(userMessage: string) {
  const messages: Anthropic.Messages.MessageParam[] = [
    { role: "user", content: userMessage },
  ];

  while (true) {
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      tools,
      messages,
    });

    if (response.stop_reason === "end_turn") {
      const text = response.content.find((b) => b.type === "text");
      return text?.text;
    }

    // Process tool uses
    const toolUses = response.content.filter((b) => b.type === "tool_use");
    messages.push({ role: "assistant", content: response.content });

    const toolResults: Anthropic.Messages.ToolResultBlockParam[] = [];
    for (const toolUse of toolUses) {
      if (toolUse.type !== "tool_use") continue;
      const result = await executeTool(
        toolUse.name,
        toolUse.input as Record<string, unknown>,
      );
      toolResults.push({
        type: "tool_result",
        tool_use_id: toolUse.id,
        content: JSON.stringify(result),
      });
    }
    messages.push({ role: "user", content: toolResults });
  }
}

const answer = await runAgent("What's the weather like in Tokyo?");
console.log(answer);
```

## Bazaar Discovery Agent

Discover available x402 services, evaluate pricing, and call them dynamically.

```typescript
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });
const fetchWithPayment = wrapFetchWithPayment(fetch, client);

interface BazaarResource {
  resource: string;
  type: string;
  accepts: Array<{ maxAmountRequired: string; network: string }>;
  metadata: { description: string };
}

async function discoverServices(facilitatorUrl: string): Promise<BazaarResource[]> {
  const response = await fetch(`${facilitatorUrl}/discovery/resources`);
  const data = await response.json();
  return data.items;
}

async function findAffordable(services: BazaarResource[], maxCostUSDC: number) {
  return services
    .map((s) => ({
      ...s,
      costUSDC: parseInt(s.accepts[0].maxAmountRequired) / 1_000_000,
    }))
    .filter((s) => s.costUSDC <= maxCostUSDC)
    .sort((a, b) => a.costUSDC - b.costUSDC);
}

// Discover → Filter → Call
const services = await discoverServices("https://x402.org/facilitator");
const affordable = await findAffordable(services, 0.01); // Max $0.01

for (const service of affordable) {
  console.log(`Calling ${service.resource} ($${service.costUSDC})`);
  const response = await fetchWithPayment(service.resource);
  console.log(await response.json());
}
```

## Budget-Controlled Agent Wallet

Enforce spending limits for autonomous agents.

```typescript
class AgentWallet {
  private totalSpent = 0;
  private txLog: Array<{ url: string; amount: number; ts: Date }> = [];

  constructor(
    private dailyBudget: number,
    private perCallMax: number,
  ) {}

  approve(url: string, amountAtomic: string): boolean {
    const usd = parseInt(amountAtomic) / 1_000_000;

    if (usd > this.perCallMax) {
      console.warn(`Rejected: $${usd} exceeds per-call max $${this.perCallMax}`);
      return false;
    }
    if (this.totalSpent + usd > this.dailyBudget) {
      console.warn(`Rejected: daily budget exhausted`);
      return false;
    }

    this.totalSpent += usd;
    this.txLog.push({ url, amount: usd, ts: new Date() });
    return true;
  }

  summary() {
    return {
      spent: this.totalSpent,
      remaining: this.dailyBudget - this.totalSpent,
      calls: this.txLog.length,
    };
  }

  resetDaily() { this.totalSpent = 0; }
}

// Wire into x402 client via lifecycle hooks
const wallet = new AgentWallet(1.0, 0.10); // $1/day, $0.10/call

client.onBeforePayment(async (details) => {
  return wallet.approve(details.resource, details.amount);
});

client.onAfterPayment(async () => {
  console.log("Budget:", wallet.summary());
});
```

## Multi-Agent Payment Orchestration

Separate wallets and budgets per agent role.

```typescript
function createAgent(name: string, keyEnvVar: string, budgetUSDC: number) {
  const signer = privateKeyToAccount(process.env[keyEnvVar] as `0x${string}`);
  const client = new x402Client();
  registerExactEvmScheme(client, { signer });

  const wallet = new AgentWallet(budgetUSDC, budgetUSDC / 10);

  client.onBeforePayment(async (details) => {
    const ok = wallet.approve(details.resource, details.amount);
    if (ok) console.log(`[${name}] Approved: ${details.resource}`);
    return ok;
  });

  return {
    client,
    wallet,
    fetch: wrapFetchWithPayment(fetch, client),
  };
}

const research = createAgent("research", "RESEARCH_KEY", 5.0);
const data     = createAgent("data",     "DATA_KEY",     2.0);
const analysis = createAgent("analysis", "ANALYSIS_KEY", 1.0);
```
