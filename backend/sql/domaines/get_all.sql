SELECT 
    d.id_domaine AS "id_domaine",
    d.code_domaine AS "code_domaine",
    d.nom_domaine AS "nom_domaine"
FROM DIM_DOMAINE d
ORDER BY d.id_domaine;
