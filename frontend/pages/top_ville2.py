import dash
from dash import html, dcc, Input, Output
import requests
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_URL", "http://localhost:8081")

dash.register_page(__name__, path="/top_ville2")

def get_map_figure(data, label_col):
    df = pd.DataFrame(data)
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        size="count",
        hover_name=label_col,
        color=label_col,
        size_max=50,
        zoom=4,
        height=600,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="white",
    )
    return fig

def layout():
    return html.Div(
        style={"padding": "30px", "backgroundColor": "#f9f9f9", "fontFamily": "Arial"},
        children=[
            html.H1("📍 Top Zones par Offres d'Emploi", style={
                "textAlign": "center",
                "color": "#333",
                "marginBottom": "20px",
                "fontSize": "2.5em"
            }),

            html.Div("Choisissez d'afficher les villes ou les régions avec le plus d'offres d'emploi :", style={
                "textAlign": "center",
                "color": "#555",
                "fontSize": "1.2em",
                "marginBottom": "20px"
            }),

            dcc.RadioItems(
                id="zone-selector",
                options=[
                    {"label": "🧭 Villes", "value": "ville"},
                    {"label": "🗺️ Régions", "value": "region"}
                ],
                value="ville",
                labelStyle={"display": "inline-block", "margin": "0 20px", "fontSize": "1.1em"},
                style={"textAlign": "center", "marginBottom": "30px"},
            ),

            html.Div(id="map-container")
        ]
    )

@dash.callback(
    Output("map-container", "children"),
    Input("zone-selector", "value")
)
def update_map(zone_type):
    try:
        if zone_type == "ville":
            response = requests.get(f"{API_BASE_URL}/api/top_ville")
            data = response.json()["data"]
            fig = get_map_figure(data, label_col="ville")
        else:
            response = requests.get(f"{API_BASE_URL}/api/top_region")
            data = response.json()["data"]
            fig = get_map_figure(data, label_col="region")

        return html.Div([
            dcc.Graph(figure=fig)
        ], style={
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
            "borderRadius": "12px",
            "overflow": "hidden",
            "backgroundColor": "#ffffff",
            "padding": "10px"
        })

    except Exception as e:
        return html.Div([
            html.H2("❌ Erreur de chargement", style={"color": "red"}),
            html.P(str(e))
        ])
