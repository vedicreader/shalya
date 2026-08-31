# Release notes

<!-- do not remove -->

## 0.0.3

- `summary` marks the one line a person reads after a tool runs, beside the tool's docstring, and
  `summarise` reads it. Every tool this package defines carries one, including the git group, the
  API group, `add_root`, `ask_memory`, `public_api` and `generate_image`, which the dispatch that
  used to hold this in Ramabana had never named. `SUMMARIES` indexes them by name as well, because
  an activity row records what was called rather than the object that ran.
- `one_line` is the clipper both sides of that were using separately.

## 0.0.2

- `acts` marks a tool that acts without writing a file the user owns: running code, an API call that
  can POST, an image that costs money, and standing work that outlives the turn. `has_effect` reads
  the mark and `ACTING_TOOLS` names the same six for a caller that only has a name. The mark is
  orthogonal to `writes`, so approval still gates writes and nothing else.
- `read_only` takes `effects=False` to withhold them, for an agent that may look and propose but
  never act. The default keeps them, so a sub-agent still researches.
- The tool budget message no longer says `sub-agent`. The budget is reachable without delegating.

## 0.0.1
shalya - arrow heads for ramabana
