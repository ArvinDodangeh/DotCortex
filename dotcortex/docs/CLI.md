# DotCortex CLI name

## What you get

After `pip install -e .` (or reinstall):

```bash
dotcortex start
dotcortex init --non-interactive
dotcortex doctor
```

`deeptutor …` still works (same code) so upstream docs and merges stay sane.

## Runtime home

Either env var works:

```bash
export DOTCORTEX_HOME="$PWD"   # preferred for DotCortex docs
# or
export DEEPTUTOR_HOME="$PWD"   # upstream name
```

## What we did *not* rename (on purpose)

| Keep as-is | Why |
|---|---|
| Python package `deeptutor` / `deeptutor_cli` | Renaming breaks every import + upstream merge |
| PyPI project name `deeptutor` | Separate decision later if you publish DotCortex wheels |
| Storage keys `deeptutor-*` in the browser | Avoid wiping user prefs on upgrade |

## Reinstall so the command appears

```bash
cd ~/Desktop/zehnium/DotCortex
source .venv/bin/activate   # if you use a venv
pip install -e .
which dotcortex
dotcortex --help
```
