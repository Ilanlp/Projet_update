schema 3NF : 

// 🔹 Table des offres d'emploi
Table OffreEmploi {
  id_offre int [pk] // identifiant unique de l'offre (source: id)
  id_contrat int [ref: > Contrat.id_contrat] // FK vers type de contrat
  id_lieu int [ref: > Lieu.id_lieu] // FK vers localisation
  id_date int [ref: > Date_calendar.id_date]
  id_entreprise int [ref: > Entreprise.id_entreprise] // FK vers l'employeur
  id_domaine int [ref: > DomaineData.id_domaine] 
  id_teletravail int [ref: > Teletravail.id_teletravail]
  id_niveau int [ref: > NiveauSeniorite.id_niveau]
  id_rome int [ref: > CodeROME.id_rome]
  description text // source: description
  date_publication datetime // source: created / dateCreation : normalisation du format
  date_mise_a_jour datetime
  source varchar(50) // valeur fixe : "adzuna" ou "france_travail"
  source_url varchar(100)
  salaire int 
}


// 🔹 Table des dates 
Table Date_calendar {
  id_date int [pk]
  full_date date // ex: 2025-04-10
  jour int // 1 à 31
  mois int // 1 à 12
  mois_nom varchar(20) // Avril
  trimestre int // 1 à 4
  annee int
  semaine int // numéro de semaine
  jour_semaine varchar(20) // Lundi, Mardi, etc.
}


// 🔹 Table des localisations géographiques
Table Lieu {
  id_lieu int [pk]
  niveau varchar(20) // "ville", "departement", "region", "pays"
  code_postal varchar(10) // à extraire via regex sur libelle
  ville varchar(50) // idem
  departement varchar(50) // idem
  region varchar(50) // Adzuna : location_area_0 | FranceTravail : à construire via mapping CP/region
  pays varchar(50) // valeur fixe : "France"
  latitude float // source directe (France Travail)
  longitude float // idem
}


// 🔹 Table des entreprises
Table Entreprise {
  id_entreprise int [pk]
  nom text // source: company_display_name / entreprise.nom
  id_type_entreprise int [ref: > TypeEntreprise.id_type] // nouveau : FK
  id_domaine_entreprise int [ref: > DomaineEntreprise.id_domaine_ent] // nouveau : FK
  tranche_effectif varchar(50) // source: trancheEffectifEtab (à fiabiliser via API)
}

// 🔹 Type d'entreprise (Start-up, PME, etc.)
Table TypeEntreprise {
  id_type int [pk]
  nom varchar(30) // ex: "Start-up", "PME", "ETI", "Grand Groupe"
}

// 🔹 Domaine d'activité de l'entreprise
Table DomaineEntreprise {
  id_domaine_ent int [pk]
  nom varchar(50) // ex: "Banque", "Retail", "Transport", "Santé", etc.
}


// 🔹 Table des contrats
Table Contrat {
  id_contrat int [pk]
  type_contrat varchar(30) // source: contract_type (CDI, CDD, Freelance) | NLP sur description
  temps_travail varchar(30) // NLP sur contexteTravail ou champ dédié
  alternance boolean // détecté via NLP (présence du mot "alternance")
  horaires text // source: contexteTravail.horaires
}

// 🔹 Table des compétences techniques (standardisées)
Table CompetenceTech {
  id_competence int [pk]
  nom text // extrait via NLP sur description
  type varchar(30) // classification manuelle : langage, outil, framework, cloud...
  
}

// 🔹 Table des formations recommandées
Table Formation {
  id_formation int [pk]
  nom text
  plateforme text // ex: OpenClassrooms, Coursera, Udemy
  cout int // en euros
  niveau text // Débutant, Intermédiaire, Avancé
  duree varchar(30) // ex: "2 semaines", "10h"
  lien text // URL directe
}

// 🔹 Table de liaison Formation <-> Compétence
Table Formation_Competence {
  id_formation int [ref: > Formation.id_formation, primary key]
  id_competence int [ref: > CompetenceTech.id_competence, primary key]
}

// 🔹 Table de liaison Offre <-> Compétence
Table Offre_CompetenceTech {
  id_offre int [ref: > OffreEmploi.id_offre, primary key]
  id_competence int [ref: > CompetenceTech.id_competence, primary key]
  //exigence boolean // A ENLEVER  NLP : si compétence obligatoire ou souhaitée
}


