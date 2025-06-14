import dash
import dash_table
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import os
import base64
from dash.exceptions import PreventUpdate

API_URL = os.getenv('API_URL', 'http://jm-backend:8081')
API_USERNAME = os.getenv('API_USERNAME', 'admin')
API_PASSWORD = os.getenv('API_PASSWORD', 'password123')

def get_auth_header():
    """Crée l'header d'authentification Basic"""
    credentials = f"{API_USERNAME}:{API_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

# Initialisation de la page
dash.register_page(__name__, path='/profile')

def fetch_competences_data():
    try:
        response = requests.get(f'{API_URL}/api/competences')
        data = response.json()['data']
        return [{'label': item['skill'], 'value': item['skill']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_softskills_data():
    try:
        response = requests.get(f'{API_URL}/api/softskills')
        data = response.json()['data']
        return [{'label': item['summary'], 'value': item['summary']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_lieux_data():
    try:
        response = requests.get(f'{API_URL}/api/lieux')
        data = response.json()['data']
        return [{'label': item['ville'], 'value': item['ville']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_contrats_data():
    try:
        response = requests.get(f'{API_URL}/api/contrats')
        data = response.json()['data']
        return [{'label': item['type_contrat'], 'value': item['type_contrat']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_entreprises_data():
    try:
        response = requests.get(f'{API_URL}/api/entreprises')
        data = response.json()['data']
        return [{'label': item['type_entreprise'], 'value': item['type_entreprise']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_seniorite_data():
    try:
        response = requests.get(f'{API_URL}/api/seniorite')
        data = response.json()['data']
        return [{'label': item['type_seniorite'], 'value': item['type_seniorite']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_teletravail_data():
    try:
        response = requests.get(f'{API_URL}/api/teletravail')
        data = response.json()['data']
        return [{'label': item['type_teletravail'], 'value': item['type_teletravail']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_domaines_data():
    try:
        response = requests.get(f'{API_URL}/api/domaines')
        data = response.json()['data']
        return [{'label': item['nom_domaine'], 'value': item['nom_domaine']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

# Layout de la page
layout = html.Div([
    # Store pour maintenir les paramètres de recherche
    dcc.Store(id='search-params-store', data={}),

    # Header centré
    html.Div([
        html.H2("👤 Profil Candidat")
    ], style={'textAlign': 'center', 'margin': '20px 0'}),
    
    html.Div([
        # Section profil candidat
        html.Div([
            html.Div([
                html.H4("Compétences techniques", className="mb-3"),
                dcc.Input(
                    id='competence-input',
                    type='text',
                    placeholder='Ex: Python, SQL, Machine Learning',
                    style={'width': '100%', 'height': '40px', 'padding': '10px'},
                    value=''
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Soft Skills", className="mb-3"),
                dcc.Input(
                    id='softskill-input',
                    type='text',
                    placeholder='Ex: Communication, Leadership, Teamwork',
                    style={'width': '100%', 'height': '40px', 'padding': '10px'},
                    value=''
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Localisation", className="mb-3"),
                dcc.Input(
                    id='lieu-input',
                    type='text',
                    placeholder='Ex: Paris, Lyon, Marseille',
                    style={'width': '100%', 'height': '40px', 'padding': '10px'},
                    value=''
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Type de contrat", className="mb-3"),
                dcc.Dropdown(
                    id='contrat-dropdown',
                    multi=True,
                    placeholder="Sélectionnez le(s) type(s) de contrat",
                    style={'height': '40px'},
                    value=[]
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Séniorité", className="mb-3"),
                dcc.Dropdown(
                    id='seniorite-dropdown',
                    multi=True,
                    placeholder="Sélectionnez votre niveau d'expérience",
                    style={'height': '40px'},
                    value=[]
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Télétravail", className="mb-3"),
                dcc.Dropdown(
                    id='teletravail-dropdown',
                    multi=True,
                    placeholder="Sélectionnez vos préférences de télétravail",
                    style={'height': '40px'},
                    value=[]
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.H4("Domaine", className="mb-3"),
                dcc.Dropdown(
                    id='domaine-dropdown',
                    multi=True,
                    placeholder="Sélectionnez le(s) domaine(s)",
                    style={'height': '40px'},
                    value=[]
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                dbc.Button(
                    'Trouver des offres',
                    id='search-button',
                    n_clicks=0,
                    className="nav-button"
                )
            ], style={'textAlign': 'center', 'marginTop': '30px'}),
        ], style={
            'maxWidth': '800px',
            'margin': '0 auto',
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)'
        }),
    ], style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '20px'
    }),
    
    # Section des résultats
    html.Div(id='results-container')
])

# Callbacks pour charger les données des dropdowns
@dash.callback(
    Output('contrat-dropdown', 'options'),
    Input('contrat-dropdown', 'id')
)
def load_contrats(_):
    return fetch_contrats_data()

@dash.callback(
    Output('seniorite-dropdown', 'options'),
    Input('seniorite-dropdown', 'id')
)
def load_seniorite(_):
    return fetch_seniorite_data()

@dash.callback(
    Output('teletravail-dropdown', 'options'),
    Input('teletravail-dropdown', 'id')
)
def load_teletravail(_):
    return fetch_teletravail_data()

@dash.callback(
    Output('domaine-dropdown', 'options'),
    Input('domaine-dropdown', 'id')
)
def load_domaines(_):
    return fetch_domaines_data()

# Callback pour sauvegarder les paramètres de recherche
@dash.callback(
    Output('search-params-store', 'data', allow_duplicate=True),
    Input('search-button', 'n_clicks'),
    [State('competence-input', 'value'),
     State('softskill-input', 'value'),
     State('lieu-input', 'value'),
     State('contrat-dropdown', 'value'),
     State('seniorite-dropdown', 'value'),
     State('teletravail-dropdown', 'value'),
     State('domaine-dropdown', 'value')],
    prevent_initial_call=True
)
def save_search_params(n_clicks, competence, softskill, lieu, contrat, seniorite, teletravail, domaine):
    if not n_clicks or n_clicks == 0:
        raise PreventUpdate
        
    if not any([competence, softskill, lieu, contrat, seniorite, teletravail, domaine]):
        raise PreventUpdate
    
    # Construire le texte de recherche
    search_parts = []
    
    if competence:
        search_parts.append(competence)
    if softskill:
        search_parts.append(softskill)
    if lieu:
        search_parts.append(lieu)
    if contrat:
        search_parts.extend(contrat)
    if seniorite:
        search_parts.extend(seniorite)
    if teletravail:
        search_parts.extend(teletravail)
    if domaine:
        search_parts.extend(domaine)
    
    # Joindre toutes les parties avec des espaces
    search_text = " ".join(search_parts)
    
    return {'text': search_text}

# Callback pour afficher les résultats
@dash.callback(
    Output('results-container', 'children'),
    Input('search-params-store', 'data')
)
def display_results(search_params):
    if not search_params:
        return None
    
    try:
        # Appel à l'API de recommandation
        text = search_params.get('text')
        print(text)
        response = requests.post(
            f'{API_URL}/api/model/match',
            json={'text': text},
            headers=get_auth_header()
        )
        
        if response.status_code == 401:
            return html.P("Erreur d'authentification. Veuillez vérifier les credentials.")
        elif response.status_code != 200:
            return html.P(f"Erreur API: {response.status_code}")
            
        data = response.json()
        
        if not data.get('matches'):
            return html.P("Aucune offre recommandée pour ce profil.")
        
        # Préparer les données pour le tableau
        df = pd.DataFrame(data['matches'])
        
        # Définir les colonnes à afficher
        columns = [
            {'name': 'Titre', 'id': 'title'},
            {'name': 'Entreprise', 'id': 'company'},
            {'name': 'Ville', 'id': 'location'},
            {'name': 'Type de contrat', 'id': 'type_contrat'},
            {'name': 'Domaine', 'id': 'nom_domaine'},
            {'name': 'Séniorité', 'id': 'type_seniorite'},
            {'name': 'Télétravail', 'id': 'type_teletravail'},
            {'name': 'Compétences', 'id': 'competences'},
            {'name': 'Soft Skills', 'id': 'softskills_summary'},
            {'name': 'Score de correspondance', 'id': 'score', 'type': 'numeric', 'format': {'specifier': '.2%'}}
        ]
        
        # Créer le tableau
        table = html.Div([
            html.H4(f"{len(data['matches'])} offre(s) recommandée(s)", style={'textAlign': 'center', 'margin': '20px 0'}),
            dash_table.DataTable(
                id='offres-table',
                columns=columns,
                data=df.to_dict('records'),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'column_id': 'score'},
                        'textAlign': 'right'
                    }
                ],
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                row_selectable=False,
                row_deletable=False,
                selected_rows=[],
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
            )
        ], style={'maxWidth': '1200px', 'margin': '30px auto', 'padding': '0 20px'})
        
        return table
        
    except Exception as e:
        return html.P(f"Erreur lors du chargement des recommandations: {str(e)}")
