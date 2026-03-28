# Architecture

## Stack

- `Python + Streamlit`: fastest path to a usable internal tool with strong iteration speed for filtering, visualization, and deployment.
- `PyArrow + Pandas`: reads the parquet files directly and makes it easy to transform event rows for plotting.
- `Plotly`: supports layered map rendering, paths, markers, heatmap overlays, and interactive hover behavior inside Streamlit.
- `Pillow`: used for minimap assets and event icon handling.

This stack was chosen for speed of execution and clarity over frontend complexity. The audience is Level Design, so the priority was a shareable analysis tool rather than a heavily custom web client.

## Data Flow

1. On startup, the app scans `player_data/` and builds a match index from filenames and the `map_id` column.
2. Filename parsing classifies each file as human or bot:
   - UUID prefix = human
   - numeric prefix = bot
3. For the selected filters, the app loads the relevant parquet files with PyArrow and concatenates them into a single dataframe.
4. The app decodes the `event` byte column into readable event names and derives:
   - `is_bot`
   - `match_time_ms`
   - minimap `pixel_x` / `pixel_y`
5. The dataframe is then sliced for:
   - selected movement/event filters
   - selected timeline position
   - selected heatmap scope
6. Plotly renders:
   - minimap background
   - human/bot paths
   - event icons
   - heatmap overlays

## Coordinate Mapping

The source data provides world coordinates in `x`, `y`, `z`. For top-down minimap rendering, only `x` and `z` are used.

Per the README:

```text
u = (x - origin_x) / scale
v = (z - origin_z) / scale

pixel_x = u * 1024
pixel_y = (1 - v) * 1024
```

Map-specific constants:

| Map | Scale | Origin X | Origin Z |
|---|---:|---:|---:|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

The Y flip is required because minimap images use top-left image origin while the game-space conversion is bottom-up.

## Assumptions

- A single selected match is the primary unit for path playback and event inspection.
- Bot detection by filename prefix is treated as the source of truth.
- Some matches may include bot-related events without a large visible bot presence in the selected scope; the app reflects file-based participant presence and event-based activity separately.

## Tradeoffs

| Decision | Why | Tradeoff |

| Streamlit instead of React/custom frontend | Faster build and iteration | Less control over highly custom UI and animation |
| In-memory dataframe processing | Simple implementation for dataset size | Not ideal for much larger datasets |
| Pre-index from filenames + light parquet reads | Keeps load time reasonable | Still requires scanning all files at startup |
| Plotly layered rendering | Good balance of speed and interactivity | Layer ordering with icons/heatmaps requires workarounds |
| Timeline as stepwise playback | Easy to understand and demo | Less smooth than a fully custom canvas animation |

## With More Time

- Add metrics using the available event data for better understanding.
- Deeper understanding of human behavior interms of map location, events .etc.
- Add stronger map annotations, extraction zones, and named hotspots.
- Add screenshot/export support for insights and design reviews.
- Use of React instead of Streamlit for better experience and performance.
