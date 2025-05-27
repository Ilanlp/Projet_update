import dash
from dash import html, dcc, Input, Output
import requests

dash.register_page(__name__, path="/")

def layout():
    return html.Div([
        html.H2("🩺 Health Check"),
        dcc.Checklist(
            id='toggle-health',
            options=[{'label': 'Afficher les détails', 'value': 'show'}],
            value=[]
        ),
        html.Div(id='health-content')
    ])

@dash.callback(
    Output('health-content', 'children'),
    Input('toggle-health', 'value')
)
def update_health_details(toggle_value):
    if 'show' in toggle_value:
        try:
            response = requests.get("http://jm-backend:8000/health_check")
            data = response.json()
            return html.Div([
                html.P(f"Statut : {data['status']}"),
                html.P(f"Version : {data['version']}"),
            ])
        except Exception as e:
            return html.Div([html.P(f"Erreur : {str(e)}")])
    return html.Div()
