# DotCortex architecture policy

**Goal:** change logic (backend + frontend) freely without destroying DeepTutor’s architecture or re-coding systems that already exist.

## Rule of thumb

```text
Want a change?
  → Does DeepTutor already have a hook?
        YES → extend that hook (smallest diff)
        NO  → add under dotcortex/ + one thin register call
```

## Theme (worked example)

Already supported: `light` | `dark` | `glass` | `snow` via `web/lib/theme.ts` + `globals.css` tokens + Appearance settings.

**Zehnium theme = new palette id**, not a new theme product:

1. Add `"zehnium"` to `Theme` in `web/lib/theme.ts`
2. Add `.theme-zehnium { --background: …; --primary: #ff6b00; … }` in `globals.css` (map from Zehnium `--z-*`)
3. Add option in `AppearanceSettingsSection.tsx`
4. Wire `applyThemeToDocument` class list

Wrong: new “Theme Studio” page, parallel CSS framework, hardcoded colors in every component.

## Backend / MCP / mastery pins

- Implement under `dotcortex/` (Python package).
- Pin store + map overview use mastery path ids (not a parallel skill table).
- Register tools/routes with the existing DeepTutor tool/capability/MCP surfaces.
- Do not fork a second FastAPI app unless you intentionally split deploy later.

## Frontend product surfaces

- Home = chat (`CoachDesk`) + map icon overlay for pinned mastery paths.
- New screens: `web/features/dotcortex/` or `web/components/dotcortex/`
- Enter from existing sidebar / Learning Space with one link — don’t rebuild the shell.

## Sync with DeepTutor

```bash
git fetch upstream
git merge upstream/main
```

Keep product code in `dotcortex/` and `web/**/dotcortex/**` so merges stay small.
