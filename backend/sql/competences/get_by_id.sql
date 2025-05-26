SELECT 
    id_competence AS "id_competence",
    skill AS "skill",
    type AS "type"
FROM DIM_COMPETENCE
WHERE {{"id_competence = :ID"}}
ORDER BY id_competence DESC
LIMIT 1