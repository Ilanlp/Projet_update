SELECT 
    id_competence AS "id_competence",
    skill AS "skill",
    type AS "type"
FROM DIM_COMPETENCE 
ORDER BY id_competence
{% if with_pagination %}
    LIMIT :page_size
    OFFSET :offset;
{% endif %}
