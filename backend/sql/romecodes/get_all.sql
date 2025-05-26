SELECT 
    id_rome AS "id_rome",
    code_rome AS "code_rome",
FROM DIM_ROMECODE
ORDER BY id_rome
{% if with_pagination %}
    LIMIT :page_size
    OFFSET :offset;
{% endif %}
