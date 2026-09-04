# Release notes

<!-- do not remove -->

## 0.0.7
- Unified `read_page`: full site-read, fetch, article extraction, shell/page escalation, JSON-LD handling. `LocalHost.read_url` wraps it and returns `title`, `kind`, `sections`, `strategy`, `text`, `url`. Leela and shalya logic merged.
- `READERS` adds a fourth field: returned `kind` (`repo`, `paper`, `page`).
- `THIN_PAGE` is now 800. Catches more shells, at cost of another fetch for thin pages.
- `md_title`, `CONTENT_SEL`, `BLOCK_SEL`, `MAX_PAGE`, `MIN_SECTION` now public.
- `tool_groups` and `group_of` auto-name tool groups from factories—prevents stale table; covers `image` and `skill`. Checkpoints show tool's name only.

### Fixed

- `create_file`, `edit_cell`, `add_cell` now respect write guard. Generated files/cells were bypassing refusal.
- Out-of-scope paths now error out of `view_file`, `replace_text`, `edit_file`, `outline`, `ls`, `similar_code` rather than raising. Consistent `resolved` spelling.
- `read_skill` no longer doubly clips text, closing tag always present.
- `save_media` no longer overwrites after deletion—file numbering robust.
- `terminal_text(0)` fixed: avoids transcript leak on zero.
- `clip` with zero or less now returns nothing, never keeps accidental end-chars. `run_shell` adjusted.
- `_fuse` imports `litesearch` only under `try`.
- `watch_url` not offered to reminder-only hosts.


## 0.0.6
dep fix release

## 0.0.5
make tools succinct

## 0.0.4
init exposes inner all

## 0.0.3
- `summary` decorator for all tools to help humans understand what the tool does.

## 0.0.2

- `acts` marks a tool that acts without writing a file the user owns.
- `read_only` takes `effects=False` to withhold them, for an agent that may look and propose but never act. The default keeps them, so a sub-agent still researches.
- The tool budget message no longer says `sub-agent`. The budget is reachable without delegating.

## 0.0.1
shalya - arrow heads for ramabana