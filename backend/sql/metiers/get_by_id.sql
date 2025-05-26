SELECT 
    id_metier AS "id_metier",
    id_appellation AS "id_appellation",
    nom AS "nom",
FROM DIM_METIER
WHERE {{"id_metier = :ID"}}
ORDER BY id_metier DESC
LIMIT 1