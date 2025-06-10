import dash
from dash import html, dcc, Input, Output
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_URL", "http://localhost:8081")

dash.register_page(__name__, path="/")

def layout():
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100vh",
            "backgroundColor": "#f4f6f8",
            "fontFamily": "Arial, sans-serif"
        },
        children=[
            html.H1("🔍 Système de Surveillance", style={
                "color": "#333",
                "marginBottom": "30px"
            }),

            html.Div([
                html.Label("Afficher les détails", style={"fontSize": "18px", "marginRight": "10px"}),
                dcc.RadioItems(
                    id="toggle-health",
                    options=[
                        {"label": "Oui", "value": "show"},
                        {"label": "Non", "value": "hide"}
                    ],
                    value="hide",
                    labelStyle={"display": "inline-block", "marginRight": "20px"},
                    inputStyle={"marginRight": "5px"}
                ),
            ], style={"marginBottom": "30px"}),

            html.Div(id="health-content", style={"width": "400px"})
        ]
    )

@dash.callback(
    Output("health-content", "children"),
    Input("toggle-health", "value")
)
def update_health_details(toggle_value):
    if toggle_value == "show":
        try:
            response = requests.get(f"{API_BASE_URL}/health_check")
            data = response.json()

            color = "#28a745" if data["status"].lower() == "ok" else "#dc3545"

            return html.Div(
                style={
                    "backgroundColor": "#fff",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                    "borderLeft": f"8px solid {color}"
                },
                children=[
                    html.H3("✅ État du service", style={"color": "#333"}),
                    html.P(f"Statut : {data['status']}", style={"fontSize": "16px", "color": color}),
                    html.P(f"Version : {data['version']}", style={"fontSize": "16px", "color": "#555"})
                ]
            )
        except Exception as e:
            return html.Div([
                html.Div("❌ Erreur de chargement :", style={"color": "red", "marginBottom": "10px"}),
                html.Code(str(e), style={"backgroundColor": "#fee", "padding": "10px", "display": "block"})
            ])
    return html.Div()
