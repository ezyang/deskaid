# codemcp Architecture

This document provides an overview of the architecture and design decisions of codemcp.

## Project Configuration

The codemcp tool uses a TOML file (`codemcp.toml`) in the project root for configuration. This file has several sections:

### Project Prompt

The `project_prompt` string is included in system prompts to provide project-specific instructions to Claude.

```toml
project_prompt = """
Project-specific instructions for Claude go here.
"""
```

### Commands

The `commands` section specifies commands that can be executed by specialized tools at specific times. Commands are defined as arrays of strings that will be joined with spaces and executed in a shell context:

```toml
[commands]
format = ["./run_format.sh"]
```

Currently supported commands:
- `format`: Used by the Format tool to format code according to project standards.

## Tools

codemcp provides several tools that Claude can use during interaction:

- **ReadFile**: Read a file from the filesystem 
- **WriteFile**: Write content to a file
- **EditFile**: Make targeted edits to a file
- **LS**: List files and directories
- **Grep**: Search for patterns in files
- **InitProject**: Initialize a project and load its configuration
- **Format**: Format code according to project standards using the configured command

## System Integration

When a project is initialized using `InitProject`, codemcp reads the `codemcp.toml` file and constructs a system prompt that includes:

1. Default system instructions
2. The project's `project_prompt`
3. Instructions to use specific tools at appropriate times

For example, if a format command is configured, the system prompt will include an instruction for Claude to use the Format tool when the task is complete.
