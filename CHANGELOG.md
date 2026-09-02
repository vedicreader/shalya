# Release notes

<!-- do not remove -->

## 0.0.6

### New

- `read_page` reads any target fossick knows: a page, an arXiv id, a YouTube link, a GitHub file, a
  PDF, a local path. `fossick.read` picks the reader and escalates past bot walls, so the reader
  table and the thin-page retry that lived here are gone. `md_title` and `md_sections` come with it,
  and `LocalHost.read_url` is now one line over it.
- `tool_groups` and `group_of` answer which group a tool name belongs to, read off the factories
  rather than a second list a caller has to keep in step.
- `summary` marks the one line a person reads after a tool runs, `summarise` renders it, and
  `SUMMARIES` answers from a name alone. Every tool shalya builds carries one.
- `acts`, `has_effect` and `ACTING_TOOLS` name the effects approval does not gate, and
  `read_only(effects=False)` withholds them.

### Fixed

- `create_file`, `edit_cell` and `add_cell` consulted no write guard, so a host that refused an edit
  to a generated file was bypassed by writing the whole file, or the whole cell, instead.
- `read_only` read the `@writes` mark alone, so a tool built somewhere that never marked it was
  handed to an agent which must not act. It reads the mark or the name now, and fails safe on either.
- `image_tools` took `model_id` as a string, so a caller that reads the turn's model per call had no
  way to pass it. It accepts a callable.
- A path outside the open folders raised out of `view_file`, `replace_text`, `edit_file`, `outline`,
  `ls` and `similar_code`. It is the commonest mistake a model makes, and a raise ends the turn
  instead of letting it try again. Every path tool answers with `ERROR: ` now.
- `read_skill` clipped a skill body a second time at a smaller budget than `Skill.text` holds, so a
  skill written up to the limit arrived without its closing tag.
- `save_media` numbered by file count, so deleting one picture made the next one overwrite another.
- `terminal_text(0)` returned the whole transcript, because `transcript[-0:]` is `transcript[0:]`.
- `clip` with a budget of zero or less kept the end of the string and reported nothing shown.
  `run_shell` reached it by subtracting its margin from a small budget.
- `_fuse` imported `litesearch` outside the `try` written to fall back without it.
- `watch_url` was offered to hosts that declare they accept reminders only.
- `replace_text`'s docstring named an `edits` parameter it does not take.

## 0.0.1
shalya - arrow heads for ramabana
