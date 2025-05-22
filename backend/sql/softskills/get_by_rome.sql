SELECT 
    s.id_softskill AS "id_softskill",
    s.summary AS "summary",
    s.details AS "details"
FROM DIM_SOFTSKILL s
JOIN LIAISON_ROME_SOFT_SKILL_GOLD_SQL j ON s.id_softskill = j.id_softskill
JOIN DIM_ROMECODE r ON j.id_rome = r.id_rome
WHERE r.CODE_ROME = :code_rome;
