SELECT *
FROM ONE_BIG_TABLE
ORDER BY CODE_ROME {% if with_pagination %}
LIMIT %(page_size) s OFFSET %(offset) s {% endif %}