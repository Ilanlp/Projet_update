import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from dotenv import load_dotenv

load_dotenv()

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

app.layout = dbc.Container([
    html.H1("Job Market Dashboard"),
    
    # Navigation
    dbc.Nav([
        dbc.NavLink("🩺 Health Check", href="/", active="exact"),
        dbc.NavLink("🧠 Soft Skills", href="/softskills", active="exact"),
        dbc.NavLink("🧠 Top Ville", href="/top_ville", active="exact"),
        dbc.NavLink("💼 Search Offer",href="/search",active="exact")
    ], pills=True),

    html.Hr(),

    # Ici s'affichera le contenu de chaque page
    dash.page_container
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080, dev_tools_hot_reload=True)