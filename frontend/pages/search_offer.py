import dash
from dash import html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import requests
import pandas as pd
import dash_table
import os
from .graph_offer import (
    create_offers_by_contract,
    create_offers_by_seniority,
    create_offers_by_domain,
    create_offers_by_location,
    create_skills_heatmap,
    create_offers_by_enterprise,
)

API_URL = os.getenv('API_URL', 'http://jm-backend:8081')

dash.register_page(__name__, path="/search")

def fetch_contrat_data():
    try:
        response = requests.get(f'{API_URL}/api/contrats')
        data = response.json()['data']
        return [{'label': item['type_contrat'], 'value': item['type_contrat']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_seniorite_data():
    try:
        response = requests.get(f'{API_URL}/api/seniorite')
        data = response.json()['data']
        return [{'label': item['type_seniorite'], 'value': item['type_seniorite']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]

def fetch_domaine_data():
    try:
        response = requests.get(f'{API_URL}/api2/domaines')
        data = response.json()['data']
        return [{'label': item['nom_domaine'], 'value': item['nom_domaine']} for item in data]
    except:
        return [{'label': 'Erreur de chargement', 'value': 'error'}]
    
layout = html.Div([
    # Store pour maintenir les paramètres de recherche
    dcc.Store(id='search-params-store', data={}),

    # Header centré
    html.Div([
        html.H2("💼 Rechercher une offre")
    ], style={'textAlign': 'center', 'margin': '20px 0'}),
    
    html.Div([
        # Section recherche
        html.Div([
            html.Div([
                html.Label("Recherche d'offre :"),
                dcc.Input(
                    id='input-search',
                    type='text',
                    placeholder='Data Engineer',
                    style={'width': '100%', 'height': '40px'}
                ),
            ], style={'width': '68%'}),
            
            html.Div([
                html.Label("Ville :"),
                html.Br(),
                dcc.Input(
                    id='input-location',
                    placeholder="Sélectionnez une ville",
                    value='France',
                    style={'width': '100%', 'height': '40px'}
                )
            ], style={'width': '30%'}),
        ], style={'display': 'flex', 'justify-content': 'space-between'}),

        # Section filtres
        html.Div([
            html.Div([
                html.Label("Type de contrat :"),
                dcc.Dropdown(
                    id='dropdown-contrat',
                    multi=True,
                    placeholder="Sélectionnez un contrat",
                    style={'height': '40px'}
                )
            ], style={'flex': '1', 'marginRight': '15px'}),
            
            html.Div([
                html.Label("Séniorité :"),
                dcc.Dropdown(
                    id='dropdown-seniorite',
                    multi=True,
                    placeholder="Niveau d'expérience",
                    style={'height': '40px'}
                )
            ], style={'flex': '1', 'marginRight': '15px'}),

            html.Div([
                html.Label("Domaine :"),
                dcc.Dropdown(
                    id='dropdown-domaine',
                    multi=True,
                    placeholder="Sélectionnez un domaine",
                    style={'height': '40px'}
                )
            ], style={'flex': '1', 'marginRight': '15px'}),

        ], id='search-bar', style={
            'display': 'flex',
            'flexDirection': 'row',
            'gap': '15px',
            'marginBottom': '30px',
            'marginTop': '20px'
        }),
        
        html.Div([
            html.Button(
                'Rechercher',
                id='search-button',
                n_clicks=0,
                style={
                    'padding': '12px 30px',
                    'cursor': 'pointer',
                    'width': '200px',
                    'height': '45px'
                }
            )
        ], style={'textAlign': 'center'}),
    ], style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '0 20px'
    }),
    
    # Section des résultats
    html.Div(id='output-container')
])

# Callback pour charger les options du dropdown contrat
@dash.callback(
    Output('dropdown-contrat', 'options'),
    Input('dropdown-contrat', 'id')
)
def load_contrat(_):
    return fetch_contrat_data()

# Callback pour charger les options du dropdown séniorité
@dash.callback(
    Output('dropdown-seniorite', 'options'),
    Input('dropdown-seniorite', 'id')
)
def load_seniorite(_):
    return fetch_seniorite_data()

# Callback pour charger les options du dropdown domaine
@dash.callback(
    Output('dropdown-domaine', 'options'),
    Input('dropdown-domaine', 'id')
)
def load_domaine(_):
    return fetch_domaine_data()

# Callback pour sauvegarder les paramètres de recherche
@dash.callback(
    Output('search-params-store', 'data'),
    Input('search-button', 'n_clicks'),
    [State('input-search', 'value'),
     State('input-location', 'value'),
     State('dropdown-contrat', 'value'),
     State('dropdown-seniorite', 'value'),
     State('dropdown-domaine', 'value')],
    prevent_initial_call=True
)
def save_search_params(n_clicks, search_value, location_value, contrat_value, seniorite_value, domaine_value):
    if not search_value:
        raise PreventUpdate
    
    params = {
        'search': search_value,
        'location': location_value,
        'contrat': contrat_value,
        'seniorite': seniorite_value,
        'domaine': domaine_value
    }
    
    return params

# Callback pour mettre à jour le tableau et les graphiques
@dash.callback(
    Output('output-container', 'children'),
    Input('search-params-store', 'data')
)
def update_table_and_graphs(search_params):
    if not search_params or not search_params.get('search'):
        return None
    
    try:
        params = {
            'SEARCH': search_params['search']
        }
        
        if search_params.get('contrat'):
            params['TYPE_CONTRAT'] = search_params['contrat']
            
        if search_params.get('seniorite'):
            params['TYPE_SENIORITE'] = search_params['seniorite']
        
        if search_params.get('location'):
            params['LOCATION'] = search_params['location']

        if search_params.get('domaine'):
            params['NOM_DOMAINE'] = search_params['domaine']

        response = requests.get(f'{API_URL}/api/offres/filters', params=params)
        
        if response.status_code != 200:
            return html.P(f"Erreur API: {response.status_code}")
            
        data = response.json()['data']
        
        if not data.get('items'):
            return html.P("Aucune offre trouvée pour ces critères.")
        
        # Préparer les données pour le tableau et les graphiques
        df = pd.DataFrame(data['items'])
        
        # Définir les colonnes à afficher
        columns = [
            {'name': 'Titre', 'id': 'TITLE'},
            {'name': 'Entreprise', 'id': 'NOM_ENTREPRISE'},
            {'name': 'Ville', 'id': 'VILLE'},
            {'name': 'Type de contrat', 'id': 'TYPE_CONTRAT'},
            {'name': 'Domaine', 'id': 'NOM_DOMAINE'},
            {'name': 'Séniorité', 'id': 'TYPE_SENIORITE'},
            {'name': 'Compétences', 'id': 'COMPETENCES'}
        ]
        
        # Créer les graphiques
        contract_fig = create_offers_by_contract(df)
        entreprise_fig = create_offers_by_enterprise(df)
        seniority_fig = create_offers_by_seniority(df)
        domain_fig = create_offers_by_domain(df)
        location_fig = create_offers_by_location(df)
        skills_fig = create_skills_heatmap(df)
        
        # Créer le tableau
        table = html.Div([
            html.H4(f"{len(data['items'])} offre(s) trouvée(s)"),
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
        ], style={'maxWidth': '2000px', 'margin': '30px auto', 'padding': '0 50px'})
        
        # Créer la section des graphiques
        graphs = html.Div([
            html.H2("📊 Analyse des résultats", style={'textAlign': 'center', 'margin': '30px 0'}),
            
            html.Div([
                html.Div([
                    dcc.Graph(figure=contract_fig),
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(figure=entreprise_fig),
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            html.Div([
                html.Div([
                    dcc.Graph(figure=domain_fig),
                ], style={'width': '100%', 'display': 'inline-block'}),
            ]),

            html.Div([
                html.Div([
                    dcc.Graph(figure=seniority_fig),
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(figure=location_fig),
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            html.Div([
                dcc.Graph(figure=skills_fig),
            ], style={'width': '100%', 'marginTop': '20px'}),
            
        ], style={'maxWidth': '2000px', 'margin': '0 auto', 'padding': '0 50px'})
        
        return html.Div([table, graphs])
        
    except Exception as e:
        return html.P(f"Erreur lors du chargement des offres: {str(e)}")