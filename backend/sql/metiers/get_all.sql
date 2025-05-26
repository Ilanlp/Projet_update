SELECT 
    id_metier AS "id_metier",
    id_appellation AS "id_appellation",
    nom AS "nom",
FROM DIM_METIER
ORDER BY id_metier
{% if with_pagination %}
    LIMIT :page_size
    OFFSET :offset;
{% endif %}