// 🔹 Domaine data (standardisé)
Table DomaineData {
  id_domaine int [pk]
  nom varchar(30) // ex: "ML", "BI", "Data Eng", "Data Analyst", etc.
}


// 🔹 Table de liaison CompétenceTech <-> DomaineData
Table Competence_Domaine {
  id_competence int [ref: > CompetenceTech.id_competence, primary key]
  id_domaine int [ref: > DomaineData.id_domaine, primary key]
  poids int // calcul dynamique en fonction de la tendance du marché. Ex : offre present dans 80% des offres VBI mais 20% du ML . A renfrocer avoir le booleen
  // Cette table permet de relier une compétence à plusieurs domaines
  // Exemple : Python → ML + Data Eng + BI
}



// 🔹 Table des candidats (mise à jour avec des FK vers d'autres tables)
Table Candidat {
  id_candidat int [pk]
  email text // donné utilisateur
  mobilite boolean // l'utilisateur est-il mobile ?
  salaire_min_souhaite int // souhait utilisateur
}

// 🔹 Table des soft skills
Table Soft_skills {
  id_soft_skills int [pk]
  nom_skill varchar(50) // 
}

// 🔹 Table de liaison Candidat <-> Compétence
Table Candidat_Competence {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_competence int [ref: > CompetenceTech.id_competence, primary key]
  niveau int // niveau perçu ou auto-évalué : 1 (débutant) à 5 (expert)
}


// 🔹 Domaine data préféré du candidat (s'il peut en choisir plusieurs)
Table Candidat_DomaineData {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_domaine int [ref: > DomaineData.id_domaine, primary key]
  // Permet à un candidat d’avoir plusieurs domaines data préférés
}

// 🔹 Localisations préférées du candidat (multi-lieux)
Table Candidat_Lieu {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_lieu int [ref: > Lieu.id_lieu, primary key]
  niveau varchar(20) // "ville", "departement", "region", "pays"
  type_pref varchar(20) // optionnel : "principale", "secondaire", "remote"
}


Table Candidat_Contrat {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_contrat int [ref: > Contrat.id_contrat, primary key]
  // Permet de choisir plusieurs types de contrat souhaités (ex : CDI + Freelance)
}

Table Candidat_TypeEntreprise {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_type int [ref: > TypeEntreprise.id_type, primary key]
  // Ex : je veux bosser en start-up OU ETI
}

Table Candidat_DomaineEntreprise {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_domaine_ent int [ref: > DomaineEntreprise.id_domaine_ent, primary key]
  // Ex : secteurs préférés : Santé + Banque
}


// 🔹 Table de matching entre offre et candidat
Table MatchingCandidatOffre {
  id_matching int [pk]
  id_candidat int [ref: > Candidat.id_candidat]
  id_offre int [ref: > OffreEmploi.id_offre]
  score_global float // score final basé sur plusieurs critères
  score_tech float // score uniquement sur la correspondance des compétences
  manques text // liste des compétences manquantes
  suggestion_formation text // texte libre ou lien vers catalogue
}

// 🔹 Localisations préférées du candidat (multi-lieux)
Table Candidat_formation {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_formation int [ref: > Formation.id_formation, primary key]
  type_pref varchar(20) // optionnel : "principale", "secondaire", "remote"
}

// 🔹 Localisations préférées du candidat (multi-lieux)
Table offre_soft_skills {
  id_offre int [ref: > OffreEmploi.id_offre, primary key]
  id_soft_skills int [ref: > Soft_skills.id_soft_skills, primary key]
}

Table Teletravail {
  id_teletravail int [pk]
  modalite varchar(50) // ex: "Total", "Partiel", "Aucun", "Présentiel uniquement"
}

Table NiveauSeniorite {
  id_niveau int [pk]
  libelle varchar(30) // ex: "Junior", "Intermédiaire", "Senior", "Lead", etc.
}

Table CodeROME {
  id_rome int [pk]
  code varchar(10) // ex: "M1805"
  libelle text // ex: "Études et développement informatique"
}


Table Candidat_Teletravail {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_teletravail int [ref: > Teletravail.id_teletravail, primary key]
}


Table Candidat_NiveauSeniorite {
  id_candidat int [ref: > Candidat.id_candidat, primary key]
  id_niveau int [ref: > NiveauSeniorite.id_niveau, primary key]
  type_pref varchar(20) // optionnel également
}
