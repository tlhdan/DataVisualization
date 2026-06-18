import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
from map import (
    build_deck,
    stops_df,
    edges_df,
    routes_df,
    COMPANY_COLORS
)

st.set_page_config(layout="wide")

st.title("Hong Kong Bus Network Analytics Dashboard")

st.markdown("""<style> [data-testid="stMetricLabel"] { font-size: 4.2rem; } [data-testid="stMetricValue"] { font-size: 4.2rem; } </style> """, unsafe_allow_html=True)

# DATA
summary = pd.read_parquet("dataset/processed/summary.parquet")
data = pd.read_parquet("dataset/processed/data.parquet")
route = pd.read_parquet("dataset/processed/route.parquet")
fare = pd.read_parquet("dataset/processed/fare.parquet")
route_changes = pd.read_parquet("dataset/processed/route_changes.parquet")
stop_changes = pd.read_parquet("dataset/processed/stop_changes.parquet")
stop = pd.read_parquet("dataset/processed/stop.parquet")

df = summary.copy()
df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
df = df.sort_values("snapshot_date").reset_index(drop=True)

fare["snapshot_date"] = pd.to_datetime(fare["snapshot_date"])

latest_row = df.iloc[-1]

op_data = data[data["snapshot_date"] == df["snapshot_date"].max()].copy()

route_info = data.copy()
route_info["fare_per_minute"] = route_info["FULL_FARE"] / route_info["JOURNEY_TIME"]


# KPI + OP ROW
k, op_col = st.columns([1, 2])

COL_HEIGHT = 290

# KPIs
with k:

    with st.container(height=COL_HEIGHT):
    # ROUTES
        k1, k2, k3 = st.columns([1, 1, 1])

        with k1:
            st.metric("Routes", int(latest_row["routes"]))

            fig = px.line(
                df,
                x="snapshot_date",
                y="routes"
            )

            fig.update_traces(mode="lines")

            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    # STOPS
        with k2:
            st.metric("Stops", int(latest_row["stops"]))

            fig = px.line(
                df,
                x="snapshot_date",
                y="stops"
            )

            fig.update_traces(mode="lines")

            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    # AVG FARE
        with k3:
            st.metric(
                "Avg Fare (HKD)",
                round(latest_row["avg_route_fare"], 2)
            )

            fare_trend = (
                data.groupby("snapshot_date")["FULL_FARE"]
                .mean()
                .reset_index()
            )

            fig = px.line(
                fare_trend,
                x="snapshot_date",
                y="FULL_FARE"
            )

            fig.update_traces(mode="lines")

            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

