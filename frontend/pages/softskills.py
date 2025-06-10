import dash
from dash import html, dcc, Input, Output
from dash import dash_table
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://localhost:8081")

dash.register_page(__name__, path="/softskills")

rome_codes = ["A1101", "A1102", "A1103"]

layout = html.Div(
    [
        html.H2("🧠 Soft Skills par Code ROME"),
        html.Label("Sélectionnez un code ROME :"),
        dcc.Dropdown(
            id="dropdown-code-rome",
            options=[{"label": code, "value": code} for code in rome_codes],
            value="A1101",
            clearable=False,
        ),
        html.Br(),
        html.Div(id="softskill-table"),
    ]
)


@dash.callback(
    Output("softskill-table", "children"), Input("dropdown-code-rome", "value")
)
def update_table(code_rome):
    try:
        response = requests.get(f"{API_BASE_URL}/api/rome_softskills/{code_rome}")
        if response.status_code != 200:
            return html.P(f"Erreur {response.status_code} : {response.text}")
        softskills = response.json()["data"]
        if not softskills:
            return html.P("Aucun soft skill trouvé pour ce code ROME.")
        return dash_table.DataTable(
            data=softskills,
            columns=[
                {"name": "ID", "id": "id_softskill"},
                {"name": "Soft Skill", "id": "summary"},
                {"name": "Description", "id": "details"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
        )
    except Exception as e:
        return html.P(f"Erreur API : {e}")
