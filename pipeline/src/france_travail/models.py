from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


# Configuration de base pour tous les modèles
class FranceTravailModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
        validate_assignment=True
    )


# Modèles de base pour les réponses d'API
class Referentiel(FranceTravailModel):
    code: str = Field(description="Code du référentiel")
    libelle: str = Field(description="Libellé associé au code")


class Region(FranceTravailModel):
    code: str = Field(description="Code de la région")
    libelle: str = Field(description="Nom de la région")


class Departement(FranceTravailModel):
    code: str = Field(description="Code du département")
    libelle: str = Field(description="Nom du département")
    region: Optional[Region] = None


class Commune(FranceTravailModel):
    code: str = Field(description="Code INSEE de la commune")
    libelle: str = Field(description="Nom de la commune")
    codePostal: str = Field(description="Code postal de la commune")
    codeDepartement: str = Field(description="Code du département de la commune")


# Modèles pour les offres d'emploi
class LieuTravail(FranceTravailModel):
    libelle: str = Field(description="Libellé du lieu de travail")
    latitude: Optional[float] = Field(default=None, description="Latitude du lieu de travail")
    longitude: Optional[float] = Field(default=None, description="Longitude du lieu de travail")
    codePostal: Optional[str] = Field(default=None, description="Code postal du lieu de travail")
    commune: Optional[str] = Field(default=None, description="Code Insee du lieu de travail")


class Entreprise(FranceTravailModel):
    nom: Optional[str] = Field(default=None, description="Nom de l'entreprise")
    description: Optional[str] = Field(default=None, description="Description de l'entreprise")
    logo: Optional[HttpUrl] = Field(default=None, description="URL du logo de l'entreprise")
    url: Optional[HttpUrl] = Field(default=None, description="URL du site de l'entreprise")
    entrepriseAdaptee: Optional[bool] = Field(default=None, description="Flag entreprise adaptee")


class Formation(FranceTravailModel):
    codeFormation: Optional[str] = Field(default=None, description="Code du domaine de formation souhaité")
    domaineLibelle: Optional[str] = Field(default=None, description="Domaine de formation souhaité")
    niveauLibelle: Optional[str] = Field(default=None, description="Niveau de formation souhaité")
    commentaire: Optional[str] = Field(default=None, description="Commentaire sur la formation")
    exigence: Optional[str] = Field(default=None, description="E : la formation est exigée, S : la formation est souhaitée")


class Langue(FranceTravailModel):
    libelle: str = Field(description="Langue souhaitée")
    exigence: str = Field(description="E : la langue est exigée, S : la langue est souhaitée")


class Permis(FranceTravailModel):
    libelle: str = Field(description="Permis souhaité")
    exigence: str = Field(description="E : le permis est exigé, S : le permis est souhaité")


class Competence(FranceTravailModel):
    code: Optional[str] = Field(default=None, description="Code de la compétence")
    libelle: str = Field(description="Libellé de la compétence")
    exigence: str = Field(description="E : la compétence est exigée, S : la compétence est souhaitée")


class QualitePro(FranceTravailModel):
    libelle: str = Field(description="Libellé de la qualité professionnelle demandée")
    description: Optional[str] = Field(default=None, description="Description de la qualité professionnelle demandée")


class Salaire(FranceTravailModel):
    libelle: Optional[str] = Field(default=None, description="Libellé du salaire")
    commentaire: Optional[str] = Field(default=None, description="Commentaire sur le salaire")
    complement1: Optional[str] = Field(default=None, description="Complément 1 de rémunération (prime, véhicule, ...)")
    complement2: Optional[str] = Field(default=None, description="Complément 2 de rémunération (prime, véhicule, ...)")


