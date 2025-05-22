SELECT *
FROM ONE_BIG_TABLE
ORDER BY id {% if with_pagination %}
LIMIT :page_size OFFSET :offset {% endif %}