# shalya

> The tools an agent is given, and the host that answers them.

A host is an object that answers what it can: read a file, search an index, run a command, remember
a page. `tools_for` looks at one and returns the tools it can actually support. Nothing here runs an
agent loop or talks to a model.

## Install

```sh
pip install shalya
```

Each capability group is an extra, and the base install pulls `fastcore` and `exhash` only.

```sh
pip install 'shalya[code,web,memory,api,git,kernel]'
```

## Develop

```sh
uv sync --all-extras --group dev
uv run nbdev-export
uv run nbdev-test
uv run pytest
uv run nbdev-clean
```
