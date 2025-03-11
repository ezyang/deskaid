# codemcp

Make Claude Desktop a pair programming assistant by installing codemcp. With it, you can directly ask Claude to implement features, fix bugs and do refactors on a codebase on your computer; Claude will directly edit files and run tests. Say goodbye to copying code in and out of Claude's chat window!

<a href="https://glama.ai/mcp/servers/vujkyr83by">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/vujkyr83by/badge" alt="Deskaid MCP server" />
</a>

![Screenshot of Claude Desktop with codemcp](static/screenshot.png?raw=true)

codemcp offers similar functionality to other AI coding software (Claude Code, Cursor, Cline, Aider), but it occupies a unique point in the design space:

1. It's intended to be used with Claude Pro, Anthropic's $20/mo subscription offering. **Say goodbye to giant API bills**. (Say hello to time-based rate limits.)

2. It's built around **safe agentic AI** by providing a limited set of tools that helpful, honest and harmless LLMs are unlikely to misuse, and enforcing best practices like use of Git version control to ensure all code changes can be rolled back. As a result, you can safely **unleash the AI** and only evaluate at the end if you want to accept the changes or not.

3. It's **IDE agnostic**: you ask Claude to make changes, it makes them, and then you can use your favorite IDE setup to review the changes and make further edits.

## Getting started

First, [Install uv](https://docs.astral.sh/uv/getting-started/installation/).

Then, in `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codemcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ezyang/codemcp@prod",
        "codemcp",
      ]
    }
  }
}
```

## Usage

First, you must create a `codemcp.toml` file in the Git repository checkout you want to work on. If you want the agent to be able to do things like run your formatter or run tests, add the commands to execute them in the commands section (note: these commands need to appropriately setup any virtual environment they need):

```toml
format = ["./run_format.sh"]
test = ["./run_test.sh"]
```

Next, in Claude Desktop, we recommend creating a Project and putting this in the Project Instructions:

```
Before doing anything, first init project $PROJECT_DIR.
```

Where `$PROJECT_DIR` is the path to the project you want to work on.

Then chat with Claude about what changes you want to make to the project. Every time codemcp makes a change to your code, it will generate a commit.

To see some sample transcripts using this tool, check out:

- [Implement a new feature](https://claude.ai/share/a229d291-6800-4cb8-a0df-896a47602ca0)
- [Fix failing tests](https://claude.ai/share/2b7161ef-5683-4261-ad45-fabc3708f950)
- [Do a refactor](https://claude.ai/share/f005b43c-a657-43e5-ad9f-4714a5cd746f)

We recommend having the repository that codemcp is operating be a distinct branch from the default branch. Suppose that codemcp is operating on `develop` and the default branch is `main`, here are some useful commands:

- View a diff of LLM edits: `git diff main`
- Reject LLM changes: `git reset --keep main`
- Accept LLM changes: `git fetch . develop:main`
  - If you want to squash the commits, run `git rebase -i` and squash before you run the fetch
  - If you want to preserve the intermediate commits, checkout `main` and then run `git merge develop --no-ff`

## Philosophy

- When you get rate limited, take the time to do something else (review Claude's code, review someone else's code, make plans, do some meetings)

- This is *not* an autonomous agent. At minimum, you have to intervene after every chat to review the changes and request the next change. While you *can* ask for a long list of things to be done in a single chat, you will likely hit Claude Desktop's output limit and have to manually "continue" the agent anyway. Embrace it, and use the interruptions to make sure Claude is doing the right thing.

- When Claude goes off the rails, it costs you time rather than dollars. Behave accordingly: if time is the bottleneck, watch Claude's incremental output carefully.

## Configuration

Here are all the config options supported by `codemcp.toml`:

```toml
global_prompt = """
Before beginning work on this feature, write a short haiku. Do this only once.
"""

[commands]
format = ["./run_format.sh"]
test = ["./run_test.sh"]
```

The `global_prompt` will be loaded when you initialize the project in chats.

The `commands` section allows you to configure commands for specific tools:
- `format`: used to format code according to project standards. Formatting is done at the very end of a task.
- `test`: used to run tests. The test script should accept an argument which will be passed as is to the underlying test framework.

## Troubleshooting

Logs are written to `~/.codemcp/codemcp.log`. The log level can be set in a global configuration file at `~/.codemcprc`:

```toml
[logger]
verbosity = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

Logging is not configurable on a per project basis, but this shouldn't matter much because it's difficult to use Claude Desktop in parallel on multiple projects anyway.