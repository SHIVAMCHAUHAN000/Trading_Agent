# Stage 10 — Research dashboard

Each full research run writes:

| File | Layer |
|---|---|
| `SIMPLE_REPORT.md` | Decision / plain language |
| `research_report.json` | Full technical audit |
| `dashboard.html` | Visual summary |

## Render manually

```powershell
python scripts/render_dashboard.py path\to\research_report.json
```

Open `dashboard.html` in a browser.
