USE DATABASE JOB_MARKET;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS Date_calendar (
  id_date INT identity(1,1) PRIMARY KEY,
  full_date DATE,
  jour INT,
  mois INT,
  mois_nom VARCHAR(20),
  trimestre INT,
  annee INT,
  semaine INT,
  jour_semaine VARCHAR(20)
);
