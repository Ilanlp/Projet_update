SELECT *
FROM ONE_BIG_TABLE
ORDER BY ID {% if with_pagination %}
LIMIT :page_size OFFSET :offset {% endif %}