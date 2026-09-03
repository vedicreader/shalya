# Release notes

<!-- do not remove -->

## 0.0.7 (unreleased)
- `read_page` is the whole of reading one url: the site readers, the fetch, the extraction that
  decides which part of the page is the article, the escalation for a page that answered with a
  shell, and the JSON-LD on top. `LocalHost.read_url` is now four lines over it, and takes a `sel`
  selector. It returns `title`, `kind`, `sections` and `strategy` beside `text` and `url`.
  Leela's `Research.read` was a second implementation of the same dispatch; the two had diverged in
  both directions, so this is the union: Leela's candidate scoring, repeated-`<article>` sectioning
  and independent-extraction fallback, with shalya's structured data and stealthy retry.
- `READERS` rows carry a fourth field, the `kind` their result is: `repo`, `paper` or `page`.
- `THIN_PAGE` is 800 rather than 400: the larger threshold catches strictly more shells, at the
  cost of one more fetch on a page that was going to be thin anyway.
- `md_title`, `CONTENT_SEL`, `BLOCK_SEL`, `MAX_PAGE` and `MIN_SECTION` are public with it.
- `tool_groups` and `group_of` name the group every tool belongs to without a host, built from the
  factories rather than listed beside them, so the table cannot go stale. `image` and `skill` are
  in it. A checkpoint form drawing a saved call has the tool's name and nothing else.

### Fixed

- `create_file`, `edit_cell` and `add_cell` consulted no write guard, so a host refusing an edit to
  a generated file was bypassed by writing the whole file, or the cell, instead.
- A path outside the open folders raised out of `view_file`, `replace_text`, `edit_file`, `outline`,
  `ls` and `similar_code`, ending the turn where an `ERROR: ` lets the model try again. `resolved`
  is the one spelling.
- `read_skill` clipped a body a second time at a smaller budget than `Skill.text` holds, so a skill
  written up to the limit arrived without its closing tag.
- `save_media` numbered by counting files, so deleting one picture made the next overwrite another.
- `terminal_text(0)` returned the whole transcript: `transcript[-0:]` is `transcript[0:]`.
- `clip` with a budget of zero or less kept the end of the string and reported nothing shown.
  `run_shell` reached it by subtracting its margin from a small budget.
- `_fuse` imported `litesearch` above the `try` written to fall back without it.
- `watch_url` was offered to a host that declares it accepts reminders only.

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
