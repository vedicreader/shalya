# Release notes

<!-- do not remove -->

## 0.1.0
- `replace_text(path, edits: list[dict])` and `edit_cell(path, cell_id, edits: list[dict])` take native lists of `{oldText, newText}`; a JSON string still parses this release; `spec` and `commands` on these two are gone.
- `edit_file` moves to the `exhash` opt-in group (`tools_for(optin=('exhash',))`) and takes `commands: list[list]`; `view_cell` shows plain numbered source.
- `ls(path, pattern, recursive)` absorbs `list_files` (folders always listed, `pattern` filters files); `similar_code` only with an index; `inspect_python('')` lists variables (`list_vars` gone); the `environment` tool is gone (the host method stays); `research` and `create_skill` opt in (`research`, `author`).
- Memory: `memory_read(ref='')` (was `node_id`) browses roots, a document's tree, or a node (`doc#n`; a title with `#` is still a document); `remember(key=)` upserts; `memory_tree` and `memory_topics` gone; `MemoryHost.memory_topics` no longer abstract; `memory_search` rows carry `age` and `stale`; `group_of('remember')` is `memory`.
- Watch: one `watch(target, kind, every, note, instructions, pattern)` with kind `url`/`remind`/`search`/`folder` (`WATCH_KINDS` maps them to vault actions); `set_reminder`, `watch_url`, `poll_watches` gone (the harness calls `host.poll()`); `LocalHost.watch_actions` follows the vault.
- Git: writes return `undo`, `undoes`, `summary`, `head`, `moved` beside the state; `git_status` returns the state alone (`root`, `branch`, `upstream`, `ahead`, `behind`, `clean`, `branches`, `changes`); `git_commit(amend=)`; `git_checkout(branch, create=False, path='')` and `git_remote(op, publish=False, path='')` move positional `path` last; `git_divergence(path, upstream)` → `git_divergence(against='', path='')` and absorbs `git_rebase_preview`; `GIT_TERMINAL_PROMPT=0` is set only when a real host builds the group, not at import.
- `tools_for(optin=)` (a tuple or one name); `OPTIN`; `legacy_tools` shims (`list_files`, `list_vars`, `environment`, `memory_tree`, `git_rebase_preview`, `set_reminder`, `watch_url`) for MCP clients, removed in 0.2.0; `tool_groups` files every opt-in tool under its capability group.
- Notebooks saved without cell ids (nbformat 4.4) get deterministic `c{i}` ids through `nb_read`, so `notebook_cells` and `edit_cell` agree; the first write persists them.
- `core.attempt`; `edits` error text names the shape; `summarise` no longer imports `shalya.tools`; one-line docstrings on every tool and host contract method (tested); `ACTING_TOOLS` names `watch`; `GIT_READ_TOOLS` drops the preview; `search_code` hits point at `replace_text`.
- Needs vishalakshi 0.1.17 (`note(key=)`, folder watches, `age`/`stale`, `policy`) and gheasy 0.0.10 (`create`, `commit(amend=)`, `push(publish=)`).

## 0.0.11
- `EVENTS` gains `background_done` and `watch`, fired by ramabana when a background delegation finishes and when a run is watched.

## 0.0.10
- `environment()` and the `environment` tool: this process, the venvs under the open folders, the commands on PATH, the `inspect_python` scopes, and the tmux pane.
- tmux through fastmux (`shalya[tmux]`): `LocalHost(tmux=)` auto-detects `$TMUX`; `terminal_text` reads the sibling panes; `run_cmd_bg` runs in a pane; `open_pane` and `close_pane`.
- Background commands: `run_cmd_bg`, `cmd_output`, `cmd_stop` on the host; `run_shell_bg`, `shell_output`, `shell_stop` tools; `close()` stops them.
- Git: `git_diff`, `git_log`, `git_commit`, `git_stash`.
- `fire` returns what the hooks return; `EVENTS` gains `session_start` and `stop`; `<cfg>/hooks.json` shell hooks.
- `Host.close()` no-op on the base.
- Needs fastmux 0.0.2 for the tmux extra.

## 0.0.9
- litesearch is imported where `_fuse` and `sync_index` run, not at module load; `import shalya` no longer brings numpy and pandas into a server.

## 0.0.8
- `read_page` hands dedicated readers to `fossick.read` (adds PDF) and skips the stealthy re-fetch.
- `GROUPS` pairs each Capability class with its factory; group name lives only on `cls.group`.
- `summarise` builds the tool table for a bare name, so a saved-turn call renders its one-liner.
- `Host.writes` is read by `tools_for`.
- Added `tests/test_web.py`.
- Removed `shalya.refactor`: a copy of leela's, imported by nothing; kosha carries the superset.
- Removed the bare `except` around `rrf_all`; litesearch declared `>=0.1.34`.

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