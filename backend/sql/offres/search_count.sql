WITH filtered_data AS (
  SELECT *
  FROM ONE_BIG_TABLE
  WHERE 1 = 1 {% if filters %} {% for filter in filters %} {% if filter.operator == 'eq' %}
    AND {{ filter.field }} = :{{ filter.field }}_value {% elif filter.operator == 'neq' %}
    AND {{ filter.field }} != :{{ filter.field }}_value {% elif filter.operator == 'gt' %}
    AND {{ filter.field }} > :{{ filter.field }}_value {% elif filter.operator == 'gte' %}
    AND {{ filter.field }} >= :{{ filter.field }}_value {% elif filter.operator == 'lt' %}
    AND {{ filter.field }} < :{{ filter.field }}_value {% elif filter.operator == 'lte' %}
    AND {{ filter.field }} <= :{{ filter.field }}_value {% elif filter.operator == 'like' %}
    AND LOWER({{ filter.field }}) LIKE LOWER(:{{ filter.field }}_value) {% elif filter.operator == 'in' %}
    AND {{ filter.field }} IN (
      SELECT value
      FROM TABLE(
          SPLIT_TO_TABLE(:{{ filter.field }}_value, ',')
        )
    ) {% elif filter.operator == 'between' %}
    AND {{ filter.field }} BETWEEN :{{ filter.field }}_start AND :{{ filter.field }}_end {% endif %} {% endfor %} {% endif %} {% if search_text %}
    AND (
      LOWER(title) LIKE LOWER(:search_text)
      OR LOWER(description) LIKE LOWER(:search_text)
      OR LOWER(competences) LIKE LOWER(:search_text)
      OR LOWER(nom_metier) LIKE LOWER(:search_text)
      OR LOWER(softskills_summary) LIKE LOWER(:search_text)
    ) {% endif %}
)
SELECT COUNT(*) as total
FROM filtered_data