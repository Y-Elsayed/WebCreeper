# WebCreeper: Crawl. Extract. Discover.

WebCreeper is an open-source crawling framework built around **agents**.
Each agent is a crawler specialized for a specific task, and all agents share core crawling primitives from `creeper_core`.

## Agent Model

- Agents are modular crawler units with clear responsibilities.
- Each agent can expose its own settings and extraction behavior.
- Shared infrastructure (robots handling, retries, rate limits, hooks, policies) lives in the core.

This makes it easy to:
- Start simple with one agent.
- Add new agents without rewriting crawl infrastructure.
- Compose custom extraction logic through callbacks and hooks.

## Agent Selection

Use this table to choose the right agent.

| Agent | When To Use It | Documentation |
|---|---|---|
| `Atlas` | Crawl website structure, build link graphs, and run custom per-page extraction callbacks/hooks. | `docs/agents/atlas.md` |

All agent-specific setup and code examples are documented in each agent page.

## Documentation

- Installation and project docs index: `docs/README.md`
- Agent docs index: `docs/agents/README.md`

## License

MIT. See `LICENSE`.