# OP CHARTS
with op_col:
    with st.container(height=COL_HEIGHT):
        c1, c2, c3 = st.columns(3)

        # ROUTES
        with c1:
            op_counts = op_data["COMPANY_CODE"].value_counts().reset_index()
            op_counts.columns = ["Operator", "Routes"]

            fig = px.bar(
                op_counts,
                x="Routes",
                y="Operator",
                orientation="h",
                title="Routes by Operator",
                color="Operator",
                color_discrete_map={
                    op: f"rgb({c[0]},{c[1]},{c[2]})"
                    for op, c in COMPANY_COLORS.items()
                }
            )

            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
                xaxis_title=None,
                yaxis_title=None
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # FARE
        with c2:
            fig = px.box(
                route_info,
                x="COMPANY_CODE",
                y="FULL_FARE",
                color="COMPANY_CODE",
                color_discrete_map={
                    op: f"rgb({c[0]},{c[1]},{c[2]})"
                    for op, c in COMPANY_COLORS.items()
                },
                points=False,
                title="Fare by Operator (HKD)"
            )

            fig.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                height=200,
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        # FARE / MIN
        with c3:
            fig = px.box(
                route_info,
                x="COMPANY_CODE",
                y="fare_per_minute",
                color="COMPANY_CODE",
                color_discrete_map={
                    op: f"rgb({c[0]},{c[1]},{c[2]})"
                    for op, c in COMPANY_COLORS.items()
                },
                points=False,
                title="Fare/Min by Operator (HKD/min)"
            )
            
            fig.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                height=200,
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        legend_order = op_counts["Operator"].tolist()

        legend_df = (
            route[
                ["COMPANY_CODE", "COMPANY_NAME"]
            ]
            .drop_duplicates()
            .set_index("COMPANY_CODE")
            .loc[legend_order]
            .reset_index()
        )

        legend_cols = st.columns(10)

        for i, row in legend_df.iterrows():
            col = legend_cols[i // 1]

            color = COMPANY_COLORS.get(row["COMPANY_CODE"], [150, 150, 150])

            with col:
                st.markdown(
                    f"""
                    <div style="
                        line-height:1.0;
                        margin:0;
                        padding:0;
                        font-size:0.85rem;
                    ">
                        <span style="
                            color:rgb({color[0]},{color[1]},{color[2]});
                            font-size:20px;
                        ">■</span>
                        {row["COMPANY_NAME"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# SECOND ROW
PANEL_HEIGHT = 500

sel_col, map_col, temp_col = st.columns([2, 2, 2])

with sel_col:
    with st.container(height=PANEL_HEIGHT):
        route_timeline = route_changes.copy()

        route_timeline["routes_removed"] = (
            route_timeline["routes_removed"] * -1
        )

        fig = px.bar(
            route_timeline,
            x="snapshot_date",
            y=["routes_added", "routes_removed"],
            title="Route Additions vs Removals",
            color_discrete_sequence=[
                "#1f77b4",
                "#ff7f0e"
            ]
        )

        fig.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title=None,
            yaxis_title=None,
            legend_title_text=None,
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        stop_timeline = stop_changes.copy()

        stop_timeline["stops_added"] = stop_timeline["added"]
        stop_timeline["stops_removed"] = (
            -stop_timeline["removed"]
        )

        fig = px.bar(
            stop_timeline,
            x="snapshot_date",
            y=["stops_added", "stops_removed"],
            title="Stop Additions vs Removals",
            color_discrete_sequence=[
                "#1f77b4",
                "#ff7f0e"
            ]
        )

        fig.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title=None,
            yaxis_title=None,
            legend_title_text=None,
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

with temp_col:
    with st.container(height=260):

        # JOURNEY TIME DISTRIBUTION
        fig = px.histogram(
            route,
            x="JOURNEY_TIME",
            nbins=30,
            title="Journey Time Distribution"
        )

        fig.update_layout(
            height=240,
            xaxis_title="Journey Time (minutes)",
            yaxis_title=None,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.container(height=225):
        # WORST VALUE ROUTES
        route_plot = route.copy()

        route_plot["fare_per_min"] = (
            route_plot["FULL_FARE"] /
            route_plot["JOURNEY_TIME"]
        )

        worst_routes = (
            route_plot
            .nlargest(10, "fare_per_min")
            [
                [
                    "ROUTE_ID",
                    "ROUTE_NAMEE",
                    "COMPANY_CODE",
                    "fare_per_min",
                    "FULL_FARE",
                    "JOURNEY_TIME"
                ]
            ]
            .sort_values("fare_per_min")
            .copy()
        )

        worst_routes["route_label"] = (
            worst_routes["ROUTE_NAMEE"].astype(str)
            + " | "
            + worst_routes["ROUTE_ID"].astype(str)
        )

        worst_routes["display_name"] = (
            worst_routes["ROUTE_NAMEE"]
            .astype(str)
            .apply(lambda x: (x[:10] + "...") if len(x) > 10 else x)
        )

        worst_routes["color"] = worst_routes["COMPANY_CODE"].apply(
            lambda c: COMPANY_COLORS.get(c, (150, 150, 150))
        )

        color_map = {
            code: f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
            for code, rgb in COMPANY_COLORS.items()
        }

        fig_worst_value = px.bar(
            worst_routes,
            x="fare_per_min",
            y="route_label",
            orientation="h",
            color="COMPANY_CODE",
            color_discrete_map=color_map,
            hover_data={
                "ROUTE_ID": True,
                "ROUTE_NAMEE": True,
                "COMPANY_CODE": True,
                "FULL_FARE": ":.2f",
                "JOURNEY_TIME": True,
                "fare_per_min": ":.3f",
            },
            labels={
                "fare_per_min": "Fare / Minute (HKD/min)",
                "route_label": "",
                "COMPANY_CODE": "Operator"
            },
            title="Most Expensive Routes per Minute"
        )

        fig_worst_value.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,   # keep clean (legend already elsewhere)
        )

        fig_worst_value.update_yaxes(
            tickmode="array",
            tickvals=worst_routes["route_label"],
            ticktext=worst_routes["display_name"]
        )

        fig_worst_value.update_xaxes(
            tickformat=".2f"
        )

        st.plotly_chart(
            fig_worst_value,
            use_container_width=True
        )

# MAP
with map_col:
    with st.container(height=PANEL_HEIGHT):

        control_col1, control_col2 = st.columns([1.1, 3.9])

        with control_col1:
            mode = st.radio(
                "Explore Mode",
                ["Route", "Stop"],
                horizontal=False
            )

        selected_companies = routes_df["COMPANY_CODE"].unique()

        with control_col2:
            if mode == "Route":
                selected_companies = st.multiselect(
                    "Operators",
                    routes_df["COMPANY_CODE"].unique(),
                    default=list(routes_df["COMPANY_CODE"].unique())
                )

        deck = build_deck(
            stops_df,
            edges_df,
            routes_df,
            mode,
            selected_companies
        )

        st.pydeck_chart(
            deck,
            use_container_width=True,
            height=350,
            key="map"
        )