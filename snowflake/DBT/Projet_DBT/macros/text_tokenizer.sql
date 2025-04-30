{% macro tokenize_text(table_name, id_column, text_column, alias_prefix) %}
    {{ alias_prefix }}_tokens as (
        select 
            {{ id_column }},
            {{ text_column }},
            split(regexp_replace(lower({{ text_column }}), '[-\',.,"]+', ' '), ' ') as tokens
        from {{ table_name }}
    ),

    {{ alias_prefix }}_exploded as ( 
        select
            {{ id_column }},
            {{ text_column }},
            trim(T.value) as token
        from {{ alias_prefix }}_tokens,
        lateral flatten(input => tokens) T
    ),

    {{ alias_prefix }}_no_stopwords as (
        select
            {{ id_column }},
            {{ text_column }},
            token
        from {{ alias_prefix }}_exploded
        where len(token)>2 and token not in (select word from {{ref('STOPWORDS_FR')}})
    )
{% endmacro %}