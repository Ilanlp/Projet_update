with search_filter as (
  SELECT id,
    id_local,
    title,
    description,
    type_contrat,
    code_domaine,
    nom_domaine,
    code_postal,
    ville,
    departement,
    region,
    pays,
    latitude,
    longitude,
    population,
    mois_creation,
    jour_creation,
    mois_nom_creation,
    jour_semaine_creation,
    week_end_creation,
    mois_modification,
    jour_modification,
    mois_nom_modification,
    jour_semaine_modification,
    week_end_modification,
    type_teletravail,
    type_seniorite,
    code_rome,
    nom_entreprise,
    categorie_entreprise,
    date_creation_entreprise,
    competences,
    types_competences,
    softskills_summary,
    softskills_details,
    nom_metier
  FROM ONE_BIG_TABLE
  CROSS JOIN TABLE(FLATTEN({{":SEARCH"}})) AS search_term
  WHERE
    LOWER(title) LIKE '%' || LOWER(search_term.value) || '%'
    OR LOWER(description) LIKE '%' || LOWER(search_term.value) || '%' 
    OR LOWER(nom_metier) LIKE '%' || LOWER(search_term.value) || '%' 
    OR LOWER(competences) LIKE '%' || LOWER(search_term.value) || '%'
    OR LOWER(ville) LIKE '%' || LOWER(search_term.value) || '%' 
    OR LOWER(code_postal) LIKE '%' || LOWER(search_term.value) || '%' 
    OR LOWER(nom_entreprise) LIKE '%' || LOWER(search_term.value) || '%'
),

seniorite_matched as (
  select * from search_filter
    LEFT JOIN TABLE(FLATTEN({{":TYPE_SENIORITE"}})) AS seniorite_term ON 1=1
    WHERE CASE 
        WHEN seniorite_term.value IS NOT NULL 
          THEN LOWER(title) LIKE '%' || LOWER(seniorite_term.value) || '%' 
             OR LOWER(description) LIKE '%' || LOWER(seniorite_term.value) || '%'
             OR LOWER(type_seniorite) LIKE '%' || LOWER(seniorite_term.value) || '%'
        ELSE TRUE  
    END 
),

contrat_matched as (
  select * from seniorite_matched
    LEFT JOIN TABLE(FLATTEN({{":TYPE_CONTRAT"}})) AS contrat_term ON 1=1
    WHERE CASE 
        WHEN contrat_term.value IS NOT NULL 
          THEN LOWER(title) LIKE '%' || LOWER(contrat_term.value) || '%' 
             OR LOWER(description) LIKE '%' || LOWER(contrat_term.value) || '%'
             OR LOWER(type_contrat) LIKE '%' || LOWER(contrat_term.value) || '%'
        ELSE TRUE  
    END 
),

domaine_matched as (
  select * from contrat_matched
    LEFT JOIN TABLE(FLATTEN({{":NOM_DOMAINE"}})) AS domaine_term ON 1=1
    WHERE CASE 
        WHEN domaine_term.value IS NOT NULL 
          THEN LOWER(nom_domaine) LIKE '%' || LOWER(domaine_term.value) || '%' 
             OR LOWER(description) LIKE '%' || LOWER(domaine_term.value) || '%'
        ELSE TRUE  
    END 
),

location_matched as (
  select 
    *, CONCAT_WS(', ', ville, code_postal, departement, region, pays) AS location
  from domaine_matched
    WHERE CASE 
        WHEN {{":LOCATION"}} IS NOT NULL 
          THEN LOWER(location) LIKE '%' || LOWER({{":LOCATION"}}) || '%' 
        ELSE TRUE  
    END 
)

select * from location_matched
/* ORDER BY id {% if with_pagination %}
LIMIT :page_size OFFSET :offset {% endif %} */