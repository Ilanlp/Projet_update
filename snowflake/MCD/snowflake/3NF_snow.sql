CREATE TABLE Date_calendar (
  id_date INT PRIMARY KEY,
  full_date DATE,
  jour INT,
  mois INT,
  mois_nom VARCHAR(20),
  trimestre INT,
  annee INT,
  semaine INT,
  jour_semaine VARCHAR(20)
);

CREATE TABLE Lieu (
  id_lieu INT PRIMARY KEY,
  niveau VARCHAR(20),
  code_postal VARCHAR(10),
  ville VARCHAR(50),
  departement VARCHAR(50),
  region VARCHAR(50),
  pays VARCHAR(50),
  latitude FLOAT,
  longitude FLOAT
);

CREATE TABLE TypeEntreprise (
  id_type INT PRIMARY KEY,
  nom VARCHAR(30)
);

CREATE TABLE DomaineEntreprise (
  id_domaine_ent INT PRIMARY KEY,
  nom VARCHAR(50)
);

CREATE TABLE Entreprise (
  id_entreprise INT PRIMARY KEY,
  nom TEXT,
  id_type_entreprise INT REFERENCES TypeEntreprise(id_type),
  id_domaine_entreprise INT REFERENCES DomaineEntreprise(id_domaine_ent),
  tranche_effectif VARCHAR(50)
);

CREATE TABLE Contrat (
  id_contrat INT PRIMARY KEY,
  type_contrat VARCHAR(30),
  temps_travail VARCHAR(30),
  alternance BOOLEAN,
  horaires TEXT
);

CREATE TABLE DomaineData (
  id_domaine INT PRIMARY KEY,
  nom VARCHAR(30)
);

CREATE TABLE Teletravail (
  id_teletravail INT PRIMARY KEY,
  modalite VARCHAR(50)
);

CREATE TABLE NiveauSeniorite (
  id_niveau INT PRIMARY KEY,
  libelle VARCHAR(30)
);

CREATE TABLE CodeROME (
  id_rome INT PRIMARY KEY,
  code VARCHAR(10),
  libelle TEXT
);

CREATE TABLE OffreEmploi (
  id_offre INT PRIMARY KEY,
  id_contrat INT REFERENCES Contrat(id_contrat),
  id_lieu INT REFERENCES Lieu(id_lieu),
  id_date INT REFERENCES Date_calendar(id_date),
  id_entreprise INT REFERENCES Entreprise(id_entreprise),
  id_domaine INT REFERENCES DomaineData(id_domaine),
  id_teletravail INT REFERENCES Teletravail(id_teletravail),
  id_niveau INT REFERENCES NiveauSeniorite(id_niveau),
  id_rome INT REFERENCES CodeROME(id_rome),
  description TEXT,
  date_publication DATETIME,
  date_mise_a_jour DATETIME,
  source VARCHAR(50),
  source_url VARCHAR(100),
  salaire INT
);

CREATE TABLE CompetenceTech (
  id_competence INT PRIMARY KEY,
  nom TEXT,
  type VARCHAR(30)
);

CREATE TABLE Formation (
  id_formation INT PRIMARY KEY,
  nom TEXT,
  plateforme TEXT,
  cout INT,
  niveau TEXT,
  duree VARCHAR(30),
  lien TEXT
);

CREATE TABLE Formation_Competence (
  id_formation INT REFERENCES Formation(id_formation),
  id_competence INT REFERENCES CompetenceTech(id_competence),
  PRIMARY KEY (id_formation, id_competence)
);

CREATE TABLE Offre_CompetenceTech (
  id_offre INT REFERENCES OffreEmploi(id_offre),
  id_competence INT REFERENCES CompetenceTech(id_competence),
  PRIMARY KEY (id_offre, id_competence)
);

CREATE TABLE Competence_Domaine (
  id_competence INT REFERENCES CompetenceTech(id_competence),
  id_domaine INT REFERENCES DomaineData(id_domaine),
  poids INT,
  PRIMARY KEY (id_competence, id_domaine)
);

CREATE TABLE Candidat (
  id_candidat INT PRIMARY KEY,
  email TEXT,
  mobilite BOOLEAN,
  salaire_min_souhaite INT
);

CREATE TABLE Soft_skills (
  id_soft_skills INT PRIMARY KEY,
  nom_skill VARCHAR(50)
);

CREATE TABLE Candidat_Competence (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_competence INT REFERENCES CompetenceTech(id_competence),
  niveau INT,
  PRIMARY KEY (id_candidat, id_competence)
);

CREATE TABLE Candidat_DomaineData (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_domaine INT REFERENCES DomaineData(id_domaine),
  PRIMARY KEY (id_candidat, id_domaine)
);

CREATE TABLE Candidat_Lieu (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_lieu INT REFERENCES Lieu(id_lieu),
  niveau VARCHAR(20),
  type_pref VARCHAR(20),
  PRIMARY KEY (id_candidat, id_lieu)
);

CREATE TABLE Candidat_Contrat (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_contrat INT REFERENCES Contrat(id_contrat),
  PRIMARY KEY (id_candidat, id_contrat)
);

CREATE TABLE Candidat_TypeEntreprise (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_type INT REFERENCES TypeEntreprise(id_type),
  PRIMARY KEY (id_candidat, id_type)
);

CREATE TABLE Candidat_DomaineEntreprise (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_domaine_ent INT REFERENCES DomaineEntreprise(id_domaine_ent),
  PRIMARY KEY (id_candidat, id_domaine_ent)
);

CREATE TABLE Candidat_Teletravail (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_teletravail INT REFERENCES Teletravail(id_teletravail),
  PRIMARY KEY (id_candidat, id_teletravail)
);

CREATE TABLE Candidat_NiveauSeniorite (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_niveau INT REFERENCES NiveauSeniorite(id_niveau),
  type_pref VARCHAR(20),
  PRIMARY KEY (id_candidat, id_niveau)
);

CREATE TABLE MatchingCandidatOffre (
  id_matching INT PRIMARY KEY,
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_offre INT REFERENCES OffreEmploi(id_offre),
  score_global FLOAT,
  score_tech FLOAT,
  manques TEXT,
  suggestion_formation TEXT
);

CREATE TABLE Candidat_formation (
  id_candidat INT REFERENCES Candidat(id_candidat),
  id_formation INT REFERENCES Formation(id_formation),
  type_pref VARCHAR(20),
  PRIMARY KEY (id_candidat, id_formation)
);

CREATE TABLE offre_soft_skills (
  id_offre INT REFERENCES OffreEmploi(id_offre),
  id_soft_skills INT REFERENCES Soft_skills(id_soft_skills),
  PRIMARY KEY (id_offre, id_soft_skills)
);
