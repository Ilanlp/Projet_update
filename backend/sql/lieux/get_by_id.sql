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
WHERE {{"id_lieu = :ID"}}
ORDER BY id_lieu DESC
LIMIT 1