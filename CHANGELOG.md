# Release notes

<!-- do not remove -->

## 0.1.8

- `remember` takes optional `cue`, `component`, `evidence` and `confidence`. With any of them set, it stores one `field: value` line per field, with `lesson` first. A vault titles the note by that first line. Without them, `remember` stores the text unchanged.
- `component` is one of `LESSON_COMPONENTS` (`rule`, `skill`, `extension`, `tool`, `memory`) and `confidence` one of `LESSON_CONFIDENCE` (`low`, `medium`, `high`). Any other value, or fields with blank text, returns an `ERROR:` result. `lesson_text` builds the block.
- `skill_dirs` and `discover` take a `learned` folder. Its `skills` folder is first on the search path. Its skills override installed package skills and lose to every folder a person writes.

## 0.1.7

- Folders can be opened for reading only. `LocalHost(read_roots=)` and `add_root(path, readonly=True)` open them, and `read_roots` lists them. `roots` stays the folders writes may reach.
- `grep`, `ls` with no path or `recursive=True`, the code index and file reads search read roots too. A root inside another is searched with it, once.
- A write, or a shell command whose folder is in a read root, is refused with `READ_ONLY`. A picture there can be shown.
- A read root applies the credential deny list that `read_outside` applies, so a read root as wide as `~` does not open `.ssh`.
- `roots_note` names the read-only folders.

## 0.1.6

- `clip_json` keeps a dict within `n` by shortening its longest strings, so a long `result` no longer pushes a git report past its budget. A long list stays a list: the items that fit, then a last item saying how many more.
- `clip_lines` reserves its whole note, so a long hint no longer pushes a result past `n`.
- `run_shell` no longer forces a 500-character body under a smaller budget.
- `spill_dir` is made once, under a lock. Its folder is private to the OS user, and every `Sandbox` in the process can read it and none can write it.

## 0.1.5

- The git tools return JSON that stays JSON. 0.1.4 clipped a report longer than the budget as text, so a harness reading `undo` and `head` from it lost them. `clip_json` returns the whole document when it fits, and otherwise its plain fields with a `truncated` note naming the file that holds the whole.

## 0.1.4

- `clip` and `clip_lines` count their note against `n`. A clipped result is at most `n` characters whenever `n` is longer than its note, so a harness that cuts at the same budget keeps the note.
- `clip(keep=True)` saves the whole text with `spill` and names the file in the note. `spill_dir` is one folder per process; `Sandbox.check` allows reads inside it and refuses writes.
- The tools that cannot page keep the rest this way: `run_shell`, `shell_output`, `run_python`, `inspect_python`, `read_terminal`, `read_url`, `research`, `page_text`, `page_eval`, `api_load`, `api_call`, `memory_search`, `memory_read`, `ask_memory`, the git tools and `read_skill`.
- Every tool clips to its factory's `mx`. `read_skill`, the git tools and the memory tools no longer return two or three times the budget, and `read_url`, `web_search` and the session tools no longer ignore it.
- The `run_shell` truncation note no longer suggests `| tail`.

## 0.1.3

- `Media(str)`: a tool result that carries pictures in `.media`. `screenshot` returns one, so a harness can show the model the picture as well as the path.
- `view_file` on a picture (recognised by its bytes, up to 20 MB, inside the open folders) returns it as `Media` rather than refusing it as not text.

## 0.1.2

- `git_commit(path=)` commits in the repository `path` names, like the other git tools; `git_repo(host, path)` is that rule, and `paths` are relative to it.
- `SessionHost.restart_kernel` and a `restart_kernel` tool: a write, since it empties the person's namespace.
- `BrowserHost` and the opt-in `browser` group (`optin=('browser',)`): `browse`, `screenshot`, `page_text` and `page_reload` look; `page_click`, `page_type` and `page_eval` are writes. `screenshot` returns the PNG's path. `LocalHost` has no browser.

## 0.1.1

- `generate_image(images=[...], path=...)`: draw from reference pictures (the images edits endpoint, `input_fidelity='high'` for gpt-image models) and save where asked; a `path` refuses `.git` (any case), credential paths, symlinks, and existing files that are not pictures; the read-only copy has no `path`. `image_targets(path, n)` names every file a drawing writes.
- Pictures are recognised by their bytes (PNG, JPEG, GIF, WebP), capped at 20 MB each and 8 per call; API errors carry the response body.
- `view_file` says a binary file is not text; `create_file` refuses to overwrite a non-text file; `replace_text` says "not a text file".
- `memory_search` returns the vault's rows (with `age`/`stale`), not the result dict's key names.
- `denied()` matches credential paths case-insensitively (macOS).

## 0.1.0


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
