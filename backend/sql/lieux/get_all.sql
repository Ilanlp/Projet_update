SELECT 
    id_lieu AS "id_lieu",
    code_postal AS "code_postal",
    ville AS "ville",
    departement AS "departement",
    region AS "region",
    pays AS "pays",
    latitude AS "latitude",
    longitude AS "longitude",
    population AS "population"
FROM DIM_LIEU
ORDER BY id_lieu
{% if with_pagination %}
    LIMIT :page_size
    OFFSET :offset;
{% endif %}
