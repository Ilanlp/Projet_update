SELECT 
    id_seniorite AS "id_seniorite",
    type_seniorite AS "type_seniorite"
FROM DIM_SENIORITE
WHERE {{"id_seniorite = :ID"}}
ORDER BY id_seniorite DESC
LIMIT 1