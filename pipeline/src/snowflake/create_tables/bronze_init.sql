USE DATABASE JOB_MARKET;
USE SCHEMA RAW;


CREATE TABLE IF NOT EXISTS RAW_CANDIDAT (
  id_candidat INT IDENTITY(1,1) PRIMARY KEY,
  nom VARCHAR(50),
  prenom VARCHAR(50),
  adresse VARCHAR(100),
  email VARCHAR(50),
  tel VARCHAR(25),
  id_competence VARCHAR(100),
  id_softskill VARCHAR(100),
  id_metier VARCHAR(100),
  id_lieu VARCHAR(100),
  id_contrat VARCHAR(100),
  id_type_entreprise VARCHAR(100),
  id_seniorite VARCHAR(100),
  id_teletravail VARCHAR(100),
  id_domaine VARCHAR(100),
  salaire_min  NUMBER
);


CREATE TABLE IF NOT EXISTS RAW_SOFTSKILL (
  id_softskill INT IDENTITY(1,1) PRIMARY KEY,
  code_rome VARCHAR(50),
  uuid VARCHAR(36),
  created_at VARCHAR(100),
  skill_id VARCHAR(12),
  score NUMBER(18,17),
  summary VARCHAR(50),
  details VARCHAR(150)
);


CREATE TABLE IF NOT EXISTS RAW_OFFRE (
  id NUMBER AUTOINCREMENT PRIMARY KEY,
  id_local VARCHAR(10),
  source VARCHAR(20),
  title VARCHAR(1000),
  description VARCHAR(16777216),
  company_name VARCHAR(100),
  location_name  VARCHAR(100),
  latitude NUMBER(9,6),
  longitude NUMBER(9,6),
  date_created TIMESTAMP_LTZ,
  date_updated TIMESTAMP_LTZ,
  contract_type VARCHAR(20),
  contract_duration VARCHAR(50),
  working_hours VARCHAR(14),
  salary_min INT,
  salary_max INT,
  salary_currency VARCHAR(10),
  salary_period VARCHAR(8),
  experience_required VARCHAR(30),
  category VARCHAR(100),
  sector VARCHAR(150),
  application_url VARCHAR(16777216),
  source_url VARCHAR(16777216),
  skills VARCHAR(16777216),
  remote_work VARCHAR(10),
  is_handicap_accessible NUMBER(2,1),
  code_rome VARCHAR(5),
  langues VARCHAR(100),
  date_extraction TIMESTAMP_LTZ
);
