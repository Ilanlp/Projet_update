import dash
from dash import html
import requests

dash.register_page(__name__, path="/")

def layout():
    try:
        response = requests.get("http://jm-backend:8000/health_check")
        data = response.json()
        return html.Div([
            html.H2("🩺 Health Check"),
            html.P(f"Statut : {data['status']}"),
            html.P(f"Version : {data['version']}"),
        ])
    except Exception as e:
        return html.Div([html.P(f"Erreur : {str(e)}")])
