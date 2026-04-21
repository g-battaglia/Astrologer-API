# Astrologer API — Claude Code Skill

Agentic coding assistant skill for building apps with the Astrologer API.

## Install

### Claude Code (project-level)

```bash
mkdir -p .claude/skills
curl -fsSL https://kerykeion.net/skills/astrologer-api/SKILL.md \
  -o .claude/skills/astrologer-api.md
```

### Claude Code (user-level, all projects)

```bash
mkdir -p ~/.claude/skills
curl -fsSL https://kerykeion.net/skills/astrologer-api/SKILL.md \
  -o ~/.claude/skills/astrologer-api.md
```

### Other agentic tools

Drop `SKILL.md` into your agent's skill/tool/rule directory. Works with any system that reads markdown-based skill files.

## Use

Once installed, ask your agent:

- "Build a natal chart endpoint in my Flask app"
- "Add relationship compatibility to my dating app using the Astrologer API"
- "Generate an AI-powered horoscope reader"
- "Render a synastry chart as SVG in my React frontend"

The agent picks up auth headers, endpoint routing, subject schema, and common pitfalls automatically.

## What's inside

- Base URL + auth pattern
- Endpoint decision matrix (data vs charts vs context vs moon)
- Subject schema with defaults
- Python + TypeScript client templates
- LLM integration pattern (`/context/*` endpoints)
- House systems + zodiac types reference
- Common mistakes to avoid
- Pricing + subscription link

## Updates

Pull latest:

```bash
curl -fsSL https://kerykeion.net/skills/astrologer-api/SKILL.md \
  -o ~/.claude/skills/astrologer-api.md
```
