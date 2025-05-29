{{ config(materialized='table', tags=['sql']) }}

with

offre_du_jour as (
    select *
    from {{ source('RAW', 'RAW_OFFRE') }}
    where date_extraction::date = current_date
),

{{ tokenize_text("offre_du_jour", 'id_local', 'sector', 'sector') }},
{{ tokenize_text("offre_du_jour", 'id_local', 'description', 'description') }},
{{ tokenize_text(source('dim_tables','DIM_DOMAINE'), 'id_domaine', 'nom_domaine', 'domaine') }},

sector_matching as (
    SELECT
        d.id_domaine,
        d.nom_domaine,
        s.sector,
        s.id_local,
        COUNT(*) as MATCHED_TOKENS,
        COUNT(DISTINCT s.TOKEN) as UNIQUE_MATCHED_TOKENS,
        ARRAY_AGG(DISTINCT s.TOKEN) as MATCHING_TOKENS
    FROM domaine_no_stopwords d
    LEFT JOIN sector_no_stopwords s 
    ON s.TOKEN = d.TOKEN
    GROUP BY s.id_local, s.sector, d.id_domaine, d.nom_domaine
),

description_matching as (
    SELECT
        d.id_domaine,
        d.nom_domaine,
        des.description,
        des.id_local,
        COUNT(*) as MATCHED_TOKENS,
        COUNT(DISTINCT des.TOKEN) as UNIQUE_MATCHED_TOKENS,
        ARRAY_AGG(DISTINCT des.TOKEN) as MATCHING_TOKENS
    FROM domaine_no_stopwords d
    LEFT JOIN description_no_stopwords des 
    ON des.TOKEN = d.TOKEN
    GROUP BY des.id_local, des.description, d.id_domaine, d.nom_domaine
    
),

sector_token_counts as (
    select
        sector,
        count(distinct token) as total_tokens,
    from sector_no_stopwords
    group by sector
),

description_token_counts as (
    select
        description,
        count(distinct token) as total_tokens,
    from description_no_stopwords
    group by description
),

sector_scored_matches AS (
    SELECT
        m.id_domaine,
        m.nom_domaine,
        m.sector,
        m.id_local,
        m.MATCHED_TOKENS,
        m.UNIQUE_MATCHED_TOKENS,
        m.MATCHING_TOKENS,
        c.TOTAL_TOKENS,
        (m.UNIQUE_MATCHED_TOKENS * 100.0 / NULLIF(c.TOTAL_TOKENS, 0)) as MATCH_PERCENTAGE,
        ROW_NUMBER() OVER (PARTITION BY m.sector ORDER BY MATCH_PERCENTAGE DESC) as RANK

    FROM sector_matching m
    LEFT JOIN sector_token_counts c ON m.sector = c.sector
),

desc_scored_matches as (
    SELECT
        m.id_domaine,
        m.nom_domaine,
        m.description,
        m.id_local,
        m.MATCHED_TOKENS,
        m.UNIQUE_MATCHED_TOKENS,
        m.MATCHING_TOKENS,
        c.TOTAL_TOKENS,
        (m.UNIQUE_MATCHED_TOKENS * 100.0 / NULLIF(c.TOTAL_TOKENS, 0)) as MATCH_PERCENTAGE,
        ROW_NUMBER() OVER (PARTITION BY m.description ORDER BY MATCH_PERCENTAGE DESC) as RANK

    FROM description_matching m
    LEFT JOIN description_token_counts c ON m.description = c.description
),
 
combined_scores AS (
    SELECT
        s.id_domaine,
        d.description,
        s.nom_domaine,
        s.sector,
        s.id_local,
        s.MATCHED_TOKENS as S_MATCHED_TOKENS,
        s.UNIQUE_MATCHED_TOKENS as S_UNIQUE_MATCHED_TOKENS,
        s.MATCHING_TOKENS as S_MATCHING_TOKENS,
        s.TOTAL_TOKENS as S_TOTAL_TOKENS,
        s.MATCH_PERCENTAGE as S_MATCH_PERCENTAGE,
        d.MATCHED_TOKENS,
        d.UNIQUE_MATCHED_TOKENS,
        d.MATCHING_TOKENS,
        d.TOTAL_TOKENS,
        d.MATCH_PERCENTAGE,
        -- Score combiné avec pondération (60% secteur, 40% description)
        (COALESCE(S_MATCH_PERCENTAGE, 0) * 0.6 + COALESCE(d.MATCH_PERCENTAGE, 0) * 0.4) as COMBINED_MATCH_PERCENTAGE,
        ROW_NUMBER() OVER (PARTITION BY COALESCE(s.sector, 'NULL_SECTOR'), s.id_local ORDER BY COMBINED_MATCH_PERCENTAGE DESC) as RANK
    FROM sector_scored_matches s
    FULL OUTER JOIN desc_scored_matches d
    ON s.id_local = d.id_local
),

-- Résultat final avec union des trois cas - ne garde que RANK = 1 pour chaque source
final_results AS (
    -- Cas 1: combined_scores lorsque sector et description sont non null
    SELECT
        id_domaine,
        nom_domaine,
        id_local,
        sector,
        description,
        COMBINED_MATCH_PERCENTAGE as MATCH_PERCENTAGE,
        'combined' as source
    FROM combined_scores
    WHERE RANK = 1
    
    UNION ALL
    
    -- Cas 2: desc_scored_matches lorsque sector est null et description non null
    SELECT
        id_domaine,
        nom_domaine,
        id_local,
        NULL as sector,
        description,
        MATCH_PERCENTAGE,
        'description_only' as source
    FROM desc_scored_matches
    WHERE id_local NOT IN (SELECT id_local FROM combined_scores WHERE sector IS NOT NULL)
      AND description IS NOT NULL
      AND RANK = 1
    
    UNION ALL
    
    -- Cas 3: sector_scored_matches lorsque description est null et sector non null
    SELECT
        id_domaine,
        nom_domaine,
        id_local,
        sector,
        NULL as description,
        MATCH_PERCENTAGE,
        'sector_only' as source
    FROM sector_scored_matches
    WHERE id_local NOT IN (SELECT id_local FROM combined_scores WHERE description IS NOT NULL)
      AND sector IS NOT NULL
      AND RANK = 1
)

-- Résultat final - chaque id_local n'apparaît qu'une seule fois
SELECT 
    id_domaine, nom_domaine, sector, id_local
FROM final_results
