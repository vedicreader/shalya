# Decisions

This page lists the decisions that a maintainer must know. Each entry gives the decision, the reason, the version, and the place in the code.
This repo has no CLAUDE.md. The house style and the rules of the package family are in Leela's CLAUDE.md. How to build and test is in the "Develop" part of the [README](../README.md). The changes of each release are in the [CHANGELOG](../CHANGELOG.md).

## What lives here, what does not

- **shalya gives the tools and the hosts. It does not run an agent loop or call a model.** ramabana does that, and asks shalya for the tools. Apps import tools and hosts from `shalya` by name, not through `ramabana.tools`. `tools_for` in ramabana is the one exception: it adds the image group from the turn's model. `shalya/tools.py`, `shalya/host.py`.
- **Use the packages of the family. Do not copy them.** Git is `gheasy.repo`, fetch and search are `fossick`, the code index is `koshas`, memory is `vishalakshi`, kernels are `kunda` and `dhrishti`. When a package cannot do a thing, patch that package. `pyproject.toml`.

## Hosts and groups

- **A host declares a group by the class it inherits.** `CodeHost`, `WebHost`, `ShellHost`, `GitHost` and the others each name one `group`. A host that inherits one writes every method it asks for. `Host.provides` is the only way to ask what a host supports, less `without`. There is no capabilities dict. `Host` and the `*Host` classes in `nbs/01_host.ipynb`.
- **A model gets only the tools that can work.** `tools_for(host)` builds the tools of each group the host provides. A group that the host cannot back gives no tools. `group_of(name)` says which group a tool is in. Do not keep a second list of tool names. `nbs/02_tools.ipynb`.
- **Some groups are opt-in.** `OPTIN` has `exhash`, `research`, `author`, `browser` and `legacy`. The browser group is opt-in because its tools act on a real page. (0.1.2, 0.1.3) `OPTIN` in `nbs/02_tools.ipynb`.
- **The legacy shims stay for one release.** `legacy_tools` keeps old tool names that an MCP client may still send. Remove them in 0.2.0. `legacy_tools`.

## Tool results

- **A tool never raises.** An exception ends the turn of the agent. A tool that fails returns a string that starts with `ERROR:`. `failed(result)` checks it. `err` and `failed` in `nbs/00_core.ipynb`.
- **Each result fits a budget.** `MAX_TOOL_CHARS` is 6000, set for the smallest model. `clip`, `clip_lines` and `clip_json` count their note in the budget. With `keep=True` the full text goes to `spill`, and the note names the file. A git report stays valid JSON, so a harness can read `undo` and `head`. (0.1.4 to 0.1.6) `nbs/00_core.ipynb`.
- **Each tool parameter has a docments comment.** The JSON schema of the tool gets it, and the docstring stays one line. (0.1.18) `nbs/02_tools.ipynb`.

## Safety

- **The open folders are the limit.** `Sandbox.check` refuses a path outside the roots. A read root (0.1.7) is for reading only, and a write there gets `READ_ONLY`. `DENY` lists credential files that are never read, also in a read root. A read through a hard link is refused, except under `site-packages` and `node_modules`, because uv and pnpm install with hard links. (0.1.27) `Sandbox`, `DENY`, `HARDLINK` in `nbs/00_core.ipynb`.
- **The host can see and stop each read.** `read_guard` gets a `ReadCheck` before a read tool sends content. It can send it, mask it or withhold it. Shell and Python output go through it too, and a withheld command still gives its exit code. (0.1.10, 0.1.23) `guard` in `nbs/00_core.ipynb`. `url_ok` refuses a URL and `on_read` sees each web read and file read. Both are off by default. (0.1.28) `LocalHost`.
- **A page fetch does not use `auto=True`.** With `auto`, fossick can end in the logged-in debug Chrome on port 9223, and a page can make an agent open any URL. Only a host in `SESSION_HOSTS` may use it. That list is empty by default. (0.1.24) `SESSION_HOSTS`, `session_ok` in `nbs/01_host.ipynb`.
- **A shell command gets `/dev/null` as stdin.** Before, a command could read the keys of the user or block the terminal of the app. (0.1.19) `run_cmd`, `run_cmd_bg`.
- **The git write tools ask first and give an undo token.** `GIT_WRITE_TOOLS` lists them. `git_sync` merges or rebases. It never resets. (0.1.26) `GIT_WRITE_TOOLS` in `nbs/00_core.ipynb`, `git_tools` in `nbs/02_tools.ipynb`.
- **The code index is written in a child process.** A crash there does not stop the host. The host then opens the index for reading only. (0.1.21) `sync_index` in `nbs/01_host.ipynb`.

## Release and docs

- **Give the imports of a test cell their own cell.** The docs build runs only the cells with an import, `#| export` or `show_doc`. (19 Oct and 1 Nov 2026)
- **Develop with nbdev 3.3.25 or later.** That version releases on a clean tree. Local nbdev must match CI. (0.1.25) `dev` extra in `pyproject.toml`.
