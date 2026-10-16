# DotCortex plan — mastery path pins

Implements `dotcortex/DECISIONS.md` (2026-10-16 pin model).

## Data

Persistence: `<runtime home>/data/user/dotcortex/pins.json`

```text
active_path_id: string | null
pins: [{ path_id, source: user|agent, pinned_at, position?: {x,y} }]
```

## Phases

1. **Pin store + API** — `GET/POST/DELETE /api/dotcortex/pins`, `PUT .../active`
2. **Home = chat only** — remove `SkillsMapPanel`
3. **Map overlay** — overview of pins; drill into DeepTutor path map
4. **Chat prefix** — active path in localStorage + message prefix
5. **Coach tool** — `pin_mastery_path` registers on API boot

## Tear down

- `skills.json` skill records, `/api/dotcortex/skills*`, skill create form
- SkillScopeBanner tied to `?skill=`

Keep Library nav + pages.
