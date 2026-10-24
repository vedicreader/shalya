# Release notes

<!-- do not remove -->

## 0.1.21

- `LocalHost.sync_index` writes each Kosha index in a child process. A failed child retries once. Errors name the folder and the exit code or signal. Successful indexes reopen read-only in the host.
- Folder scans skip hidden folders and SQLite databases and sidecars. File tools refuse direct access to SQLite files before opening them.
- Needs litesearch 0.1.59. Each connection sets its own busy timeout, writes commit in batches of 1,000 rows, and the WAL is truncated after bulk writes.

## 0.1.20

- `LocalHost.tmux_pane` is the pane tmux started this process in, `$TMUX_PANE`. It was fastmux's `current_pane()`, the client's active pane, so `open_pane` and the panes built on it, such as Ramabana's now pane and its Getting started pane, opened beside whichever window was active when the session's own window was not. Without `$TMUX_PANE` it still falls back to `current_pane()`.
- A host given a pane target as a string, `LocalHost(tmux='%3')` or `'session:window.pane'`, resolves it with `fastmux.Pane.fetch`. It called `fastmux.pane` and `fastmux._tmux`, which fastmux 0.0.2 and 0.0.3 do not have, so it raised `AttributeError`.

## 0.1.19

- `run_cmd` and `run_cmd_bg` give the command `/dev/null` as standard input. A command used to inherit the host's standard input, which in a terminal app is the terminal itself. It could read the user's keystrokes, or turn the terminal non-blocking, which the app shares; ramabana's CLI then froze. A command that reads standard input now gets end of file at once, so `cat` with no file returns instead of waiting for the timeout. Both already ran in their own session, so a timeout or `cmd_stop` kills the command the same way.

## 0.1.18

- Every parameter of every tool has a description in its JSON schema. Each one is a docments comment on the parameter, which `get_schema` reads, so `mk_toolspec` and native tool calling carry it to the model. Parameter detail moved out of the tool docstrings, which are now one-line summaries. Signatures, defaults and behaviour are unchanged.

## 0.1.17

- `grep`'s `path_filter` finds a folder or file the way a model writes it: `pkg`, `pkg/sub/`, `./pkg/sub`, an absolute path inside an open folder, or one starting with the open folder's own name. It also matches in any case. Through ripgrep it matched only a file name or a whole relative path, so a folder filter returned "no matches" for text the file held. `path_scope` turns a filter into the pattern both ripgrep and the tool's own file scan use. A glob such as `*.py` still works.
- `grep` with an absolute `path_filter` outside every open folder, and a recursive `ls` of such a folder, say that the path is outside the open folders and what to do instead. They used to answer "no matches" and "no matching files" for a folder `view_file` could read.
- A recursive `ls` lists each folder's files in sorted order. The order used to change from call to call.

## 0.1.16

- `generate_image` with no session folder saves under `media/` in the host's first open folder, checked by `host.check`. It used to save under the process's working directory, so a desktop app put pictures in its own data folder rather than the project.
- `media_dir` and `save_media` take `host=`. Without a session they use the host's open folder, and with neither they raise `ValueError` instead of writing to the working directory.

## 0.1.15

- `generate_image` draws through any OpenAI-shaped image API, not OpenAI's by name. `image_tools(route=)` takes a function returning `{base_url, api_key, model}`, or a sentence saying how to set a model up, which the tool returns instead of calling anything. Without one it is `openai_route`, OpenAI's API with `OPENAI_API_KEY`, as before. `turn_route=` gives the endpoint and key of the turn's own model for when it draws itself through the Responses API, which used to go to OpenAI whatever served the turn.
- `post_image`, `post_responses` and the edits call take `base_url` and `api_key`; without them they call OpenAI with `OPENAI_API_KEY`, as before. `OPENAI_BASE` names OpenAI's base URL.

## 0.1.14

- `parse_lesson` reads a lesson `lesson_text` wrote back into its fields, from a vault note's `field: value` lines or a memory file's ` | `-joined line with its `- [key] **title**: ` head. It returns None for a plain note. `lessons` finds every lesson in a memory file or vault note. `LESSON_FIELDS` names the fields in order.

## 0.1.13

- `post_image` (tools) is public, because Ramabana's tests replace it. `_post_image` stays as an alias. `generate_image` calls `post_image`, so a test replaces `shalya.tools.post_image`.

## 0.1.12

- `fuse` (host), `post_responses` (tools), `describe` and `mod_skill` (skills) are public, because Ramabana imports them. The `_`-prefixed names stay as aliases. `discover` calls `mod_skill`, so code that replaces how a module becomes a skill replaces `shalya.skills.mod_skill`; replacing `_mod_skill` no longer has an effect.

## 0.1.11

- `LocalHost.inspect_python` without a kernel deep-copies each name the code reads, so `radii.append(99)` leaves the real `radii` alone. Objects `deepcopy` refuses, and the namespace a user's function reads through its globals, stay shared.
- `cmd_stop` reports `stopped` for a command it killed, even when the shell exits `137` before its own `SIGKILL` lands.
- The `dev` extra holds the test and docs dependencies, `fastmux` included; the `dev` group points at it.

## 0.1.10

- `Host.read_guard`, when set, is asked before a read tool sends content to the model. It gets a `ReadCheck` (`path`, `tool`, `kind`, the turn's `model` and `local`, and `text` loaded on first use) and returns None to send it, a string to send instead, or a `Refusal`. A guard that raises refuses the read.
- `view_file` (text and pictures), `grep`, `search_code`, `similar_code`, `outline`, `public_api`, `notebook_cells`, `view_cell`, `git_diff` (file by file), `read_url`, `page_text`, `screenshot` and the reference pictures of `generate_image` go through it, as do the diffs `replace_text` and `edit_cell` return.
- A refusal reaches the model as `ERROR: <kind>: <path>: <why>`. A reference picture is never sent masked.
- `Host.model_local` returns `(local, model)` for the turn's model. `LocalHost` takes `read_guard=` and `model_local=`.
- With no guard set, every tool returns what it did before.

## 0.1.9

- A `search_code` hit's hint names only the tools that reach it on this host. A hit inside the open folders gets `view_file`/`replace_text`. A hit in a read root, or anywhere with `read_outside`, is read-only. Any other hit, such as an installed package on a host that does not read outside its folders, is named as outside the open folders. `reach_hint` builds the hint.

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
