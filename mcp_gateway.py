"""
BrickLayer MCP Gateway
======================
A FastMCP 3.1 proxy that aggregates upstream MCPs into a single HTTP endpoint.
BrickLayer sessions connect here instead of loading each server individually.

Usage:
    python mcp_gateway.py            # runs on 127.0.0.1:8350
    python mcp_gateway.py --port 8351

Claude Code connection (.claude.json):
    {
      "mcpServers": {
        "bricklayer-gateway": {
          "type": "http",
          "url": "http://127.0.0.1:8350/mcp"
        }
      }
    }
"""

import argparse
import os
import sys

try:
    from fastmcp.mcp_config import MCPConfig
    from fastmcp.server import create_proxy
except ImportError:
    print("fastmcp not installed. Run: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Upstream MCP definitions — sensitive values fall back to env vars.
# ---------------------------------------------------------------------------

EXA_API_KEY = os.environ.get("EXA_API_KEY", "d1383966-eb3f-4c92-9291-b53f4d0c15d9")

MCP_CONFIG = {
    "mcpServers": {
        "recall": {
            "command": "node",
            "args": ["C:/Users/trg16/Dev/Recall/mcp-server/index.js"],
            "env": {
                "RECALL_HOST": os.environ.get(
                    "RECALL_HOST", "http://100.80.82.114:8200"
                ),
                "RECALL_API_KEY": os.environ.get(
                    "RECALL_API_KEY", "recall-admin-key-change-me"
                ),
            },
        },
        "github": {
            "command": "C:/Program Files/nodejs/npx.cmd",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get(
                    "GITHUB_PERSONAL_ACCESS_TOKEN", ""
                ),
            },
        },
        "context7": {
            "command": "C:/Program Files/nodejs/npx.cmd",
            "args": ["-y", "@upstash/context7-mcp"],
        },
        "firecrawl": {
            "command": "C:/Program Files/nodejs/npx.cmd",
            "args": ["-y", "firecrawl-mcp"],
            "env": {
                "FIRECRAWL_API_URL": os.environ.get(
                    "FIRECRAWL_API_URL", "http://192.168.50.35:3002"
                ),
                "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", "local"),
            },
        },
        "exa": {
            "type": "http",
            "url": (
                f"https://mcp.exa.ai/mcp?exaApiKey={EXA_API_KEY}"
                "&tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,"
                "crawling_exa,company_research_exa,people_search_exa,"
                "deep_researcher_start,deep_researcher_check"
            ),
        },
    }
}


def main() -> None:
    parser = argparse.ArgumentParser(description="BrickLayer MCP Gateway")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8350)
    args = parser.parse_args()

    print(f"Starting BrickLayer MCP Gateway on {args.host}:{args.port} ...", flush=True)

    config = MCPConfig.from_dict(MCP_CONFIG)
    gateway = create_proxy(config, name="BrickLayer Gateway")

    print(f"Gateway ready — connect at http://{args.host}:{args.port}/mcp", flush=True)
    gateway.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
