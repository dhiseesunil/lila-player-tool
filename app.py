from __future__ import annotations

import base64
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq
import streamlit as st
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
PLAYER_DATA_DIR = BASE_DIR / "player_data"
MINIMAP_DIR = BASE_DIR / "minimaps"
EVENT_ICON_DIR = BASE_DIR / "event_icons"

MAP_CONFIG = {
    "AmbroseValley": {
        "scale": 900,
        "origin_x": -370,
        "origin_z": -473,
        "minimap": MINIMAP_DIR / "AmbroseValley_Minimap.png",
    },
    "GrandRift": {
        "scale": 581,
        "origin_x": -290,
        "origin_z": -290,
        "minimap": MINIMAP_DIR / "GrandRift_Minimap.png",
    },
    "Lockdown": {
        "scale": 1000,
        "origin_x": -500,
        "origin_z": -500,
        "minimap": MINIMAP_DIR / "Lockdown_Minimap.jpg",
    },
}

EVENT_COLORS = {
    "Position": "#1677ff",
    "BotPosition": "#fa8c16",
    "Kill": "#ff4d4f",
    "Killed": "#8b0000",
    "BotKill": "#ff7a45",
    "BotKilled": "#ad6800",
    "Loot": "#36cfc9",
    "KilledByStorm": "#9254de",
}

MOVEMENT_EVENTS = ["Position", "BotPosition"]
DISCRETE_EVENTS = ["Kill", "Killed", "BotKill", "BotKilled", "Loot", "KilledByStorm"]
ALL_EVENT_TYPES = MOVEMENT_EVENTS + DISCRETE_EVENTS
HEATMAP_EVENT_SETS = {
    "None": [],
    "Traffic heatmap": ["Position", "BotPosition"],
    "Kill heatmap": ["Kill", "BotKill"],
    "Death heatmap": ["Killed", "BotKilled", "KilledByStorm"],
}


def transparent_colorscale(color: str) -> list[list[object]]:
    return [
        [0.0, "rgba(0,0,0,0)"],
        [0.05, "rgba(0,0,0,0)"],
        [0.18, "rgba(0,0,0,0.10)"],
        [1.0, color],
    ]


HEATMAP_COLORSCALES = {
    "Traffic heatmap": transparent_colorscale("rgba(22,119,255,0.95)"),
    "Kill heatmap": transparent_colorscale("rgba(255,77,79,0.98)"),
    "Death heatmap": transparent_colorscale("rgba(146,84,222,0.98)"),
}
HEATMAP_LEGEND_COLORS = {
    "Traffic heatmap": "rgba(22,119,255,0.55)",
    "Kill heatmap": "rgba(255,77,79,0.60)",
    "Death heatmap": "rgba(146,84,222,0.60)",
}
HEATMAP_RGB = {
    "Traffic heatmap": (22, 119, 255),
    "Kill heatmap": (255, 77, 79),
    "Death heatmap": (146, 84, 222),
}
EVENT_SYMBOLS = {
    "Position": "━━",
    "BotPosition": "┅┅",
    "Kill": "◆",
    "Killed": "◆",
    "BotKill": "◆",
    "BotKilled": "◆",
    "Loot": "◆",
    "KilledByStorm": "◆",
}
EVENT_ICON_FILES = {
    "Loot": EVENT_ICON_DIR / "Loot.png",
    "KilledByStorm": EVENT_ICON_DIR / "KilledByStorm.png",
    "Killed": EVENT_ICON_DIR / "Killed.png",
    "Kill": EVENT_ICON_DIR / "Kill.png",
    "BotKilled": EVENT_ICON_DIR / "BotKilled.png",
    "BotKill": EVENT_ICON_DIR / "BotKill.png",
}


def blur_density(grid: np.ndarray) -> np.ndarray:
    kernel = np.array(
        [
            [1, 2, 3, 2, 1],
            [2, 4, 6, 4, 2],
            [3, 6, 9, 6, 3],
            [2, 4, 6, 4, 2],
            [1, 2, 3, 2, 1],
        ],
        dtype=float,
    )
    kernel /= kernel.sum()
    padded = np.pad(grid, ((2, 2), (2, 2)), mode="constant")
    blurred = np.zeros_like(grid, dtype=float)

    for row in range(grid.shape[0]):
        for col in range(grid.shape[1]):
            window = padded[row : row + 5, col : col + 5]
            blurred[row, col] = float((window * kernel).sum())

    return blurred


