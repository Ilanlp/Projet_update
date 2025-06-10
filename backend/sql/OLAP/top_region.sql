SELECT 
    COUNT(*) AS "count", 
    l.region AS "region", 
    l.latitude AS "latitude", 
    l.longitude AS "longitude"
FROM Fait_offre o 
JOIN DIM_LIEU l ON o.id_lieu = l.id_lieu
WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
GROUP BY l.region, l.latitude, l.longitude
ORDER BY "count" DESC
LIMIT 15;
