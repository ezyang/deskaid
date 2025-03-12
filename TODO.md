BIGGEST PROBLEMS
- Git structure seems good, maybe want a way to make the LLM generate the
  commit message
- Audit the tests to make sure they actually do the right thing

CODE QUAL
- Setup types
- General logging to repro problems (CLI logging helps, but some signpost
  logging would be good too)
    - An attempt was done at e6b49ee but I think it's overlogging, and the
      logging format is not right
- Stop using catch all exceptions

TOOLS:
- Typecheck/build integration
- Scrape webpage and add to context
- Explicitly add file to context
- Make file executable tool
- A few more of Claude Code's tools: glob, memory, notebook

FEATURES
- Diff review mode
- Rage

SHARPEN THE SAW
- Use the Anthropic export data to do some token counting / analysis

LLM AFFORDANCE
- Support this style of grep
{
  `command`: `Grep`,
  `pattern`: `self\\.assertIn.*normalized_result`,
  `path`: `/Users/ezyang/Dev/codemcp/test/test_mcp_e2e.py`
}
- Regex search replace for refactor-y stuff (need to prompt this well, cuz LLM
  needs to review changes)
- Make CLAUDE.md system prompt work (let's be compat with claude code)
- Infer my codemcp.toml

~~~~

HARD TO FIX
- Deal with output length limit from Claude Desktop (cannot do an edit longer
  than the limit)

UNCLEAR PAYOFF
- More faithfully copy claude code's line numbering algorithm
- Figure out if "compact output" is a good idea
- Figure out how to make Claude stop trying to do things I don't want it to do
  (like running tests)
