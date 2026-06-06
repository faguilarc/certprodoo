-- 1. Verificar la relación entre professional_request y res_users
SELECT
    pr.id as request_id,
    pr.name as request_number,
    pr.user_id,
    ru.login as usuario_login,
    ru.partner_id
FROM professional_registers_professional_request pr
LEFT JOIN res_users ru ON pr.user_id = ru.id
WHERE pr.user_id IS NOT NULL
LIMIT 10;


-- 2. Buscar archivos adjuntos subidos por un usuario específico a través de sus solicitudes
SELECT
    a.id as attachment_id,
    a.name as filename,
    a.res_model,
    a.res_id,
    a.create_date,
    ru.login as uploaded_by_user
FROM ir_attachment a
JOIN res_users ru ON a.create_uid = ru.id
WHERE ru.login = 'nombre_usuario'  -- Reemplaza con el login del usuario
  AND a.res_model IN (
    'professional_registers_inscription',
    'professional_registers_professional_request',
    'professional_registers_claim_request',
    'professional_registers_public_request'
  )
ORDER BY a.create_date DESC;

-- 3. Actualizar para hacer públicos los archivos adjuntos de un usuario específico
UPDATE ir_attachment
SET public = true
WHERE create_uid = (SELECT id FROM res_users WHERE login = 'nombre_usuario')
  AND res_model IN (
    'professional_registers_inscription',
    'professional_registers_professional_request',
    'professional_registers_claim_request',
    'professional_registers_public_request'
  )
  AND public = false;

-- 3.1 Actualizar para hacer públicos los archivos adjuntos de un usuario específico
UPDATE ir_attachment
SET public = true
WHERE create_uid = (SELECT id FROM res_users WHERE login = 'mprado')
  AND public = false;

-- 4. Mostrar cuántos archivos se actualizaron
SELECT COUNT(*) as archivos_actualizados
FROM ir_attachment
WHERE create_uid = (SELECT id FROM res_users WHERE login = 'nombre_usuario')
  AND res_model IN (
    'professional_registers_inscription',
    'professional_registers_professional_request',
    'professional_registers_claim_request',
    'professional_registers_public_request'
  )
  AND public = true;

-- 5. Ver campos de professional_registers_professional_request
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'professional_registers_professional_request'
AND column_name IN ('id', 'name', 'user', 'user_id', 'create_uid')
ORDER BY ordinal_position;

-- 6. Ver campos de res_users
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'res_users'
AND column_name IN ('id', 'login', 'partner_id', 'create_date')
ORDER BY ordinal_position;

-- 7. Actualizar el login en res_users basado en el campo 'user' de las solicitudes
UPDATE res_users ru
SET login = pr.user
FROM professional_registers_professional_request pr
WHERE pr.user_id = ru.id
  AND pr.user IS NOT NULL
  AND pr.user != ''
  AND ru.login != pr.user; -- Solo actualiza si son diferentes

-- 7. Mostrar Usuarios que pertenecen a un grupo estándar específico (según res_groups.name)
SELECT
    ru.id AS user_id,
    ru.login AS user_login,
    ru.active,
    rp.name AS partner_name,
    rp.email,
    rg.name AS group_name,
    rg.comment AS group_comment
FROM res_users ru
JOIN res_partner rp ON ru.partner_id = rp.id
JOIN res_groups_users_rel rel ON ru.id = rel.uid
JOIN res_groups rg ON rel.gid = rg.id
WHERE rg.name ILIKE '%nombre_del_grupo%'
ORDER BY ru.login;

-- 8. Ver Grupos con cantidad de usuarios
SELECT
    rg.id AS group_id,
    rg.name AS group_name,
    COUNT(ru.id) AS total_usuarios
FROM res_groups rg
LEFT JOIN res_groups_users_rel rgur ON rg.id = rgur.gid
LEFT JOIN res_users ru ON rgur.uid = ru.id
GROUP BY rg.id, rg.name
ORDER BY rg.name;

-- 9. Ver Usuarios por grupo
SELECT
    rg.name AS group_name,
    ru.id AS user_id,
    ru.login,
    rp.name AS partner_name
FROM res_groups rg
JOIN res_groups_users_rel rgur ON rg.id = rgur.gid
JOIN res_users ru ON rgur.uid = ru.id
LEFT JOIN res_partner rp ON ru.partner_id = rp.id
ORDER BY rg.name, ru.login;

-- 10. Ver Usuarios con la lista de grupos a los que pertenecen
SELECT
    ru.id AS user_id,
    ru.login,
    rp.name AS partner_name,
    COALESCE(array_agg(rg.name ORDER BY rg.name), '{}'::text[]) AS grupos
FROM res_users ru
LEFT JOIN res_partner rp ON ru.partner_id = rp.id
LEFT JOIN res_groups_users_rel rgur ON ru.id = rgur.uid
LEFT JOIN res_groups rg ON rgur.gid = rg.id
GROUP BY ru.id, ru.login, rp.name
ORDER BY ru.login;

-- 11. Ver Usuarios que pertenecen a alguno de los grupos especificados
SELECT DISTINCT
    ru.id AS user_id,
    ru.login,
    rp.name AS partner_name,
    (SELECT array_agg(g.name ORDER BY g.name)
     FROM res_groups_users_rel gur
     JOIN res_groups g ON gur.gid = g.id
     WHERE gur.uid = ru.id) AS grupos
FROM res_users ru
LEFT JOIN res_partner rp ON ru.partner_id = rp.id
WHERE EXISTS (
    SELECT 1
    FROM res_groups_users_rel gur
    JOIN res_groups g ON gur.gid = g.id
    WHERE gur.uid = ru.id AND g.name IN ('grupo1', 'grupo2')  -- nombres de grupos
)
ORDER BY ru.login;