class Contact(FranceTravailModel):
    nom: Optional[str] = Field(default=None, description="Nom du recruteur")
    coordonnees1: Optional[str] = Field(default=None, description="Adresse du recruteur")
    coordonnees2: Optional[str] = Field(default=None, description="Adresse du recruteur")
    coordonnees3: Optional[str] = Field(default=None, description="Adresse du recruteur")
    telephone: Optional[str] = Field(default=None, description="N° de téléphone du recruteur")
    courriel: Optional[str] = Field(default=None, description="Courriel du recruteur")
    commentaire: Optional[str] = Field(default=None, description="Précision sur le contact de l'offre")
    urlRecruteur: Optional[HttpUrl] = Field(default=None, description="URL du recruteur")
    urlPostulation: Optional[HttpUrl] = Field(default=None, description="URL du formulaire de postulation")


class Agence(FranceTravailModel):
    telephone: Optional[str] = Field(default=None, description="N° de téléphone de l'agence France Travail")
    courriel: Optional[str] = Field(default=None, description="Courriel de l'agence de France Travail")


class PartenaireOffre(FranceTravailModel):
    nom: Optional[str] = Field(default=None, description="Nom du partenaire")
    url: Optional[HttpUrl] = Field(default=None, description="URL de l'offre sur les sites des partenaires")
    logo: Optional[HttpUrl] = Field(default=None, description="URL du logo sur les sites des partenaires")


class OrigineOffre(FranceTravailModel):
    origine: str = Field(description="Origine de l'offre. 1 : France Tavail, 2 - Partenaire")
    urlOrigine: Optional[HttpUrl] = Field(default=None, description="URL de l'offre sur les sites des partenaires")
    partenaires: Optional[List[PartenaireOffre]] = Field(default=None)


class ContexteTravail(FranceTravailModel):
    horaires: Optional[List[str]] = Field(default=None, description="Liste des horaires du contexte de travail")
    conditionsExercice: Optional[List[str]] = Field(default=None, description="Liste des conditions d'exercice du contexte de travail")


class Offre(FranceTravailModel):
    id: str = Field(description="Identifiant de l'offre d'emploi")
    intitule: str = Field(description="Intitulé de l'offre")
    description: Optional[str] = Field(default=None, description="Description de l'offre")
    dateCreation: Optional[datetime] = Field(default=None, description="Date de création de l'offre")
    dateActualisation: Optional[datetime] = Field(default=None, description="Date de dernière actualisation de l'offre")
    lieuTravail: Optional[LieuTravail] = None
    romeCode: Optional[str] = Field(default=None, description="Code ROME de l'offre")
    romeLibelle: Optional[str] = Field(default=None, description="Libellé associé au code ROME")
    appellationlibelle: Optional[str] = Field(default=None, description="Libellé de l'appellation ROME de l'offre")
    entreprise: Optional[Entreprise] = None
    typeContrat: Optional[str] = Field(default=None, description="Code du type de contrat proposé (CDD, CDI, etc.)")
    typeContratLibelle: Optional[str] = Field(default=None, description="Libellé du type de contrat proposé")
    natureContrat: Optional[str] = Field(default=None, description="Nature du contrat (contrat d'apprentissage, etc.)")
    experienceExige: Optional[str] = Field(default=None, description="D : débutant accepté, E : l'expérience est exigée, S : l'expérience est souhaitée")
    experienceLibelle: Optional[str] = Field(default=None, description="Libellé de l'expérience")
    experienceCommentaire: Optional[str] = Field(default=None, description="Commentaire sur l'expérience")
    formations: Optional[List[Formation]] = Field(default=None, description="Formations")
    langues: Optional[List[Langue]] = Field(default=None, description="Langues")
    permis: Optional[List[Permis]] = Field(default=None, description="Permis")
    outilsBureautiques: Optional[List[str]] = Field(default=None, description="Liste des outils bureautiques utilisés")
    competences: Optional[List[Competence]] = Field(default=None, description="Compétences")
    salaire: Optional[Salaire] = None
    dureeTravailLibelle: Optional[str] = Field(default=None, description="Libellé de la durée de travail")
    dureeTravailLibelleConverti: Optional[str] = Field(default=None, description="Temps plein ou temps partiel")
    complementExercice: Optional[str] = Field(default=None, description="Complément exercice")
    conditionExercice: Optional[str] = Field(default=None, description="Conditions d'exercice")
    alternance: Optional[bool] = Field(default=None, description="Vrai si c'est une offre pour de l'alternance")
    contact: Optional[Contact] = None
    agence: Optional[Agence] = None
    nombrePostes: Optional[int] = Field(default=None, description="Nombre de postes disponibles pour cette offre")
    accessibleTH: Optional[bool] = Field(default=None, description="Vrai si l'offre est accessible aux travailleurs handicapés")
    deplacementCode: Optional[str] = Field(default=None, description="Code de la fréquence des déplacements")
    deplacementLibelle: Optional[str] = Field(default=None, description="Description des déplacements demandés")
    qualificationCode: Optional[str] = Field(default=None, description="Qualification du poste. Pour la qualification, on remonte les 9 valeurs 1 - manœuvre, ..., 8 - agent de maitrise, 9 - cadre")
    qualificationLibelle: Optional[str] = Field(default=None, description="Libellé de la qualification du poste")
    codeNAF: Optional[str] = Field(default=None, description="Code NAF (Code APE)")
    secteurActivite: Optional[str] = Field(default=None, description="Division NAF (comprend les deux premiers chiffre du code NAF)")
    secteurActiviteLibelle: Optional[str] = Field(default=None, description="Secteur d'activité de l'offre")
    qualitesProfessionnelles: Optional[List[QualitePro]] = Field(default=None, description="Qualités professionnelles")
    trancheEffectifEtab: Optional[str] = Field(default=None, description="Libellé de la tranche d'effectif de l'établissement")
    origineOffre: Optional[OrigineOffre] = None
    offresManqueCandidats: Optional[bool] = Field(default=None, description="Vrai si c'est une offre difficile à pourvoir")
    contexteTravail: Optional[ContexteTravail] = None


