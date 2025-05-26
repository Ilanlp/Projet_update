SELECT 
    id_rome AS "id_rome",
    code_rome AS "code_rome",
FROM DIM_ROMECODE
WHERE {{"id_rome = :ID"}}
ORDER BY id_rome DESC
LIMIT 1