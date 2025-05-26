SELECT 
    id_contrat AS "id_contrat",
    type_contrat AS "type_contrat"
FROM DIM_CONTRAT
WHERE {{"id_contrat = :ID"}}
ORDER BY id_contrat DESC
LIMIT 1