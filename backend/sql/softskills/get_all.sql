SELECT 
    s.id_softskill AS "id_softskill",
    s.summary AS "summary",
    s.details AS "details"
FROM DIM_SOFTSKILL s
ORDER BY s.id_softskill
LIMIT :page_size
OFFSET :offset;
