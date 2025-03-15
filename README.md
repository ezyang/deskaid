# codemcp

Make Claude Desktop a pair programming assistant by installing codemcp.  With
it, you can directly ask Claude to implement features, fix bugs and do
refactors on a codebase on your computer; Claude will directly edit files and
run tests.  Say goodbye to copying code in and out of Claude's chat window!

![Screenshot of Claude Desktop with codemcp](static/screenshot.png?raw=true)

codemcp offers similar functionality to other AI coding software (Claude Code,
Cursor, Cline, Aider), but it occupies a unique point in the design space:

1. It's intended to be used with Claude Pro, Anthropic's $20/mo subscription
   offering.  **Say goodbye to giant API bills**.  (Say hello to time-based rate
   limits.)

2. It's built around **safe agentic AI** by providing a limited set of tools
   that helpful, honest and harmless LLMs are unlikely to misuse, and enforcing
   best practices like use of Git version control to ensure all code changes
   can be rolled back.  As a result, you can safely **unleash the AI** and
   only evaluate at the end if you want to accept the changes or not.

3. It's **IDE agnostic**: you ask Claude to make changes, it makes them, and
   then you can use your favorite IDE setup to review the changes and make
   further edits.

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
Note, if you get an error like "MCP codemcp: spawn uvx ENOENT" on MacOS, then you most likely need to the absolute path to uvx. For example 
```
/Users/<your local username>/.local/bin/uvx
```
instead of just uvx

## Usage

First, you must create a `codemcp.toml` file in the Git repository checkout
you want to work on.  If you want the agent to be able to do things like run
your formatter or run tests, add the commands to execute them in the commands
section (note: these commands need to appropriately setup any virtual
environment they need):

```toml
format = ["./run_format.sh"]
test = ["./run_test.sh"]
```

Next, in Claude Desktop, we recommend creating a Project and putting this in
the Project Instructions:

```
Initialize codemcp with $PROJECT_DIR
```

Where `$PROJECT_DIR` is the path to the project you want to work on.

Then chat with Claude about what changes you want to make to the project.
Every time codemcp makes a change to your code, it will generate a commit.

To see some sample transcripts using this tool, check out:

- [Implement a new feature](https://claude.ai/share/a229d291-6800-4cb8-a0df-896a47602ca0)
- [Fix failing tests](https://claude.ai/share/2b7161ef-5683-4261-ad45-fabc3708f950)
- [Do a refactor](https://claude.ai/share/f005b43c-a657-43e5-ad9f-4714a5cd746f)

codemcp will generate a commit per chat and amend it as it is working on your feature.

## Philosophy

- When you get rate limited, take the time to do something else (review
  Claude's code, review someone else's code, make plans, do some meetings)

- This is *not* an autonomous agent.  At minimum, you have to intervene after
  every chat to review the changes and request the next change.  While you
  *can* ask for a long list of things to be done in a single chat, you will
  likely hit Claude Desktop's output limit and have to manually "continue" the
  agent anyway.  Embrace it, and use the interruptions to make sure Claude is
  doing the right thing.

- When Claude goes off the rails, it costs you time rather than dollars.
  Behave accordingly: if time is the bottleneck, watch Claude's incremental
  output carefully.

## Configuration

Here are all the config options supported by `codemcp.toml`:

```toml
project_prompt = """
Before beginning work on this feature, write a short haiku.  Do this only once.
"""

[commands]
format = ["./run_format.sh"]
test = ["./run_test.sh"]

[git]
auto_commit = false  # Set to false to disable automatic commits after file changes
```

The `project_prompt` will be loaded when you initialize the project in chats.

The `commands` section allows you to configure commands for specific tools. The
names are told to the LLM, who will decide when it wants to run them.

The `git` section allows you to configure Git-related behavior:
- `auto_commit`: When set to `false`, codemcp will no longer automatically commit changes 
  after editing files. This allows you to review changes before manually committing them.
  Defaults to `true` for backward compatibility.

You can also control auto-commit behavior in the following ways (in order of precedence):
1. Set the `CODEMCP_AUTO_COMMIT` environment variable to "true" or "false"
2. Project-specific `codemcp.toml` setting (as shown above)
3. User-wide setting in `~/.codemcprc`:
   ```toml
   [git]
   auto_commit = false
   ```

We also support a more verbose syntax where you can give specific instructions on a 
tool-by-tool basis:

```
[commands.test]
command = ["./run_test.sh"]
doc = "Accepts a pytest-style test selector as an argument to run a specific test."
```

## Troubleshooting

To run the server with inspector, use:

```
PYTHONPATH=. mcp dev codemcp/__main__.py
```

Logs are written to `~/.codemcp/codemcp.log`. The log level can be set in a global configuration file at `~/.codemcprc`:

```toml
[logger]
verbosity = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

Logging is not configurable on a per project basis, but this shouldn't matter
much because it's difficult to use Claude Desktop in parallel on multiple
projects anyway.