@st.cache_data(show_spinner=False)
def icon_data_url(event_name: str) -> str:
    icon_path = EVENT_ICON_FILES[event_name]
    encoded = base64.b64encode(icon_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


@st.cache_data(show_spinner=False)
def load_event_icon(event_name: str) -> Image.Image:
    icon = Image.open(EVENT_ICON_FILES[event_name]).convert("RGBA")
    icon.thumbnail((140, 140))
    return icon


def legend_symbol_html(event_name: str) -> str:
    if event_name in EVENT_ICON_FILES:
        return (
            f"<img src='{icon_data_url(event_name)}' "
            "style='width:24px;height:24px;vertical-align:middle;object-fit:contain;' />"
        )

    if event_name == "Human paths":
        return (
            "<span style='display:inline-block;width:34px;height:0;"
            "border-top:4px solid #1677ff;border-radius:999px;vertical-align:middle;'></span>"
        )

    if event_name == "Bot paths":
        return (
            "<span style='display:inline-block;width:34px;height:0;"
            "border-top:4px dashed #fa8c16;border-radius:999px;vertical-align:middle;'></span>"
        )

    return (
        "<span style='display:inline-block;width:12px;height:12px;"
        "border-radius:999px;background:#94a3b8;vertical-align:middle;'></span>"
    )


def build_heatmap_overlay_image(density: np.ndarray, heatmap_mode: str) -> Image.Image:
    normalized = density.copy()
    if np.nanmax(normalized) > 0:
        normalized = normalized / np.nanmax(normalized)
    normalized = np.nan_to_num(normalized, nan=0.0)

    r, g, b = HEATMAP_RGB[heatmap_mode]
    alpha = np.clip((normalized ** 0.7) * 235, 0, 235).astype(np.uint8)

    rgba = np.zeros((normalized.shape[0], normalized.shape[1], 4), dtype=np.uint8)
    rgba[..., 0] = r
    rgba[..., 1] = g
    rgba[..., 2] = b
    rgba[..., 3] = alpha

    image = Image.fromarray(rgba, mode="RGBA")
    return image.resize((1024, 1024), Image.Resampling.BILINEAR)


def is_bot_user(user_id: object) -> bool:
    return str(user_id).isdigit()


def decode_event(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def match_time_ms(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return (series - pd.Timestamp("1970-01-01")) // pd.Timedelta(milliseconds=1)
    return pd.to_numeric(series, errors="coerce")


def world_to_minimap(df: pd.DataFrame, map_id: str) -> pd.DataFrame:
    cfg = MAP_CONFIG[map_id]
    u = (df["x"] - cfg["origin_x"]) / cfg["scale"]
    v = (df["z"] - cfg["origin_z"]) / cfg["scale"]
    df["pixel_x"] = u * 1024
    df["pixel_y"] = (1 - v) * 1024
    return df


@st.cache_data(show_spinner=False)
def build_match_index() -> pd.DataFrame:
    records: list[dict[str, str]] = []

    for day_dir in sorted(PLAYER_DATA_DIR.iterdir()):
        if not day_dir.is_dir() or day_dir.name.startswith("."):
            continue

        for file_path in sorted(day_dir.iterdir()):
            if not file_path.is_file():
                continue

            parts = file_path.name.split("_", 1)
            user_id = parts[0]
            match_name = parts[1] if len(parts) > 1 else ""
            match_id = match_name.removesuffix(".nakama-0")

            table = pq.read_table(file_path, columns=["map_id"]).slice(0, 1)
            map_id = table.column("map_id")[0].as_py()

            records.append(
                {
                    "date": day_dir.name,
                    "map_id": map_id,
                    "match_id": match_id,
                    "file_path": str(file_path),
                    "user_id": user_id,
                }
            )

    index_df = pd.DataFrame(records)
    if index_df.empty:
        return index_df

    index_df["is_bot"] = index_df["user_id"].map(is_bot_user)
    return index_df


def build_match_summary(index_df: pd.DataFrame) -> pd.DataFrame:
    if index_df.empty:
        return index_df

    summary = (
        index_df.groupby(["date", "map_id", "match_id"], as_index=False)
        .agg(
            human_files=("is_bot", lambda s: int((~s).sum())),
            bot_files=("is_bot", lambda s: int(s.sum())),
            total_files=("file_path", "count"),
        )
        .sort_values(["date", "map_id", "match_id"])
        .reset_index(drop=True)
    )
    summary["match_label"] = summary.apply(
        lambda row: f"{row['match_id']} (H:{row['human_files']} B:{row['bot_files']})",
        axis=1,
    )
    summary["date_match_label"] = summary.apply(
        lambda row: f"{row['date']} | {row['match_id']} (H:{row['human_files']} B:{row['bot_files']})",
        axis=1,
    )
    return summary


@st.cache_data(show_spinner=False)
def build_match_event_flags(index_df: pd.DataFrame) -> pd.DataFrame:
    flags: list[dict[str, object]] = []

    for (date, match_id), group in index_df.groupby(["date", "match_id"], sort=False):
        has_storm = False
        for file_path in group["file_path"]:
            table = pq.read_table(file_path, columns=["event"])
            events = table.column("event").to_pylist()
            if any(decode_event(event) == "KilledByStorm" for event in events):
                has_storm = True
                break

        flags.append(
            {
                "date": date,
                "match_id": match_id,
                "has_storm": has_storm,
            }
        )

    return pd.DataFrame(flags)


@st.cache_data(show_spinner=False)
def load_match_data(file_paths: tuple[str, ...]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for file_path in file_paths:
        table = pq.read_table(file_path)
        frame = table.to_pandas()
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["event_name"] = df["event"].map(decode_event)
    df["is_bot"] = df["user_id"].map(is_bot_user)
    df["match_time_ms"] = match_time_ms(df["ts"])
    df = df.sort_values(["match_time_ms", "user_id"]).reset_index(drop=True)
    df = world_to_minimap(df, str(df["map_id"].iloc[0]))
    return df


def build_figure(
    match_df: pd.DataFrame,
    heatmap_df_source: pd.DataFrame,
    map_id: str,
    selected_movement_events: list[str],
    selected_discrete_events: list[str],
    selected_heatmap_modes: list[str],
) -> go.Figure:
    minimap = Image.open(MAP_CONFIG[map_id]["minimap"])
    fig = go.Figure()

    fig.add_layout_image(
        dict(
            source=minimap,
            x=0,
            y=0,
            sizex=1024,
            sizey=1024,
            xref="x",
            yref="y",
            layer="below",
        )
    )

    position_df = match_df[match_df["event_name"].isin(selected_movement_events)]
    shown_path_legend: set[bool] = set()
    for (user_id, is_bot), player_df in position_df.groupby(["user_id", "is_bot"], sort=False):
        legend_name = "Bot paths" if is_bot else "Human paths"
        fig.add_trace(
            go.Scatter(
                x=player_df["pixel_x"],
                y=player_df["pixel_y"],
                mode="lines",
                line={
                    "width": 2,
                    "color": "#fa8c16" if is_bot else "#1677ff",
                    "dash": "dot" if is_bot else "solid",
                },
                name=legend_name,
                legendgroup=legend_name,
                showlegend=is_bot not in shown_path_legend,
                hovertemplate=(
                    f"user_id={user_id}<br>"
                    "event=%{customdata[0]}<br>"
                    "time_ms=%{customdata[1]}<extra></extra>"
                ),
                customdata=player_df[["event_name", "match_time_ms"]],
            )
        )
        shown_path_legend.add(is_bot)

    event_df = match_df[match_df["event_name"].isin(selected_discrete_events)]
    for event_name, filtered_df in event_df.groupby("event_name", sort=False):
        fig.add_trace(
            go.Scatter(
                x=filtered_df["pixel_x"],
                y=filtered_df["pixel_y"],
                mode="markers",
                marker={
                    "size": 20,
                    "color": EVENT_COLORS[event_name],
                    "symbol": "circle",
                    "opacity": 0.01,
                    "line": {"width": 0, "color": EVENT_COLORS[event_name]},
                },
                name=event_name,
                legendgroup=event_name,
                hovertemplate=(
                    "event=%{customdata[0]}<br>"
                    "user_id=%{customdata[1]}<br>"
                    "time_ms=%{customdata[2]}<extra></extra>"
                ),
                customdata=filtered_df[["event_name", "user_id", "match_time_ms"]],
            )
        )
        if event_name in EVENT_ICON_FILES:
            icon_image = load_event_icon(event_name)
            for row in filtered_df.itertuples():
                fig.add_layout_image(
                    dict(
                        source=icon_image,
                        x=row.pixel_x,
                        y=row.pixel_y,
                        sizex=90,
                        sizey=90,
                        xref="x",
                        yref="y",
                        xanchor="center",
                        yanchor="middle",
                        layer="above",
                    )
                )

    for heatmap_mode in selected_heatmap_modes:
        heatmap_events = HEATMAP_EVENT_SETS[heatmap_mode]
        heatmap_df = heatmap_df_source[heatmap_df_source["event_name"].isin(heatmap_events)]
        if heatmap_df.empty:
            continue

        x_bins = np.linspace(0, 1024, 85)
        y_bins = np.linspace(0, 1024, 85)
        density, _, _ = np.histogram2d(
            heatmap_df["pixel_y"],
            heatmap_df["pixel_x"],
            bins=[y_bins, x_bins],
        )
        density = blur_density(density)
        if np.nanmax(density) > 0:
            density = density / np.nanmax(density)
        density = np.where(density > 0.02, density, 0.0)
        overlay_image = build_heatmap_overlay_image(density, heatmap_mode)
        fig.add_layout_image(
            dict(
                source=overlay_image,
                x=0,
                y=0,
                sizex=1024,
                sizey=1024,
                xref="x",
                yref="y",
                layer="above",
            )
        )

    fig.update_xaxes(range=[0, 1024], visible=False)
    fig.update_yaxes(range=[1024, 0], visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        height=850,
        showlegend=False,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "xanchor": "left",
            "itemsizing": "constant",
            "tracegroupgap": 12,
            "font": {"size": 13},
            "groupclick": "togglegroup",
        },
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="LILA Match Viewer", layout="wide")
    st.title("LILA Match Viewer")
    st.caption("Explore one match at a time by map, date, and match ID.")

    if not PLAYER_DATA_DIR.exists():
        st.error(f"Missing data directory: {PLAYER_DATA_DIR}")
        return

    if not MINIMAP_DIR.exists():
        st.error(f"Missing minimap directory: {MINIMAP_DIR}")
        return

    with st.spinner("Indexing match files..."):
        index_df = build_match_index()
        match_summary_df = build_match_summary(index_df)
        match_event_flags_df = build_match_event_flags(index_df)

    if not match_event_flags_df.empty:
        match_summary_df = match_summary_df.merge(
            match_event_flags_df,
            on=["date", "match_id"],
            how="left",
        )
        match_summary_df["has_storm"] = match_summary_df["has_storm"].fillna(False)

    if index_df.empty:
        st.warning("No match files were found.")
        return

    st.sidebar.header("Filters")

    def apply_match_filters(summary_df: pd.DataFrame) -> pd.DataFrame:
        filtered = summary_df.copy()
        if only_matches_with_bots:
            filtered = filtered[filtered["bot_files"] > 0]
        if only_matches_with_multiple_humans:
            filtered = filtered[filtered["human_files"] > 1]
        if only_matches_with_storm:
            filtered = filtered[filtered["has_storm"]]
        return filtered

    available_maps = sorted(index_df["map_id"].unique().tolist())
    selected_map = st.sidebar.selectbox("Map", available_maps)

    map_filtered = index_df[index_df["map_id"] == selected_map]
    map_summary = match_summary_df[match_summary_df["map_id"] == selected_map]
    available_dates = sorted(map_filtered["date"].unique().tolist())
    selected_date = st.sidebar.selectbox("Date", available_dates)
    only_matches_with_bots = st.sidebar.checkbox("Only matches with bots", value=False)
    only_matches_with_multiple_humans = st.sidebar.checkbox(
        "Only matches with multiple humans", value=False
    )
    only_matches_with_storm = st.sidebar.checkbox("Only matches with storm", value=False)

    date_filtered = map_filtered[map_filtered["date"] == selected_date]
    date_summary = apply_match_filters(map_summary[map_summary["date"] == selected_date].copy())

    if date_summary.empty:
        st.warning("No matches found for the current filters.")
        return

    selected_match_label = st.sidebar.selectbox("Match", date_summary["match_label"].tolist())
    selected_match = date_summary.loc[
        date_summary["match_label"] == selected_match_label, "match_id"
    ].iloc[0]
    entity_mode = st.sidebar.radio("Show", ["Both", "Humans only", "Bots only"], index=0)

    selected_rows = date_filtered[date_filtered["match_id"] == selected_match]
    if entity_mode == "Humans only":
        visible_rows = selected_rows[~selected_rows["is_bot"]]
    elif entity_mode == "Bots only":
        visible_rows = selected_rows[selected_rows["is_bot"]]
    else:
        visible_rows = selected_rows

    file_paths = tuple(visible_rows["file_path"].tolist())

    with st.spinner("Loading selected match..."):
        match_df = load_match_data(file_paths)

    if match_df.empty:
        st.warning(f"No rows found for '{entity_mode}' in the selected match.")
        return

    st.sidebar.subheader("Movement")
    selected_movement_events = st.sidebar.multiselect(
        "Movement events",
        MOVEMENT_EVENTS,
        default=MOVEMENT_EVENTS,
    )
    st.sidebar.subheader("Events")
    selected_discrete_events = st.sidebar.multiselect(
        "Discrete events",
        DISCRETE_EVENTS,
        default=DISCRETE_EVENTS,
    )
    selected_heatmap_modes = st.sidebar.multiselect(
        "Heatmap overlays",
        [mode for mode in HEATMAP_EVENT_SETS if mode != "None"],
        default=[],
    )

    heatmap_df_source = match_df
    heatmap_scope_description = "Heatmaps use the selected match."
    if selected_heatmap_modes:
        st.sidebar.subheader("Heatmap scope")
        heatmap_scope = st.sidebar.radio(
            "Heatmap data",
            ["Selected match only", "Multiple matches / days"],
            index=0,
        )
        if heatmap_scope == "Multiple matches / days":
            available_heatmap_dates = sorted(map_summary["date"].unique().tolist())
            selected_heatmap_dates = st.sidebar.multiselect(
                "Heatmap dates",
                available_heatmap_dates,
                default=[selected_date],
            )
            if not selected_heatmap_dates:
                st.warning("Select at least one heatmap date.")
                return

            heatmap_summary = apply_match_filters(
                map_summary[map_summary["date"].isin(selected_heatmap_dates)].copy()
            )
            if heatmap_summary.empty:
                st.warning("No heatmap matches found for the current heatmap filters.")
                return

            default_heatmap_labels = []
            current_label = date_summary.loc[
                date_summary["match_id"] == selected_match, "date_match_label"
            ]
            if not current_label.empty:
                default_heatmap_labels = [current_label.iloc[0]]

            selected_heatmap_match_labels = st.sidebar.multiselect(
                "Heatmap matches",
                heatmap_summary["date_match_label"].tolist(),
                default=default_heatmap_labels,
            )
            if not selected_heatmap_match_labels:
                st.warning("Select at least one heatmap match.")
                return

            selected_heatmap_summary = heatmap_summary[
                heatmap_summary["date_match_label"].isin(selected_heatmap_match_labels)
            ][["date", "match_id"]]

            heatmap_rows = map_filtered.merge(
                selected_heatmap_summary,
                on=["date", "match_id"],
                how="inner",
            )
            if entity_mode == "Humans only":
                heatmap_rows = heatmap_rows[~heatmap_rows["is_bot"]]
            elif entity_mode == "Bots only":
                heatmap_rows = heatmap_rows[heatmap_rows["is_bot"]]

            heatmap_file_paths = tuple(heatmap_rows["file_path"].tolist())
            with st.spinner("Loading heatmap scope data..."):
                heatmap_df_source = load_match_data(heatmap_file_paths)

            if heatmap_df_source.empty:
                st.warning("No heatmap rows found for the selected heatmap scope.")
                return

            heatmap_scope_description = (
                f"Heatmaps use {len(selected_heatmap_match_labels)} matches across "
                f"{len(selected_heatmap_dates)} date(s)."
            )

    visible_event_names = set(selected_movement_events + selected_discrete_events)
    filtered_match_df = match_df[match_df["event_name"].isin(visible_event_names)].copy()

    if filtered_match_df.empty:
        st.warning("No rows match the current movement/event filters.")
        return

    timeline_points = sorted(filtered_match_df["match_time_ms"].dropna().astype(int).unique().tolist())
    if not timeline_points:
        st.warning("No timeline points are available for the current filters.")
        return

    timeline_context_key = "|".join(
        [
            selected_map,
            selected_date,
            selected_match,
            entity_mode,
            ",".join(selected_movement_events),
            ",".join(selected_discrete_events),
        ]
    )
    if st.session_state.get("timeline_context_key") != timeline_context_key:
        st.session_state.timeline_context_key = timeline_context_key
        st.session_state.timeline_index = len(timeline_points) - 1
        st.session_state.timeline_playing = False

    current_timeline_index = int(
        min(max(st.session_state.get("timeline_index", len(timeline_points) - 1), 0), len(timeline_points) - 1)
    )
    current_timeline_ms = timeline_points[current_timeline_index]

    timeline_filtered_match_df = filtered_match_df[
        filtered_match_df["match_time_ms"] <= current_timeline_ms
    ].copy()
    if selected_heatmap_modes and heatmap_scope_description == "Heatmaps use the selected match.":
        heatmap_df_visible = heatmap_df_source[heatmap_df_source["match_time_ms"] <= current_timeline_ms].copy()
    else:
        heatmap_df_visible = heatmap_df_source

    if timeline_filtered_match_df.empty:
        st.warning("No rows fall inside the selected timeline range.")
        return

    total_human_count = selected_rows.loc[~selected_rows["is_bot"], "user_id"].nunique()
    total_bot_count = selected_rows.loc[selected_rows["is_bot"], "user_id"].nunique()
    visible_human_count = visible_rows.loc[~visible_rows["is_bot"], "user_id"].nunique()
    visible_bot_count = visible_rows.loc[visible_rows["is_bot"], "user_id"].nunique()
    event_count = len(timeline_filtered_match_df)

    summary_tiles = [
        ("Map", selected_map),
        ("Date", selected_date),
        ("Visible Humans / Bots", f"{visible_human_count} / {visible_bot_count}"),
        ("Event Rows", f"{event_count:,}"),
    ]
    summary_cols = st.columns(4)
    for index, (label, value) in enumerate(summary_tiles):
        with summary_cols[index]:
            st.markdown(
                f"""
                <div style="
                    background: #161b22;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 12px;
                    padding: 10px 12px;
                    margin-bottom: 10px;
                    min-height: 70px;
                ">
                    <div style="font-size:0.78rem; color:#d1d5db; font-weight:600;">
                        {label}
                    </div>
                    <div style="font-size:1.02rem; font-weight:650; color:white; margin-top:6px;">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    event_counts = (
        timeline_filtered_match_df["event_name"]
        .value_counts()
        .reindex(ALL_EVENT_TYPES, fill_value=0)
        .to_dict()
    )
    st.markdown("#### Event Summary")
    tile_cols = st.columns(4)
    for index, event_name in enumerate(ALL_EVENT_TYPES):
        with tile_cols[index % 4]:
            if event_name in EVENT_ICON_FILES:
                event_prefix = (
                    f"<img src='{icon_data_url(event_name)}' "
                    "style='width:52px;height:52px;vertical-align:middle;object-fit:contain;' />"
                )
            else:
                event_prefix = (
                    f"<span style='color:{EVENT_COLORS[event_name]}; font-weight:700; font-size:1.15rem;'>{EVENT_SYMBOLS[event_name]}</span>"
                )
            st.markdown(
                f"""
                <div style="
                    background: #161b22;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 12px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                    box-shadow: none;
                    min-height: 108px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div style="
                        font-size:0.82rem;
                        color:#d1d5db;
                        font-weight:600;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        gap:10px;
                        text-align:center;
                        line-height:1.15;
                    ">
                        <span style="display:inline-flex; align-items:center; justify-content:center; min-width:52px; min-height:52px;">{event_prefix}</span>
                        <span>{event_name}</span>
                    </div>
                    <div style="
                        font-size:1.2rem;
                        font-weight:700;
                        color:white;
                        margin-top:12px;
                        text-align:center;
                    ">
                        {event_counts[event_name]:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    legend_items = []
    if "Position" in selected_movement_events and visible_human_count > 0:
        legend_items.append("Human paths")
    if "BotPosition" in selected_movement_events and visible_bot_count > 0:
        legend_items.append("Bot paths")
    for event_name in selected_discrete_events:
        if event_counts.get(event_name, 0) > 0:
            legend_items.append(event_name)

    if legend_items:
        legend_html = "".join(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:6px 10px;
                background:#161b22;
                border:1px solid rgba(255,255,255,0.08);
                border-radius:999px;
            ">
                {legend_symbol_html(item)}
                <span style="color:#e5e7eb; font-size:0.92rem; font-weight:600;">{item}</span>
            </div>
            """
            for item in legend_items
        )
        st.markdown(
            f"""
            <div style="
                display:flex;
                flex-wrap:wrap;
                gap:10px;
                margin: 4px 0 12px 0;
            ">
                {legend_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.plotly_chart(
        build_figure(
            timeline_filtered_match_df,
            heatmap_df_visible,
            selected_map,
            selected_movement_events,
            selected_discrete_events,
            selected_heatmap_modes,
        ),
        use_container_width=True,
    )

    st.markdown("#### Timeline")
    timeline_cols = st.columns([1, 1, 1, 5])
    if timeline_cols[0].button("Previous", use_container_width=True):
        st.session_state.timeline_index = max(current_timeline_index - 1, 0)
        st.session_state.timeline_playing = False
        st.rerun()
    if timeline_cols[1].button(
        "Pause" if st.session_state.get("timeline_playing", False) else "Play",
        use_container_width=True,
    ):
        if st.session_state.get("timeline_playing", False):
            st.session_state.timeline_playing = False
        else:
            if current_timeline_index >= len(timeline_points) - 1:
                st.session_state.timeline_index = 0
            st.session_state.timeline_playing = True
        st.rerun()
    if timeline_cols[2].button("Next", use_container_width=True):
        st.session_state.timeline_index = min(current_timeline_index + 1, len(timeline_points) - 1)
        st.session_state.timeline_playing = False
        st.rerun()
    manual_time = timeline_cols[3].slider(
        "Match time (ms)",
        min_value=0,
        max_value=len(timeline_points) - 1,
        value=current_timeline_index,
        format="%d",
        label_visibility="collapsed",
    )
    if manual_time != current_timeline_index:
        st.session_state.timeline_index = manual_time
        st.session_state.timeline_playing = False
        st.rerun()

    st.caption(
        f"Frame {current_timeline_index + 1} of {len(timeline_points)} • Showing events up to {current_timeline_ms:,} ms"
    )

    if st.session_state.get("timeline_playing", False):
        if current_timeline_index < len(timeline_points) - 1:
            time.sleep(1.2)
            st.session_state.timeline_index = current_timeline_index + 1
            st.rerun()
        else:
            st.session_state.timeline_playing = False

    with st.expander("Human and bot files in this match", expanded=False):
        file_cols = st.columns(2)

        with file_cols[0]:
            st.subheader("Human files")
            human_files = selected_rows.loc[~selected_rows["is_bot"], "file_path"].tolist()
            if human_files:
                st.code("\n".join(human_files), language="text")
            else:
                st.caption("No human files in this match.")

        with file_cols[1]:
            st.subheader("Bot files")
            bot_files = selected_rows.loc[selected_rows["is_bot"], "file_path"].tolist()
            if bot_files:
                st.code("\n".join(bot_files), language="text")
            else:
                st.caption("No bot files in this match.")

    with st.expander("Selected match data"):
        visible_columns = [
            "user_id",
            "map_id",
            "event_name",
            "match_time_ms",
            "x",
            "y",
            "z",
            "pixel_x",
            "pixel_y",
            "is_bot",
        ]
        st.dataframe(timeline_filtered_match_df[visible_columns], use_container_width=True, height=320)


if __name__ == "__main__":
    main()
