import dash
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

dash.register_page(__name__, path="/graph")

def create_offers_by_contract(df):
    """Crée un graphique en camembert montrant la répartition des offres par type de contrat"""
    if df.empty:
        return go.Figure()
    
    # Ajouter une catégorie "Non étiqueté" pour les valeurs manquantes
    contract_counts = df['TYPE_CONTRAT'].fillna('Non étiqueté').value_counts()
    
    fig = px.pie(
        values=contract_counts.values,
        names=contract_counts.index,
        title='Répartition des offres étiquetées par type de contrat',
        hole=0.3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=600
    )
    
    return fig

def create_offers_by_enterprise(df):
    """Crée un graphique en camembert montrant la répartition des offres par entreprise"""
    if df.empty:
        return go.Figure()
    
    # Ajouter une catégorie "Non étiqueté" pour les valeurs manquantes
    entreprise_counts = df['NOM_ENTREPRISE'].fillna('Non étiqueté').value_counts().head(5)
    
    fig = px.pie(
        values=entreprise_counts.values,
        names=entreprise_counts.index,
        title='Répartition du top 5 des entreprises qui recrutent le plus',
        hole=0.3
    )
    
    fig.update_traces(
        textposition='outside',
        textinfo='percent+label',
        textfont_size=14
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        height=600,
        margin=dict(t=100, b=100, l=100, r=100)
    )
    
    return fig

def create_offers_by_seniority(df):
    """Crée un graphique en barres montrant la répartition des offres par niveau de séniorité"""
    if df.empty:
        return go.Figure()
    
    # Ajouter une catégorie "Non étiqueté" pour les valeurs manquantes
    seniority_counts = df['TYPE_SENIORITE'].fillna('Non étiqueté').value_counts()
    
    fig = px.bar(
        x=seniority_counts.index,
        y=seniority_counts.values,
        title='Répartition des offres étiquetées par niveau de séniorité',
        labels={'x': 'Niveau de séniorité', 'y': 'Nombre d\'offres'}
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14
    )
    
    return fig

def create_offers_by_domain(df):
    """Crée un graphique en barres horizontales montrant la répartition des offres par domaine"""
    if df.empty:
        return go.Figure()
    
    # Ajouter une catégorie "Non étiqueté" pour les valeurs manquantes
    domain_counts = df['NOM_DOMAINE'].fillna('Non étiqueté').value_counts().head(10)
    
    fig = px.bar(
        x=domain_counts.values,
        y=domain_counts.index,
        orientation='h',
        title='Top 10 des domaines les plus demandés',
        labels={'x': 'Nombre d\'offres', 'y': 'Domaine'}
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        height=500
    )
    
    return fig

def create_offers_by_location(df):
    """Crée un graphique en barres montrant la répartition des offres par ville"""
    if df.empty:
        return go.Figure()
    
    # Ajouter une catégorie "Non étiqueté" pour les valeurs manquantes
    location_counts = df['VILLE'].fillna('Non étiqueté').value_counts().head(10)
    
    fig = px.bar(
        x=location_counts.index,
        y=location_counts.values,
        title='Top 10 des villes avec le plus d\'offres étiquetées',
        labels={'x': 'Ville', 'y': 'Nombre d\'offres'}
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        xaxis_tickangle=45
    )
    
    return fig

def create_skills_heatmap(df):
    """Crée une heatmap des compétences les plus demandées"""
    if df.empty:
        return go.Figure()
    
    # Extraire et compter les compétences
    all_skills = []
    for skills in df['COMPETENCES'].fillna('Non étiqueté'):
        if isinstance(skills, str):
            all_skills.extend([skill.strip() for skill in skills.split(',')])
    
    skill_counts = pd.Series(all_skills).value_counts().head(20)
    
    fig = px.imshow(
        np.array([skill_counts.values]),
        labels=dict(x="Compétences", y="", color="Nombre d'occurrences"),
        x=skill_counts.index,
        title="Top 20 des compétences les plus demandées",
        color_continuous_scale="Viridis"
    )
    
    # Ajuster l'échelle de la barre de couleur
    max_value = skill_counts.max()
    step = 100
    colorbar_ticks = list(range(0, max_value + step, step))
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        xaxis_tickangle=45,
        height=500,
        coloraxis_colorbar=dict(
            tickmode='array',
            tickvals=colorbar_ticks,
            ticktext=[str(x) for x in colorbar_ticks]
        )
    )
    
    return fig

layout = html.Div([
    html.H1("📊 Analyse des offres d'emploi", style={'textAlign': 'center', 'margin': '20px 0'}),
    
    html.Div([
        html.Div([
            dcc.Graph(id='contract-pie-chart'),
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='seniority-bar-chart'),
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),
    
    html.Div([
        html.Div([
            dcc.Graph(id='domain-bar-chart'),
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='location-bar-chart'),
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),
    
    html.Div([
        dcc.Graph(id='skills-heatmap'),
    ], style={'width': '100%', 'marginTop': '20px'})
])
