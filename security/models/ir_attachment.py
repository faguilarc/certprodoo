# -*- coding: utf-8 -*-
"""
Override de ir.attachment.check() para permitir que usuarios internos
(Editor/Gestor, Registrador, etc.) puedan leer adjuntos creados por otros
usuarios cuando esos adjuntos estan vinculados a registros a los que tienen
acceso.

PROBLEMA RAIZ:
  En Odoo 14, ir.attachment.check() bloquea la lectura de adjuntos "huerfanos"
  (sin res_id) o con res_field configurado, a menos que el usuario sea el
  creador o sea system/admin. Cuando un Editor/Gestor abre una solicitud
  creada por otro usuario (ej: Registrador), Odoo intenta leer los
  ir.attachment asociados via Many2many, pero check() lanza AccessError porque
  el adjunto fue creado por otro usuario y/o no tiene res_id.

  Linea critica en ir_attachment.py:
    if not self.env.is_system() and (res_field or (not res_id and create_uid != self.env.uid)):
        raise AccessError(...)

FIX:
  Para modo 'read', si el usuario es interno (base.group_user) Y tiene
  acceso de lectura al registro padre (res_model, res_id), se permite la
  lectura del adjunto. Si el adjunto es huerfano (sin res_model/res_id),
  se verifica si esta vinculado via una relacion Many2many a un registro
  accesible.
"""
import logging
from odoo import models, api, _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def check(self, mode, values=None):
        """Override de check() para permitir lectura cruzada de adjuntos
        entre usuarios internos cuando tienen acceso al registro padre.

        Estrategia:
          1. Intentar el check original de Odoo
          2. Si falla con AccessError en modo 'read' y el usuario es interno:
             a. Si el adjunto tiene res_model/res_id, verificar acceso al padre
             b. Si es huerfano, buscar si esta en una relacion Many2many
                con un registro accesible
          3. Si ninguna verificacion adicional pasa, relanzar el AccessError
        """
        try:
            return super(IrAttachment, self).check(mode, values=values)
        except AccessError:

            # Solo aplicar logica extendida para modo lectura
            if mode != 'read':
                raise

            # El usuario debe ser interno (empleado)
            if not self.env.user.has_group('base.group_user'):
                raise

            # Si es superusuario o sistema, no deberia haber llegado aqui
            if self.env.is_superuser() or self.env.is_system():
                raise

            # Verificar cada adjunto individualmente
            if not self:
                return True

            self.flush(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute(
                'SELECT id, res_model, res_id, create_uid, public, res_field '
                'FROM ir_attachment WHERE id IN %s',
                [tuple(self.ids)]
            )
            attachment_data = self._cr.fetchall()

            for att_id, res_model, res_id, create_uid, public, res_field in attachment_data:

                # Los adjuntos publicos son legibles por todos
                if public:
                    continue

                # CASO 1: Adjunto vinculado a un registro padre (res_model + res_id)
                if res_model and res_id and res_model in self.env:
                    try:
                        records = self.env[res_model].browse(res_id).exists()
                        if records:
                            records.check_access_rights('read')
                            records.check_access_rule('read')
                            # El usuario tiene acceso al registro padre -> permite lectura
                            continue
                        else:
                            # El registro padre fue eliminado, permitir lectura
                            # del adjunto huerfano a usuarios internos
                            continue
                    except AccessError:
                        # El usuario NO tiene acceso al registro padre
                        _logger.warning(
                            "AccessError: usuario %s no tiene acceso de lectura al "
                            "registro %s,%s para adjunto %s",
                            self.env.uid, res_model, res_id, att_id
                        )
                        raise

                # CASO 2: Adjunto con res_field (campo binario almacenado como adjunto)
                # En Odoo, fields.Image y fields.Binary con attachment=True crean
                # adjuntos con res_field. Permitimos lectura si el usuario tiene
                # acceso al registro padre.
                if res_field and res_model and res_id and res_model in self.env:
                    try:
                        records = self.env[res_model].browse(res_id).exists()
                        if records:
                            records.check_access_rights('read')
                            records.check_access_rule('read')
                            continue
                        else:
                            continue
                    except AccessError:
                        raise

                # CASO 3: Adjunto huerfano (sin res_model/res_id)
                # Esto ocurre con Many2many(ir.attachment) usando widget many2many_binary
                # El adjunto esta vinculado solo a traves de la tabla de relacion.
                # Buscamos si esta en una relacion Many2many con un registro accesible.
                if self._check_orphan_attachment_access(att_id):
                    continue

                # Si ninguna verificacion paso, denegar acceso
                _logger.warning(
                    "AccessError: usuario %s no puede leer adjunto huerfano %s "
                    "(creado por %s)",
                    self.env.uid, att_id, create_uid
                )
                raise

            return True

    def _check_orphan_attachment_access(self, attachment_id):
        """Verifica si un adjunto huerfano esta vinculado a un registro
        accesible via una relacion Many2many.

        Busca en las tablas de relacion Many2many de los modelos principales
        del proyecto para determinar si el adjunto pertenece a un registro
        que el usuario actual puede leer.
        """
        # Tablas de relacion Many2many(ir.attachment) en el proyecto
        # Estas se extraen de las definiciones de campos en los modelos
        many2many_relations = [
            # professional_request -> attachment_ids
            {
                'table': 'professional_registers_professional_request_ir_attachment_rel',
                'model': 'professional_registers.professional_request',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_professional_request_id',
            },
            # professional_request -> certificate_attachment
            {
                'table': 'professional_ir_attachments_rel',
                'model': 'professional_registers.professional_request',
                'att_column': 'attachment_id',
                'rec_column': 'professional_id',
            },
            # professional_request_update -> attachment_ids
            {
                'table': 'professional_request_upd_attach',
                'model': 'professional_registers.professional_request_update',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_professional_request_update_id',
            },
            # professional_request_update -> certificate_attachment
            {
                'table': 'professional_request_upd_cert_attach',
                'model': 'professional_registers.professional_request_update',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_professional_request_update_id',
            },
            # claim_request -> evidence_attachment_ids
            {
                'table': 'professional_registers_claim_request_ir_attachment_rel',
                'model': 'professional_registers.claim_request',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_claim_request_id',
            },
            # pr_document -> attachment_ids
            {
                'table': 'professional_registers_pr_document_ir_attachment_rel',
                'model': 'professional_registers.pr_document',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_pr_document_id',
            },
            # profile -> attachment_ids
            {
                'table': 'professional_registers_profile_ir_attachment_rel',
                'model': 'professional_registers.profile',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_profile_id',
            },
            # inscription -> certificate_attachment
            {
                'table': 'professional_registers_inscription_ir_attachment_rel',
                'model': 'professional_registers.inscription',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_inscription_id',
            },
            # expedient_communication -> attachment_ids
            {
                'table': 'professional_expedient_comm_attachment_rel',
                'model': 'professional_registers.expedient_communication',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_expedient_communication_id',
            },
            # base_process_request -> attachment_ids
            {
                'table': 'professional_registers_base_process_request_ir_attachment_rel',
                'model': 'professional_registers.base_process_request',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_base_process_request_id',
            },
            # solicitud.observacion.wizard -> attachment_ids
            {
                'table': 'solicitud_observacion_wizard_attachment_rel',
                'model': 'solicitud.observacion.wizard',
                'att_column': 'attachment_id',
                'rec_column': 'wizard_id',
            },
            # side_notes -> attachment_ids
            {
                'table': 'professional_registers_side_notes_ir_attachment_rel',
                'model': 'professional_registers.side_notes',
                'att_column': 'ir_attachment_id',
                'rec_column': 'professional_registers_side_notes_id',
            },
        ]

        for rel in many2many_relations:
            try:
                # Verificar si la tabla existe
                self._cr.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = %s)",
                    [rel['table']]
                )
                if not self._cr.fetchone()[0]:
                    continue

                # Verificar si las columnas existen
                self._cr.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = %s AND column_name IN %s",
                    [rel['table'], (rel['att_column'], rel['rec_column'])]
                )
                existing_columns = set(row[0] for row in self._cr.fetchall())
                if rel['att_column'] not in existing_columns or rel['rec_column'] not in existing_columns:
                    # Intentar con nombres de columna alternativos
                    # Odoo puede generar nombres diferentes
                    self._cr.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = %s",
                        [rel['table']]
                    )
                    all_columns = [row[0] for row in self._cr.fetchall()]
                    if len(all_columns) >= 2:
                        # Usar las dos columnas disponibles
                        alt_att_col = None
                        alt_rec_col = None
                        for col in all_columns:
                            if 'attachment' in col or 'ir_attachment' in col:
                                alt_att_col = col
                            else:
                                alt_rec_col = col
                        if alt_att_col and alt_rec_col:
                            rel = dict(rel, att_column=alt_att_col, rec_column=alt_rec_col)
                        else:
                            continue
                    else:
                        continue

                # Buscar si el adjunto esta en esta relacion
                self._cr.execute(
                    "SELECT {rec_column} FROM {table} "
                    "WHERE {att_column} = %s LIMIT 1".format(**rel),
                    [attachment_id]
                )
                row = self._cr.fetchone()
                if row:
                    record_id = row[0]
                    model_name = rel['model']
                    if model_name in self.env:
                        try:
                            records = self.env[model_name].browse(record_id).exists()
                            if records:
                                records.check_access_rights('read')
                                records.check_access_rule('read')
                                # El usuario tiene acceso al registro vinculado
                                return True
                        except AccessError:
                            # No tiene acceso a este registro, seguir buscando
                            continue
                        except Exception:
                            continue
            except Exception as e:
                _logger.debug(
                    "Error verificando relacion %s para adjunto %s: %s",
                    rel['table'], attachment_id, str(e)
                )
                continue

        return False
