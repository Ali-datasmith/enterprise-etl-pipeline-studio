"""Observability helpers and dashboard plot generation."""

from typing import Any

import plotly.graph_objects as go
import pydeck as pdk

from etl.constants import COLOR_ACCENT
from etl.models import LineageRecord, QualityReport, RunMetadata


def create_stage_duration_chart(run_meta: RunMetadata | None) -> go.Figure:
    fig = go.Figure()

    if not run_meta or not run_meta.stage_metrics:
        fig.update_layout(
            title="Stage Durations (No Data Available)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#FFFFFF"},
        )
        return fig

    stages = list(run_meta.stage_metrics.keys())
    durations = [m.get("duration_seconds", 0.0) for m in run_meta.stage_metrics.values()]

    fig.add_trace(
        go.Bar(
            x=stages,
            y=durations,
            marker_color=COLOR_ACCENT,
            hovertemplate="Stage: %{x}<br>Duration: %{y:.3f}s<extra></extra>",
        )
    )

    fig.update_layout(
        title="Pipeline Stage Execution Durations (seconds)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
        xaxis={"title": "Stage", "gridcolor": "rgba(255,255,255,0.1)"},
        yaxis={"title": "Duration (s)", "gridcolor": "rgba(255,255,255,0.1)"},
    )
    return fig


def create_quality_score_gauge(quality_report: QualityReport | None) -> go.Figure:
    score = quality_report.quality_score if quality_report else 0.0

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Quality Score", "font": {"color": "#FFFFFF", "size": 18}},
            number={"suffix": "/100", "font": {"color": "#FFFFFF"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#FFFFFF"},
                "bar": {"color": COLOR_ACCENT},
                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 1,
                "bordercolor": "rgba(255,255,255,0.2)",
                "steps": [
                    {"range": [0, 50], "color": "rgba(248, 113, 113, 0.3)"},
                    {"range": [50, 80], "color": "rgba(251, 191, 36, 0.3)"},
                    {"range": [80, 100], "color": "rgba(52, 211, 153, 0.3)"},
                ],
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin={"t": 30, "b": 10, "l": 20, "r": 20},
    )
    return fig


def create_sankey_lineage_chart(records: list[LineageRecord]) -> go.Figure:
    fig = go.Figure()

    if not records:
        fig.update_layout(
            title="Lineage Sankey Flow (No Data)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#FFFFFF"},
        )
        return fig

    labels: list[str] = []
    label_map: dict[str, int] = {}

    def get_node_id(name: str) -> int:
        if name not in label_map:
            label_map[name] = len(labels)
            labels.append(name)
        return label_map[name]

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []

    for rec in records:
        src_id = get_node_id(rec.input_artifact)
        tgt_id = get_node_id(rec.output_artifact)
        val = rec.row_count_out or rec.row_count_in or 10
        sources.append(src_id)
        targets.append(tgt_id)
        values.append(max(1, val))

    fig.add_trace(
        go.Sankey(
            node={
                "pad": 15,
                "thickness": 20,
                "line": {"color": "black", "width": 0.5},
                "label": labels,
                "color": COLOR_ACCENT,
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": "rgba(0, 229, 255, 0.3)",
            },
        )
    )

    fig.update_layout(
        title="Dataset Lineage Flow",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
    )
    return fig


def create_geospatial_map(data: list[dict[str, Any]]) -> pdk.Deck:
    if not data:
        view_state = pdk.ViewState(latitude=37.7749, longitude=-122.4194, zoom=3, pitch=0)
        return pdk.Deck(layers=[], initial_view_state=view_state, map_style="dark")

    valid_points: list[dict[str, Any]] = []
    for row in data:
        lat = row.get("latitude") or row.get("lat")
        lon = row.get("longitude") or row.get("lon") or row.get("long")
        if lat is not None and lon is not None:
            try:
                valid_points.append(
                    {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "info": str(row.get("name") or row.get("_row_id") or "Record"),
                    }
                )
            except (ValueError, TypeError):
                continue

    if not valid_points:
        view_state = pdk.ViewState(latitude=37.7749, longitude=-122.4194, zoom=3, pitch=0)
        return pdk.Deck(layers=[], initial_view_state=view_state, map_style="dark")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=valid_points,
        get_position="[longitude, latitude]",
        get_color="[0, 229, 255, 200]",
        get_radius=50000,
        pickable=True,
    )

    avg_lat = sum(float(p["latitude"]) for p in valid_points) / len(valid_points)
    avg_lon = sum(float(p["longitude"]) for p in valid_points) / len(valid_points)

    view_state = pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=4, pitch=0)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"text": "{info}\nLat: {latitude}, Lon: {longitude}"},
    )