class Agregation(FranceTravailModel):
    valeurPossible: str = Field(description="Valeur possible du filtre")
    nbResultats: int = Field(description="Nombre de résultats attendus pour cette valeur")


class FiltrePossible(FranceTravailModel):
    filtre: str = Field(description="Nom du filtre")
    agregation: List[Agregation] = Field(description="Agrégations")


class ResultatRecherche(FranceTravailModel):
    resultats: List[Offre] = Field(description="Liste des offres retournées")
    filtresPossibles: Optional[List[FiltrePossible]] = Field(default=None, description="Liste des filtres supplémentaires possibles")


# Classes pour les paramètres de recherche
class SearchParams(FranceTravailModel):
    """
    Modèle pour les paramètres de recherche
    Gère également la conversion des énumérations
    """
    range: Optional[str] = Field(default="0-49", description="Pagination des données. Format : p-d, p est l'index du premier élément, d est l'index du dernier élément")
    sort: Optional[Union[str, int]] = Field(default=1, description="Tri des résultats (0: pertinence, 1: date, 2: distance)")
    domaine: Optional[str] = Field(default=None, description="Domaine de l'offre")
    codeROME: Optional[str] = Field(default=None, description="Code ROME de l'offre, séparés par virgule (max 200)")
    appellation: Optional[Union[str, int]] = Field(default=None, description="Code appellation ROME de l'offre")
    theme: Optional[Union[str, int]] = Field(default=None, description="Thème ROME du métier")
    secteurActivite: Optional[str] = Field(default=None, description="Division NAF de l'offre (2 premiers chiffres), séparés par virgule (max 2)")
    codeNAF: Optional[str] = Field(default=None, description="Code NAF (Code APE) de l'offre, séparés par virgule (max 2)")
    experience: Optional[Union[str, int]] = Field(default=None, description="Niveau d'expérience: 0-Non précisé, 1-Moins d'un an, 2-De 1 à 3 ans, 3-Plus de 3 ans")
    typeContrat: Optional[str] = Field(default=None, description="Code du type de contrat")
    natureContrat: Optional[str] = Field(default=None, description="Code de la nature du contrat")
    origineOffre: Optional[int] = Field(default=None, description="Origine de l'offre: 1-France Travail, 2-Partenaire")
    qualification: Optional[Union[str, int]] = Field(default=None, description="Qualification du poste: 0-non-cadre, 9-cadre")
    tempsPlein: Optional[bool] = Field(default=None, description="Temps plein ou partiel")
    commune: Optional[str] = Field(default=None, description="Code INSEE de la commune, séparés par virgule (max 5)")
    distance: Optional[int] = Field(default=None, description="Distance kilométrique du rayon de la recherche autour de la commune")
    departement: Optional[str] = Field(default=None, description="Département de l'offre, séparés par virgule (max 5)")
    inclureLimitrophes: Optional[bool] = Field(default=None, description="Inclure les départements limitrophes dans la recherche")
    region: Optional[str] = Field(default=None, description="Région de l'offre")
    paysContinent: Optional[str] = Field(default=None, description="Pays ou continent de l'offre")
    niveauFormation: Optional[str] = Field(default=None, description="Niveau de formation demandé")
    permis: Optional[str] = Field(default=None, description="Permis demandé")
    motsCles: Optional[str] = Field(default=None, description="Mots clés de recherche, séparés par virgule")
    salaireMin: Optional[Union[str, int]] = Field(default=None, description="Salaire minimum recherché")
    periodeSalaire: Optional[str] = Field(default=None, description="Période pour le calcul du salaire minimum: M-Mensuel, A-Annuel, H-Horaire, C-Cachet")
    accesTravailleurHandicape: Optional[bool] = Field(default=None, description="Offres pour lesquelles l'employeur est handi friendly")
    publieeDepuis: Optional[int] = Field(default=None, description="Recherche les offres publiées depuis maximum « X » jours")
    minCreationDate: Optional[str] = Field(default=None, description="Date minimale pour laquelle rechercher des offres (format yyyy-MM-dd'T'hh:mm:ss'Z')")
    maxCreationDate: Optional[str] = Field(default=None, description="Date maximale pour laquelle rechercher des offres (format yyyy-MM-dd'T'hh:mm:ss'Z')")
    offresMRS: Optional[bool] = Field(default=None, description="Uniquement les offres d'emplois avec méthode de recrutement par simulation proposée")
    experienceExigence: Optional[str] = Field(default=None, description="Exigence d'expérience: D-débutant accepté, S-expérience souhaitée, E-expérience exigée")
    grandDomaine: Optional[str] = Field(default=None, description="Code du grand domaine de l'offre")
    partenaires: Optional[str] = Field(default=None, description="Liste des codes partenaires dont les offres sont à inclure ou exclure")
    modeSelectionPartenaires: Optional[str] = Field(default=None, description="Mode de sélection des partenaires: INCLUS ou EXCLU")
    dureeHebdoMin: Optional[str] = Field(default=None, description="Recherche les offres avec une durée minimale (format HHMM)")
    dureeHebdoMax: Optional[str] = Field(default=None, description="Recherche les offres avec une durée maximale (format HHMM)")
    dureeContratMin: Optional[str] = Field(default=None, description="Recherche les offres avec une durée de contrat minimale (en mois, format double de 0 à 99)")
    dureeContratMax: Optional[str] = Field(default=None, description="Recherche les offres avec une durée de contrat maximale (en mois, format double de 0 à 99)")
    dureeHebdo: Optional[Union[str, int]] = Field(default=None, description="Type de durée du contrat: 0-Non précisé, 1-Temps plein, 2-Temps partiel")
    offresManqueCandidats: Optional[bool] = Field(default=None, description="Filtre les offres difficiles à pourvoir")
    entreprisesAdaptees: Optional[bool] = Field(default=None, description="Filtre les offres dont l'entreprise permet à un travailleur en situation de handicap d'exercer une activité professionnelle")
