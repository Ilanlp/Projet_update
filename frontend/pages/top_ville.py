import dash
from dash import html, dcc
import requests
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://jm-backend:8081")

dash.register_page(__name__, path="/top_ville")


def layout():
    try:
        # Appel à l'API backend
        response = requests.get(f"{API_BASE_URL}/api/top_ville")
        data = response.json()["data"]

        # Convertir en DataFrame
        df = pd.DataFrame(data)

        # Créer la carte
        fig = px.scatter_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            size="count",
            hover_name="ville",
            size_max=50,
            zoom=4,
            height=600,
            color_discrete_sequence=["#0074D9"],
        )

        fig.update_layout(
            mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

        return html.Div(
            [html.H2("📍 Villes avec le plus d'offres d'emploi"), dcc.Graph(figure=fig)]
        )

    except Exception as e:
        return html.Div([html.H2("Erreur de chargement"), html.P(str(e))])
