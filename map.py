import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np

@st.cache_data
def load_stops():
    return pd.read_parquet("dataset/processed/stop.parquet")

@st.cache_data
def load_edges():
    return pd.read_parquet("dataset/processed/edge.parquet")

@st.cache_data
def load_routes():
    return pd.read_parquet("dataset/processed/route.parquet")

stops_df = load_stops()
edges_df = load_edges()
routes_df = load_routes()

COMPANY_COLORS = {
    "KMB": [0, 114, 178, 220],
    "KMB+CTB": [86, 180, 233, 220],
    "LWB": [0, 158, 115, 220],
    "CTB": [204, 121, 167, 220],
    "LWB+CTB": [213, 94, 0, 220],
    "NLB": [240, 228, 66, 220],
    "LRTFeeder": [102, 102, 102, 220],
    "XB": [51, 34, 136, 220],
    "DB": [17, 119, 51, 220],
    "PI": [136, 34, 85, 220],
}


def build_deck(
    stops_df,
    edges_df,
    routes_df,
    mode,
    selected_companies
):

    edges_render = edges_df.copy()

    # FILTER (Route mode only)
    if mode == "Route":
        if selected_companies:
            edges_render = edges_render[
                edges_render["companies"].apply(
                    lambda x: len(set(x) & set(selected_companies)) > 0
                )
            ]
        else:
            edges_render = edges_render.iloc[0:0]

    # EDGE GEOMETRY
    if len(edges_render) > 0:
        edges_render["path"] = edges_render.apply(
            lambda r: [
                [r["from_stop_coords"][1], r["from_stop_coords"][0]],
                [r["to_stop_coords"][1], r["to_stop_coords"][0]],
            ],
            axis=1
        )
    else:
        edges_render["path"] = pd.Series(dtype="object")

    # COLOR SYSTEMS

    # Stop mode
    def degree_color(rc):
        max_rc = edges_render["route_count"].max() if len(edges_render) > 0 else 1
        intensity = np.log1p(rc) / np.log1p(max_rc + 1e-6)

        return [
            0,
            int(80 + 150 * intensity),
            255,
            int(60 + 180 * intensity)
        ]

    edges_render["degree_color"] = edges_render["route_count"].apply(degree_color)

    # Route mode
    def blend_companies(companies):
        colors = [
            COMPANY_COLORS[c][:3]
            for c in companies
            if c in COMPANY_COLORS
        ]

        if not colors:
            return [120, 120, 120, 220]

        rgb = np.mean(colors, axis=0)
        return [int(rgb[0]), int(rgb[1]), int(rgb[2]), 220]

    edges_render["company_color"] = edges_render["companies"].apply(blend_companies)

    # EDGE STYLE SWITCH
    if mode == "Stop":
        edges_render["color"] = edges_render["degree_color"]
        edges_render["width"] = 1

    elif mode == "Route":
        edges_render["color"] = edges_render["company_color"]
        edges_render["width"] = 1

    # STOP STYLE
    stops_render = stops_df.copy()

    max_degree = stops_df["degree"].max()

    stops_render["radius"] = (
        50 + (np.log1p(stops_df["degree"]) / np.log1p(max_degree)) * 50
    )

    stops_render["color"] = [[255, 140, 0, 160]] * len(stops_render)

    # VIEW
    if mode == "Route" and len(edges_render) > 0:
        coords = stops_df[stops_df["STOP_ID"].isin(
            edges_df["from_stop"].tolist() + edges_df["to_stop"].tolist()
        )]

        view_state = pdk.ViewState(
            latitude=coords["lat"].mean(),
            longitude=coords["lon"].mean(),
            zoom=9,
            pitch=0
        )
    else:
        view_state = pdk.ViewState(
            latitude=stops_df["lat"].mean(),
            longitude=stops_df["lon"].mean(),
            zoom=9,
            pitch=0
        )

    # LAYERS
    edge_layer = pdk.Layer(
        "PathLayer",
        data=edges_render,
        get_path="path",
        get_color="color",
        get_width="width",
        width_min_pixels=1,
        pickable=False
    )

    stop_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stops_render,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="color",
        pickable=False
    )

    return pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[edge_layer, stop_layer]
    )