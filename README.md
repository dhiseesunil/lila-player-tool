# LILA Player Journey Visualization Tool

Interactive Streamlit tool for exploring player movement, bot behavior, loot distribution, combat events, storm deaths, and heatmaps across the LILA BLACK gameplay dataset.

## What This Tool Does

- renders player and bot journeys on the correct minimap
- filters by map, date, and match
- distinguishes humans and bots
- shows discrete event icons for:
  - `Kill`
  - `Killed`
  - `BotKill`
  - `BotKilled`
  - `Loot`
  - `KilledByStorm`
- provides cumulative timeline playback with:
  - play / pause
  - previous / next
  - manual scrubbing
- provides heatmaps for:
  - traffic
  - kills
  - deaths
- supports heatmap aggregation across multiple matches and multiple dates on the same map

## Project Files

- `app.py`: main Streamlit app
- `requirements.txt`: Python dependencies
- `ARCHITECTURE.md`: architecture, tradeoffs, and design decisions
- `INSIGHTS.md`: gameplay and level-design findings
- `DATASET_README.md`: preserved original dataset reference

## Expected Folder Structure

```text
app.py
requirements.txt
ARCHITECTURE.md
INSIGHTS.md
DATASET_README.md
player_data/
minimaps/
event_icons/
```

## Local Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Usage

1. Select a map, date, and match.
2. Optionally filter to matches with bots, multiple humans, or storm events.
3. Choose whether to show humans, bots, or both.
4. Filter movement and discrete event types.
5. Enable one or more heatmap overlays.
6. Use the timeline controls below the map to step through the match over time.

## Data Notes

- source files are parquet, even though they do not use a `.parquet` extension
- `event` values are decoded from bytes
- bot detection is based on filename prefix:
  - UUID prefix = human
  - numeric prefix = bot
- minimap plotting uses `x` and `z` coordinates
- match playback is based on `ts`, treated as elapsed match time

## Deliverables Included

- interactive visualization tool
- architecture document
- insights document
- preserved dataset reference

## Dataset Reference

The original dataset documentation has been preserved in [DATASET_README.md](DATASET_README.md).

## Future Improvements

- deploy to a public hosted URL
- export screenshots for design reviews
- add preset analysis views for common level-design questions
- improve caching for larger aggregated heatmap scopes
