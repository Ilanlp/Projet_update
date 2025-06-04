USE DATABASE JOB_MARKET;
USE SCHEMA GOLD;


CREATE TABLE IF NOT EXISTS DIM_DATE (
  id_date VARCHAR(10) PRIMARY KEY,
  semestre NUMBER(1,0),
  mois NUMBER(2,0),
  jour NUMBER(2,0),
  mois_nom VARCHAR(10),
  jour_semaine VARCHAR(10),
  week_end BOOLEAN
);


CREATE TABLE IF NOT EXISTS DIM_COMPETENCE (
  id_competence INT IDENTITY(1,1) PRIMARY KEY,
  skill VARCHAR(100),
  type VARCHAR(100)
);


CREATE TABLE IF NOT EXISTS DIM_CONTRAT (
  id_contrat INT IDENTITY(1,1) PRIMARY KEY,
  type_contrat VARCHAR(20)
);


CREATE TABLE IF NOT EXISTS DIM_DOMAINE (
  id_domaine INT IDENTITY(1,1) PRIMARY KEY,
  code_domaine VARCHAR(3),
  nom_domaine VARCHAR(200)
);


CREATE TABLE IF NOT EXISTS DIM_LIEU (
  id_lieu INT IDENTITY(1,1) PRIMARY KEY,
  code_postal NUMBER(5,0),
  ville VARCHAR(100),
  departement VARCHAR(100),
  region VARCHAR(50),
  pays VARCHAR(50),
  latitude NUMBER(9,6),
  longitude NUMBER(9,6),
  -- coord GEOGRAPHY
  population NUMBER(12,0)
);


CREATE TABLE IF NOT EXISTS DIM_METIER (
  id_metier INT IDENTITY(1,1) PRIMARY KEY,
  id_appellation INT,
  nom VARCHAR(500)
);


CREATE TABLE IF NOT EXISTS DIM_ROMECODE (
  id_rome INT IDENTITY(1,1) PRIMARY KEY,
  code_rome VARCHAR(5)
);


CREATE TABLE IF NOT EXISTS DIM_SENIORITE (
  id_seniorite INT IDENTITY(1,1) PRIMARY KEY,
  type_seniorite VARCHAR(8)
);


CREATE TABLE IF NOT EXISTS DIM_SOFTSKILL (
  id_softskill INT IDENTITY(1,1) PRIMARY KEY,
  summary VARCHAR(100),
  details VARCHAR(200)
);


CREATE TABLE IF NOT EXISTS DIM_TELETRAVAIL (
  id_teletravail INT IDENTITY(1,1) PRIMARY KEY,
  type_teletravail VARCHAR(10)
);


CREATE TABLE IF NOT EXISTS DIM_TYPE_ENTREPRISE (
  id_type_entreprise INT IDENTITY(1,1) PRIMARY KEY,
  type_entreprise VARCHAR(3),
  taille_min_salaries NUMBER(6,0),
  taille_max_salaries NUMBER(6,0),
  categorie_taille VARCHAR(50)
);


CREATE TABLE IF NOT EXISTS LIAISON_OFFRE_COMPETENCE (
  id_offre INT,
  id_local  VARCHAR(10),
  id_competence INT,
  PRIMARY KEY (id_offre,id_competence)
);


CREATE TABLE IF NOT EXISTS LIAISON_ROME_METIER (
  id_rome INT,
  id_metier INT,
  PRIMARY KEY (id_rome, id_metier)
);


CREATE TABLE IF NOT EXISTS LIAISON_ROME_SOFTSKILL (
  id_rome INT,
  id_softskill INT,
  PRIMARY KEY (id_rome, id_softskill)
);


CREATE TABLE IF NOT EXISTS FAIT_OFFRE (
    id_offre NUMBER AUTOINCREMENT,
    id_local VARCHAR(10),
    id_contrat INT,
    id_domaine INT,
    id_lieu INT,
    id_date_creation DATE,
    id_date_modification DATE,
    id_entreprise VARCHAR(100),
    id_teletravail INT,
    id_seniorite INT,
    id_rome INT
    
);