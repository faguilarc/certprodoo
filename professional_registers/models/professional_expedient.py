from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError, UserError
import zipfile
import io
import base64
import logging
import re
from datetime import datetime

class ProfessionalExpedient(models.Model):
    _name = 'professional_registers.expedient'
    _description = 'Expediente del Profesional'
    _rec_name = 'expedient_number'
    _order = 'date_open desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    expedient_number = fields.Char('Número de Expediente', required=True, copy=False, readonly=True, default='New')
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
    professional_id = fields.Many2one('professional_registers.profile', string='Profesional', required=True)
    profile_full_name = fields.Char(
        string='Nombre Completo',
        related='professional_id.full_name',
        readonly=True,
        store=True
    )
    profile_identity = fields.Char(
        string='Carnet de Identidad',
        related='professional_id.identity',
        readonly=True,
        store=True
    )
    profile_id_fuc = fields.Char(
        string='ID FUC',
        related='professional_id.id_fuc',
        readonly=True,
        store=True
    )
    profile_image = fields.Image(
        string='Foto del Profesional',
        related='professional_id.image',
        readonly=True
    )
    date_open = fields.Datetime('Fecha de Apertura', default=fields.Datetime.now, required=True)
    date_close = fields.Datetime('Fecha de Cierre')
    user_open = fields.Many2one('res.users', string='Abierto por', default=lambda self: self.env.user)
    user_close = fields.Many2one('res.users', string='Cerrado por')

    # Estados del expediente
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('pending', 'Pendiente'),
        ('closed', 'Cerrado'),
        ('archived', 'Archivado'),
    ], string='Estado', default='draft', tracking=True)

    # Relaciones con otros modelos
    request_ids = fields.One2many('professional_registers.professional_request', 'expedient_id', string='Solicitudes')
    inscription_ids = fields.One2many('professional_registers.inscription', 'expedient_id', string='Inscripciones')
    update_ids = fields.One2many('professional_registers.professional_request_update', 'expedient_id',
                                 string='Actualizaciones')
    claim_ids = fields.One2many('professional_registers.claim_request', 'expedient_id', string='Reclamaciones')

    # Historial del expediente
    history_ids = fields.One2many('professional_registers.expedient_history', 'expedient_id', string='Historial')

    # Documentos y comunicaciones
    document_ids = fields.One2many('professional_registers.expedient_document', 'expedient_id', string='Documentos')
    communication_ids = fields.One2many('professional_registers.expedient_communication', 'expedient_id',
                                        string='Comunicaciones')

    # Observaciones
    notes = fields.Text('Notas y Observaciones')

    request_count = fields.Integer('Nº de Solicitudes', compute='_compute_request_count')
    inscription_count = fields.Integer('Nº de Inscripciones', compute='_compute_inscription_count')
    document_count = fields.Integer('Nº de Documentos', compute='_compute_document_count')
    update_count = fields.Integer('Nº de Actualizaciones', compute='_compute_update_count')
    claim_count = fields.Integer('Nº de Reclamaciones', compute='_compute_claim_count')
    communication_count = fields.Integer('Nº de Comunicaciones', compute='_compute_communication_count')

    # Campos para mostrar resultados de la búsqueda
    found_requests = fields.Integer('Solicitudes Encontradas', readonly=True)
    found_inscriptions = fields.Integer('Inscripciones Encontradas', readonly=True)
    found_updates = fields.Integer('Actualizaciones Encontradas', readonly=True)
    found_claims = fields.Integer('Reclamaciones Encontradas', readonly=True)
    found_mails = fields.Integer('Correos Encontrados', readonly=True)

    # Campos para controlar la carga
    loading_records = fields.Boolean('Cargando Registros', readonly=True)
    last_load_date = fields.Datetime('Última Carga', readonly=True)
    dms_directory_id = fields.Many2one('dms.directory', string='Carpeta DMS', copy=False)

    @api.depends('professional_id')
    def action_load_associated_records(self):
        """
        Método genérico que decide qué criterio usar.
        Prioriza profile_id si existe, sino usa identity.
        """
        self.ensure_one()

        if self.professional_id:
            # Si hay perfil, usar profile_id para buscar requests
            return self._execute_load_logic(profile_id=self.professional_id.id, identity=None)
        elif hasattr(self, 'identity') and self.identity:
            # Si no hay perfil pero hay identity, usar identity
            return self._execute_load_logic(profile_id=None, identity=self.identity)
        else:
            raise ValidationError("No se puede determinar el criterio de búsqueda (ni perfil ni identidad).")

    def _execute_load_logic(self, profile_id=None, identity=None):
        """
        Lógica central de carga.
        1. Busca requests por profile_id O identity
        2. Obtiene updates/claims/inscripciones mediante relaciones con esos requests
        """
        self.write({'loading_records': True})

        try:
            # Inicializar contadores
            request_count = 0
            inscription_count = 0
            update_count = 0
            claim_count = 0

            # 1. Buscar y asociar solicitudes (por profile_id O identity)
            requests = self._search_and_link_requests(profile_id=profile_id, identity=identity)
            request_count = len(requests)

            # 2. Buscar y asociar inscripciones (mediante request_id de los requests encontrados)
            inscriptions = self._search_and_link_inscriptions(profile_id=profile_id, identity=identity)
            inscription_count = len(inscriptions)

            # 3. Buscar y asociar actualizaciones (mediante original_request_id de los requests encontrados)
            updates = self._search_and_link_updates(profile_id=profile_id, identity=identity)
            update_count = len(updates)

            # 4. Buscar y asociar reclamaciones (mediante original_request_id de los requests encontrados)
            claims = self._search_and_link_claims(profile_id=profile_id, identity=identity)
            claim_count = len(claims)

            # 5. Buscar y asociar correos
            mails = self.action_load_communications()
            mails_count = len(mails) if isinstance(mails, (list, tuple)) else 0

            # Actualizar contadores y fecha
            self.write({
                'found_requests': request_count,
                'found_inscriptions': inscription_count,
                'found_updates': update_count,
                'found_claims': claim_count,
                'found_mails': mails_count,
                'last_load_date': fields.Datetime.now(),
                'loading_records': False,
            })

            # Registrar en el historial
            mode_msg = "Perfil" if profile_id else "Identidad"
            self._add_history(
                f'Carga de Registros (Por {mode_msg})',
                f"Se han cargado {request_count} solicitudes, {inscription_count} inscripciones, {update_count} actualizaciones, {claim_count} reclamaciones y {mails_count} correos."
            )
            self.action_sync_documents()



        except Exception as e:
            self.write({'loading_records': False})
            raise ValidationError(f"Error al cargar registros asociados: {str(e)}")

    def _search_and_link_requests(self, profile_id=None, identity=None):
        """Busca y asocia solicitudes por profile_id o identity."""
        requests = []
        if profile_id:
            requests = self.env['professional_registers.professional_request'].search(
                [('expedient_id', '=', False), ('profile_id', '=', profile_id)])
        elif identity:

            requests = self.env['professional_registers.professional_request'].search(
                [('expedient_id', '=', False), ('identity', '=', identity)])
        else:
            return self.env['professional_registers.professional_request']

        for req in requests:
            req.write({'expedient_id': self.id})
        return requests

    def _search_and_link_inscriptions(self, profile_id=None, identity=None):
        """Busca y asocia inscripciones por profile_id o identity."""
        domain = [('expedient_id', '=', False)]
        if profile_id:
            # Asumiendo que inscription tiene campo profile_id
            domain.append(('profile_id', '=', profile_id))
        elif identity:
            domain.append(('identity', '=', identity))
        else:
            return self.env['professional_registers.inscription']

        inscriptions = self.env['professional_registers.inscription'].search(domain)
        for ins in inscriptions:
            ins.write({'expedient_id': self.id})
        return inscriptions

    def _search_and_link_updates(self, profile_id=None, identity=None):
        """Busca y asocia actualizaciones relacionadas con solicitudes del perfil/identidad."""
        # 1. Obtener solicitudes originales por perfil o identidad
        req_domain = []
        if profile_id:
            req_domain.append(('profile_id', '=', profile_id))
        elif identity:
            req_domain.append(('identity', '=', identity))
        else:
            return self.env['professional_registers.professional_request_update']

        original_requests = self.env['professional_registers.professional_request'].search(req_domain)

        # 2. Buscar updates vinculados a esas solicitudes
        updates = self.env['professional_registers.professional_request_update'].search([
            ('original_request_id', 'in', original_requests.ids),
            ('expedient_id', '=', False)
        ])

        for upd in updates:
            upd.write({'expedient_id': self.id})
        return updates

    def _search_and_link_claims(self, profile_id=None, identity=None):

        """Busca y asocia reclamaciones relacionadas con solicitudes del perfil/identidad."""
        # 1. Obtener solicitudes originales por perfil o identidad
        req_domain = []
        if profile_id:
            req_domain.append(('profile_id', '=', profile_id))
        elif identity:
            req_domain.append(('identity', '=', identity))
        else:
            return self.env['professional_registers.professional_request_update']

        """Busca y asocia reclamaciones por identity"""
        # Buscar solicitudes originales con ese identity
        original_requests = self.env['professional_registers.professional_request'].search(req_domain)

        # Buscar reclamaciones asociadas a esas solicitudes
        claims = self.env['professional_registers.claim_request'].search([
            ('original_request_id', 'in', original_requests.ids),
            ('expedient_id', '=', False)  # Solo las que no tienen expediente asociado
        ])

        # Asociar las reclamaciones encontradas a este expediente
        if claims:
            for n in claims:
                n.write({'expedient_id': self.id})

        return claims

    def action_load_by_profile(self):
        """
        Carga registros asociados FORZANDO la búsqueda por profile_id en los requests.
        Luego obtiene updates/claims/inscripciones mediante sus relaciones con esos requests.
        """
        self.ensure_one()
        if not self.professional_id:
            raise ValidationError("No hay perfil asociado a este expediente.")

        return self._execute_load_logic(profile_id=self.professional_id.id, identity=None)

    def action_load_by_identity(self):
        """
        Carga registros asociados al identity ingresado manualmente
        """
        # Si no hay campo identity en el expediente, necesitamos pedirlo
        if not hasattr(self, 'identity') or not self.identity:
            # Abrir un wizard para ingresar el identity
            return {
                'name': 'Cargar por Identity',
                'type': 'ir.actions.act_window',
                'res_model': 'expedient.load.identity.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_expedient_id': self.id,
                }
            }

        # Usar el método principal con el identity del expediente
        return self.action_load_associated_records()

    def action_auto_load_on_create(self):
        """
        Se ejecuta automáticamente al crear el expediente si hay perfil asociado
        """
        if self.professional_id and self.state == 'open':
            try:
                self.action_load_associated_records()
            except Exception:
                # No bloquear la creación del expediente si falla la carga
                pass

    @api.depends('request_ids')
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.request_ids)

    @api.depends('communication_ids')
    def _compute_communication_count(self):
        for record in self:
            record.communication_count = len(record.communication_ids)

    @api.depends('inscription_ids')
    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    # Documentos por tipo
    docs_request_count = fields.Integer('Documentos de Solicitudes', compute='_compute_document_count')
    docs_certificate_count = fields.Integer('Certificados', compute='_compute_document_count')
    docs_identification_count = fields.Integer('Identificación', compute='_compute_document_count')
    docs_academic_count = fields.Integer('Académicos', compute='_compute_document_count')
    docs_laboral_count = fields.Integer('Laborales', compute='_compute_document_count')
    docs_communication_count = fields.Integer('Comunicaciones', compute='_compute_document_count')
    docs_other_count = fields.Integer('Otros', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)
            record.docs_request_count = len(record.document_ids.filtered(lambda d: d.document_type == 'request'))
            record.docs_certificate_count = len(
                record.document_ids.filtered(lambda d: d.document_type == 'certificate'))
            record.docs_identification_count = len(
                record.document_ids.filtered(lambda d: d.document_type == 'identification'))
            record.docs_academic_count = len(record.document_ids.filtered(lambda d: d.document_type == 'academic'))
            record.docs_laboral_count = len(record.document_ids.filtered(lambda d: d.document_type == 'laboral'))
            record.docs_communication_count = len(
                record.document_ids.filtered(lambda d: d.document_type == 'communication'))
            record.docs_other_count = len(record.document_ids.filtered(lambda d: d.document_type == 'other'))

    @api.depends('update_ids')
    def _compute_update_count(self):
        for record in self:
            record.update_count = len(record.update_ids)

    @api.depends('claim_ids')
    def _compute_claim_count(self):
        for record in self:
            record.claim_count = len(record.claim_ids)

    def action_view_documents(self):
        """Abre la vista de documentos del expediente"""
        return {
            'name': 'Documentos del Expediente',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.expedient_document',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {
                'default_expedient_id': self.id,
                'search_default_group_document_type': 1,
            }
        }

    def action_view_communications(self):
        """Abre la vista de comunicaciones del expediente"""
        return {
            'name': 'Comunicaciones del Expediente',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.expedient_communication',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {
                'default_expedient_id': self.id,
                'search_default_group_communication_type': 1,
            }
        }

    def action_view_history(self):
        """Abre la vista de historial del expediente"""
        return {
            'name': 'Historial del Expediente',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.expedient_history',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {
                'default_expedient_id': self.id,
            }
        }

    @api.model
    def create(self, vals):
        if vals.get('expedient_number', 'Nuevo') == 'Nuevo':
            vals['expedient_number'] = self.env['ir.sequence'].next_by_code('professional_registers.expedient') or 'New'
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id

        expedient = super(ProfessionalExpedient, self).create(vals)
        # Crear estructura de carpetas DMS
        expedient._create_expedient_folder_structure()

        return expedient

    def write(self, vals):
        res = super(ProfessionalExpedient, self).write(vals)

        return res

    def action_open(self):
        if self.professional_id:
            # Si hay perfil, usar profile_id para buscar requests
            self._execute_load_logic(profile_id=self.professional_id.id, identity=None)
        elif hasattr(self, 'identity') and self.identity:
            # Si no hay perfil pero hay identity, usar identity
            self._execute_load_logic(profile_id=None, identity=self.identity)
        else:
            raise ValidationError("No se puede determinar el criterio de búsqueda (ni perfil ni identidad).")
        self.write({'state': 'open'})
        self._add_history('Expediente abierto', 'El expediente ha sido abierto para su procesamiento')

        # Crear carpetas para las solicitudes cargadas
        for request in self.request_ids:
            self._create_request_folder_structure(request.id)

        self.action_organize_documents_by_type()

    def action_close(self):
        self.write({
            'state': 'closed',
            'date_close': fields.Datetime.now(),
            'user_close': self.env.user.id
        })
        self._add_history('Expediente cerrado', 'El expediente ha sido cerrado')

    def action_archive(self):
        self.write({'state': 'archived'})
        self._add_history('Expediente archivado', 'El expediente ha sido archivado')

    def _add_history(self, title, description):
        self.env['professional_registers.expedient_history'].create({
            'expedient_id': self.id,
            'title': title,
            'description': description,
            'user_id': self.env.user.id,
        })

    def action_view_requests(self):
        return {
            'name': 'Solicitudes del Expediente',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {'default_expedient_id': self.id}
        }

    def action_view_inscriptions(self):
        return {
            'name': 'Inscripciones del Expediente',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.inscription',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {'default_expedient_id': self.id}
        }

    def action_view_updates(self):
        """Abre la vista de actualizaciones del expediente"""
        self.ensure_one()

        return {
            'name': f'Actualizaciones del Expediente ({self.update_count})',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request_update',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {
                'default_expedient_id': self.id,
                'search_default_group_update_type': 1,
            }
        }

    def action_view_claims(self):
        """Abre la vista de reclamaciones del expediente"""
        self.ensure_one()

        return {
            'name': f'Reclamaciones del Expediente ({self.claim_count})',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.claim_request',
            'view_mode': 'tree,form',
            'domain': [('expedient_id', '=', self.id)],
            'context': {
                'default_expedient_id': self.id,
                'search_default_group_claim_type': 1,
            }
        }

    def action_load_communications(self):
        """
        Carga todas las comunicaciones relacionadas con el profesional
        """
        self.ensure_one()

        try:
            # Obtener el email del profesional
            professional_email = self.professional_id.email
            if not professional_email:
                raise ValidationError("No se puede determinar el correo electrónico del profesional.")

            # Eliminar comunicaciones existentes para evitar duplicados
            self.env['professional_registers.expedient_communication'].search([
                ('expedient_id', '=', self.id)
            ]).unlink()

            # 1. Buscar en mail.message
            messages, mails = self._get_all_emails(self.professional_id)
            for message in messages:
                self.env['professional_registers.expedient_communication'].create_from_mail_message(message, self.id)

            for mail in mails:
                self.env['professional_registers.expedient_communication'].create_from_mail_mail(mail, self.id)

            # Registrar en el historial
            total_count = len(messages) + len(mails)
            self._add_history(
                'Carga de Comunicaciones',
                f"Se han cargado {total_count} comunicaciones relacionadas."
            )



        except Exception as e:
            raise ValidationError(f"Error al cargar comunicaciones: {str(e)}")

    def _get_all_emails(self, professional):
        """Obtiene TODOS los correos (enviados, recibidos y pendientes)"""

        # Validar que el profesional tenga partner
        if not professional.user_id.partner_id:
            raise ValueError("El profesional debe tener un partner asociado")

        partner_id = professional.user_id.partner_id.id

        # --- Búsqueda en mail.message (correos ya enviados) ---
        messages = self.env['mail.message'].sudo().search([
            ('author_id', '=', partner_id),
            ('message_type', '=', 'email')
        ])

        # --- Búsqueda en mail.mail (correos pendientes) ---
        mails = self.env['mail.mail'].sudo().search([
            '|',
            ('author_id', '=', partner_id),
            ('email_to', 'ilike', professional.email)
        ])

        return messages, mails

    def action_sync_documents(self):
        """
        Sincroniza todos los documentos de solicitudes, actualizaciones,
        reclamaciones e inscripciones al expediente.
        """
        self.ensure_one()
        documents_created = 0

        for request in self.request_ids:
            # 1. Documentos directos de la solicitud (attachment_ids)
            for att in request.attachment_ids:
                existing = self.env['professional_registers.expedient_document'].search([
                    ('expedient_id', '=', self.id),
                    ('attachment_id', '=', att.id)
                ], limit=1)
                if not existing:
                    self.env['professional_registers.expedient_document'].create({
                        'expedient_id': self.id,
                        'name': att.name,
                        'attachment_id': att.id,
                        'document_type': 'request',
                        'source_model': 'professional_registers.professional_request',
                        'source_id': request.id,
                        'user_id': att.create_uid.id,
                    })
                    documents_created += 1

            # 2. Documentos requeridos de la solicitud (pr_document)
            for pr_doc in request.documents_required:
                for att in pr_doc.attachment_ids:
                    existing = self.env['professional_registers.expedient_document'].search([
                        ('expedient_id', '=', self.id),
                        ('attachment_id', '=', att.id)
                    ], limit=1)
                    if not existing:
                        doc_name = pr_doc.documents.name if pr_doc.documents else att.name
                        self.env['professional_registers.expedient_document'].create({
                            'expedient_id': self.id,
                            'name': doc_name,
                            'attachment_id': att.id,
                            'document_type': 'request',
                            'source_model': 'professional_registers.professional_request',
                            'source_id': request.id,
                            'user_id': att.create_uid.id,
                        })
                        documents_created += 1

        for update in self.update_ids:
            # 3. Documentos de actualizaciones
            for att in update.attachment_ids:
                existing = self.env['professional_registers.expedient_document'].search([
                    ('expedient_id', '=', self.id),
                    ('attachment_id', '=', att.id)
                ], limit=1)
                if not existing:
                    self.env['professional_registers.expedient_document'].create({
                        'expedient_id': self.id,
                        'name': att.name,
                        'attachment_id': att.id,
                        'document_type': 'communication',
                        'source_model': 'professional_registers.professional_request_update',
                        'source_id': update.id,
                        'user_id': att.create_uid.id,
                    })
                    documents_created += 1

            # 4. Certificaciones de actualizaciones
            for att in update.certificate_attachment:
                existing = self.env['professional_registers.expedient_document'].search([
                    ('expedient_id', '=', self.id),
                    ('attachment_id', '=', att.id)
                ], limit=1)
                if not existing:
                    self.env['professional_registers.expedient_document'].create({
                        'expedient_id': self.id,
                        'name': f"Certificación - {att.name}",
                        'attachment_id': att.id,
                        'document_type': 'certificate',
                        'source_model': 'professional_registers.professional_request_update',
                        'source_id': update.id,
                        'user_id': att.create_uid.id,
                    })
                    documents_created += 1

        for claim in self.claim_ids:
            # 5. Evidencias de reclamaciones
            for att in claim.evidence_attachment_ids:
                existing = self.env['professional_registers.expedient_document'].search([
                    ('expedient_id', '=', self.id),
                    ('attachment_id', '=', att.id)
                ], limit=1)
                if not existing:
                    self.env['professional_registers.expedient_document'].create({
                        'expedient_id': self.id,
                        'name': f"Reclamación - {att.name}",
                        'attachment_id': att.id,
                        'document_type': 'communication',
                        'source_model': 'professional_registers.claim_request',
                        'source_id': claim.id,
                        'user_id': att.create_uid.id,
                    })
                    documents_created += 1

        for inscription in self.inscription_ids:
            # 6. Certificados de inscripciones
            for att in inscription.certificate_attachment:
                existing = self.env['professional_registers.expedient_document'].search([
                    ('expedient_id', '=', self.id),
                    ('attachment_id', '=', att.id)
                ], limit=1)
                if not existing:
                    self.env['professional_registers.expedient_document'].create({
                        'expedient_id': self.id,
                        'name': f"Inscripción - {att.name}",
                        'attachment_id': att.id,
                        'document_type': 'certificate',
                        'source_model': 'professional_registers.inscription',
                        'source_id': inscription.id,
                        'user_id': att.create_uid.id,
                    })
                    documents_created += 1

        # Registrar en historial
        self._add_history(
            'Documentos sincronizados',
            f"Se han sincronizado {documents_created} documentos al expediente."
        )

        self.action_organize_documents_by_type()

    def get_all_documents_tree(self):
        """
        Retorna estructura de carpetas para vista kanban/tree
        """
        self.ensure_one()
        tree = []

        # Carpetas por tipo de documento
        folders = {
            'request': {'name': 'Solicitudes', 'documents': [], 'icon': 'fa-clipboard'},
            'certificate': {'name': 'Certificados', 'documents': [], 'icon': 'fa-graduation-cap'},
            'identification': {'name': 'Identificación', 'documents': [], 'icon': 'fa-id-card'},
            'academic': {'name': 'Académicos', 'documents': [], 'icon': 'fa-book'},
            'laboral': {'name': 'Laborales', 'documents': [], 'icon': 'fa-briefcase'},
            'communication': {'name': 'Comunicaciones', 'documents': [], 'icon': 'fa-envelope'},
            'other': {'name': 'Otros', 'documents': [], 'icon': 'fa-file'},
        }

        for doc in self.document_ids:
            doc_type = doc.document_type or 'other'
            if doc_type in folders:
                folders[doc_type]['documents'].append({
                    'id': doc.id,
                    'name': doc.name,
                    'date': doc.date,
                    'user_id': doc.user_id.name,
                    'attachment_id': doc.attachment_id.id,
                })

        # Convertir a lista
        for folder in folders.values():
            if folder['documents']:
                tree.append(folder)

        return tree

    # Funciones asociadas al directorio de expedientes

    def _create_dms_structure(self):
        """
        Crea la estructura de carpetas DMS para el expediente con una jerarquía completa.
        Estructura:
        - Expediente (raíz)
          - Solicitudes
            - [Número de Solicitud]
              - Actualizaciones
                - [Número de Actualización]
              - Reclamaciones
                - [Número de Reclamación]
              - Denegadas
              - Canceladas
              - Aprobadas
                - [Número de Inscripción]
          - Correos
          - Otros Documentos
        """
        self.ensure_one()

        try:
            # 1. Validar que el módulo DMS esté instalado
            if not self.env.registry.get('dms.directory'):
                raise UserError("El módulo DMS no está instalado. Contacte al administrador.")

            # 2. Obtener o crear almacenamiento
            storage = self._get_or_create_default_storage()

            # 3. Obtener o crear directorio raíz
            root = self.env['dms.directory'].sudo().search([
                ('name', '=', 'Expedientes'),
                ('is_root_directory', '=', True),
                ('storage_id', '=', storage.id)
            ], limit=1)

            if not root:
                # Crear raíz si no existe
                root = self.env['dms.directory'].sudo().create({
                    'name': 'Expedientes',
                    'is_root_directory': True,
                    'storage_id': storage.id,
                })

            # 4. Verificar si ya existe carpeta para este expediente
            existing_dir = self.env['dms.directory'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('parent_id', '=', root.id)
            ], limit=1)

            if existing_dir:
                self.dms_directory_id = existing_dir
                return existing_dir

            # 5. CREAR GRUPO DE ACCESO DMS
            dms_access_group_id = self._get_or_create_dms_access_group()

            # 6. Crear carpeta del expediente con el grupo de acceso
            expedient_dir = self.env['dms.directory'].sudo().create({
                'name': self._get_folder_name(),
                'parent_id': root.id,
                'res_model': self._name,
                'res_id': self.id,
                'group_ids': [(6, 0, [dms_access_group_id])],
            })

            # 7. Crear carpetas principales
            solicitudes_dir = self._create_directory_if_not_exists(
                'Solicitudes', expedient_dir, dms_access_group_id)
            correos_dir = self._create_directory_if_not_exists(
                'Correos', expedient_dir, dms_access_group_id)
            otros_dir = self._create_directory_if_not_exists(
                'Otros Documentos', expedient_dir, dms_access_group_id)

            # 8. Guardar referencia en el expediente
            self.write({'dms_directory_id': expedient_dir.id})

            # 9. Registrar en historial
            self._add_history(
                'Estructura DMS Creada',
                f'Se ha creado la estructura de carpetas DMS para el expediente {self.expedient_number}'
            )

            # 10. Organizar documentos existentes
            self.action_organize_documents_by_type()

            return expedient_dir

        except Exception as e:
            raise UserError(f"Error al crear estructura DMS: {str(e)}")

    def _create_directory_if_not_exists(self, name, parent_dir, group_id=None):
        """Crea un directorio si no existe"""
        existing = self.env['dms.directory'].sudo().search([
            ('name', '=', name),
            ('parent_id', '=', parent_dir.id)
        ], limit=1)

        if not existing:
            vals = {
                'name': name,
                'parent_id': parent_dir.id,
            }
            if group_id:
                vals['group_ids'] = [(6, 0, [group_id])]

            existing = self.env['dms.directory'].sudo().create(vals)

        return existing

    def action_open_dms_directory(self):
        """
        Abre la vista de carpetas DMS para este expediente.
        """
        self.ensure_one()

        if not self.dms_directory_id:
            self._create_expedient_folder_structure()

        return {
            'type': 'ir.actions.act_window',
            'name': f'Carpetas del Expediente {self.expedient_number}',
            'res_model': 'dms.directory',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'child_of', self.dms_directory_id.id)],
            'context': {
                'default_parent_id': self.dms_directory_id.id,
                'search_default_parent_id': self.dms_directory_id.id,
            },
        }

    def _get_or_create_subdir(self, name, parent=None):
        """Obtiene o crea una subcarpeta dentro del directorio del expediente"""
        if parent is None:
            parent = self.dms_directory_id
        if not parent:
            return False
        directory = self.env['dms.directory'].search([
            ('name', '=', name),
            ('parent_id', '=', parent.id)
        ], limit=1)
        if not directory:
            directory = self.env['dms.directory'].sudo().create({
                'name': name,
                'parent_id': parent.id,
            })
        return directory

    def action_export_zip(self):
        self.ensure_one()
        if not self.dms_directory_id:
            raise UserError("No hay carpeta DMS asociada.")


        _logger = logging.getLogger(__name__)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            # 1. Obtener TODOS los directorios hijos (incluyendo el raíz del expediente)
            # Usamos child_of para obtener la jerarquía completa
            all_directories = self.env['dms.directory'].search([
                ('id', 'child_of', self.dms_directory_id.id)
            ])

            _logger.info(f"Exportando ZIP para {self.expedient_number}: Procesando {len(all_directories)} directorios.")

            for directory in all_directories:
                # Construir la ruta relativa de la carpeta desde el directorio raíz del expediente
                path_parts = []
                current_dir = directory

                # Subimos hasta llegar al directorio raíz del expediente
                while current_dir and current_dir.id != self.dms_directory_id.id:
                    path_parts.insert(0, current_dir.name)
                    current_dir = current_dir.parent_id

                # Si es el directorio raíz, rel_path será vacío, si no, será la ruta de la carpeta
                rel_path = '/'.join(path_parts)

                # Añadir la carpeta al ZIP.
                # Nota: En zipfile, añadir una entrada que termine en '/' crea una carpeta vacía.
                if rel_path:
                    zip_file.writestr(rel_path + '/', '')

                    # 2. Obtener y añadir los archivos de este directorio específico
                files = self.env['dms.file'].search([('directory_id', '=', directory.id)])

                for file in files:
                    # La ruta final del archivo es la ruta de la carpeta + el nombre del archivo
                    file_path = f"{rel_path}/{file.name}" if rel_path else file.name

                    # Obtener contenido: primero del campo content, si está vacío, del attachment_id
                    file_content = file.content
                    if not file_content and file.attachment_id:
                        file_content = file.attachment_id.datas

                    if file_content:
                        try:
                            zip_file.writestr(file_path, base64.b64decode(file_content))
                        except Exception as e:
                            _logger.error(f"Error al añadir '{file.name}' al ZIP: {str(e)}")
                    else:
                        _logger.warning(f"El archivo '{file.name}' (ID: {file.id}) no tiene contenido binario.")

        # Guardar el zip como attachment temporal
        zip_data = base64.b64encode(zip_buffer.getvalue())
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.expedient_number.lower()}_{self.profile_identity}.zip',
            'type': 'binary',
            'datas': zip_data,
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_organize_documents_by_type(self):
        """
        Organiza todos los documentos en la estructura de carpetas DMS
        según su tipo, estado y lógica de negocio granular.
        """
        self.ensure_one()

        if not self.dms_directory_id:
            self._create_dms_structure()

        # Carpeta de correos general del expediente (nivel superior)
        correos_exp_dir = self._get_or_create_subdir('Correos')

        for request in self.request_ids:
            request_dir = self._create_request_folder_structure(request.id)

            # ---------------------------------------------------------
            # A. DOCUMENTOS REQUERIDOS DE LA SOLICITUD (Con nombre personalizado)
            # ---------------------------------------------------------
            req_docs_dir = self._get_subdirectory('Documentos Requeridos', request_dir)
            req_num = request.request_number.replace('/', '-') if request.request_number else 'SN'

            for pr_doc in request.documents_required:
                doc_name = pr_doc.documents.name if pr_doc.documents else "Documento"
                custom_file_name = f"{doc_name}_solicitud_{req_num}".lower()

                for attachment in pr_doc.attachment_ids:
                    self._attach_file_to_directory(attachment, req_docs_dir, custom_name=custom_file_name)

            # ---------------------------------------------------------
            # B. ACTUALIZACIONES (Con sus propias subcarpetas)
            # ---------------------------------------------------------
            updates_dir = self._get_subdirectory('Actualizaciones', request_dir)
            update_ids = self.env['professional_registers.professional_request_update'].search(
                [('original_request_id', '=', request.id)])
            for update in update_ids:
                # Carpeta de la actualización específica
                update_dir = self._create_subdirectory(
                    f"Actualización-{update.request_number}".replace('/', '-'),
                    updates_dir
                )
                # Subcarpetas DENTRO de esta actualización
                update_docs_dir = self._create_subdirectory('Documentos', update_dir)
                update_correos_dir = self._create_subdirectory('Correos', update_dir)

                # Adjuntar documentos a la carpeta de Documentos de ESTA actualización
                for attachment in update.attachment_ids:
                    self._attach_file_to_directory(attachment, update_docs_dir)

            # ---------------------------------------------------------
            # C. RECLAMACIONES (Con sus propias subcarpetas)
            # ---------------------------------------------------------
            claims_dir = self._get_subdirectory('Reclamaciones', request_dir)
            for claim in request.claim_ids:
                # Carpeta de la reclamación específica
                claim_dir = self._create_subdirectory(
                    f"Reclamación-{claim.request_number}".replace('/', '-'),
                    claims_dir
                )
                # Subcarpetas DENTRO de esta reclamación
                claim_docs_dir = self._create_subdirectory('Documentos', claim_dir)
                claim_correos_dir = self._create_subdirectory('Correos', claim_dir)

                # Adjuntar evidencias a la carpeta de Documentos de ESTA reclamación
                for attachment in claim.evidence_attachment_ids:
                    self._attach_file_to_directory(attachment, claim_docs_dir)

            # ---------------------------------------------------------
            # D. INSCRIPCIONES
            # ---------------------------------------------------------
            inscripcion_dir = self._get_subdirectory('Inscripcion', request_dir)
            inscriptions = self.env['professional_registers.inscription'].search([('request_id', '=', request.id)])

            for inscription in inscriptions:
                if inscription.states.priority == 1:  # Aprobada
                    insc_dir = self._get_subdirectory(
                        f"Inscripción-{inscription.inscription_number}".replace('/', '-'),
                        inscripcion_dir
                    )
                    for attachment in inscription.certificate_attachment:
                        self._attach_file_to_directory(attachment, insc_dir)
                elif inscription.states.priority == 8:  # Denegada
                    denegadas_dir = self._get_subdirectory('Denegadas', inscripcion_dir)
                    for attachment in inscription.certificate_attachment:
                        self._attach_file_to_directory(attachment, denegadas_dir)
                elif inscription.states.priority == 2:  # Cancelada
                    canceladas_dir = self._get_subdirectory('Canceladas', inscripcion_dir)
                    for attachment in inscription.certificate_attachment:
                        self._attach_file_to_directory(attachment, canceladas_dir)

        # Organizar comunicaciones/correos generales del expediente
        for comm in self.communication_ids:
            for attachment in comm.attachment_ids:
                self._attach_file_to_directory(attachment, correos_exp_dir)

        self._add_history(
            'Documentos Organizados',
            'Se han organizado todos los documentos en la estructura de carpetas DMS con jerarquía granular por trámite.'
        )

    def _get_folder_name(self):
        """Genera el nombre de la carpeta para el expediente basado en su número y la identidad del profesional."""
        self.ensure_one()
        # Obtener el número de expediente y reemplazar '/' por '-'
        exp_num = self.expedient_number.replace('/', '-') if self.expedient_number else ''
        # Obtener la identidad del profesional (si existe)
        identity = self.professional_id.identity if self.professional_id else ''
        # Si no hay identidad, podríamos usar otro campo o un valor por defecto
        if not identity:
            # Opcional: podrías lanzar un error o usar un valor genérico
            identity = 'sin-identidad'
        # Construir el nombre: EXP-00006-00041067584
        folder_name = f"{exp_num}-{identity}".replace(' ', '')
        # Opcional: convertir a mayúsculas o minúsculas
        return folder_name.upper()  # o .lower() según prefieras

    def _get_or_create_dms_access_group(self):
        """
        Crea o recupera un grupo de acceso DMS que incluye los usuarios
        de tus grupos de seguridad de Odoo.
        Retorna el ID del grupo de acceso DMS.
        """
        self.ensure_one()

        # Nombre único para el grupo de acceso DMS
        dms_group_name = f"Expedientes - Acceso Completo ({self.expedient_number})"

        # 1. Buscar si ya existe un grupo de acceso DMS para este expediente
        dms_group = self.env['dms.access.group'].sudo().search([
            ('name', '=', dms_group_name)
        ], limit=1)

        if dms_group:
            return dms_group.id

        # 2. Lista de tus grupos de seguridad de Odoo (XML IDs)
        security_group_xml_ids = [
            'professional_registers.group_professional_superadmin',
            'professional_registers.group_professional_register_employee',
            'professional_registers.group_professional_editor_managment',
            'professional_registers.group_professional_editor',
            'professional_registers.group_professional_client_online',
        ]

        # 3. Recopilar todos los usuarios de esos grupos
        user_ids = []
        for xml_id in security_group_xml_ids:
            odoo_group = self.env.ref(xml_id, raise_if_not_found=False)
            if odoo_group:
                user_ids.extend(odoo_group.users.ids)

        # 4. Eliminar duplicados
        user_ids = list(set(user_ids))

        # 5. Si no hay usuarios, usar el usuario actual como fallback
        if not user_ids:
            user_ids = [self.env.user.id]

        # 6. Crear el grupo de acceso DMS con permisos completos
        dms_group = self.env['dms.access.group'].sudo().create({
            'name': dms_group_name,
            'explicit_user_ids': [(6, 0, user_ids)],
            # Permisos completos

            'perm_create': True,
            'perm_write': True,
            'perm_unlink': True,
        })

        return dms_group.id

    # Crear almacenamiento por defecto
    def _get_or_create_default_storage(self):
        """Obtiene o crea un almacenamiento por defecto"""
        storage = self.env['dms.storage'].sudo().search([
            ('name', '=', 'almacenamiento-expedientes')
        ], limit=1)

        if not storage:
            storage = self.env['dms.storage'].sudo().create({
                'name': 'almacenamiento-expedientes',
                'save_type': 'database',  # o 'attachment' según configuración
            })
        return storage

    # Crear carpeta root de todos los expedientes
    def _get_or_create_root_directory(self):
        """
        Obtiene o crea la carpeta raíz para todos los expedientes profesionales.
        Esta carpeta es única y contendrá todas las carpetas individuales de expedientes.
        """
        storage = self._get_or_create_default_storage()

        root_dir = self.env['dms.directory'].sudo().search([
            ('name', '=', 'Expedientes Profesionales'),
            ('is_root_directory', '=', True),
            ('storage_id', '=', storage.id)
        ], limit=1)

        if not root_dir:
            root_dir = self.env['dms.directory'].sudo().create({
                'name': 'Expedientes Profesionales',
                'is_root_directory': True,
                'storage_id': storage.id,
            })

        return root_dir

    # Crear expediente individual
    def _create_expedient_directory(self):
        """
        Crea la carpeta individual para este expediente dentro de la estructura raíz.
        """
        self.ensure_one()

        # Obtener o crear la carpeta raíz
        root_dir = self._get_or_create_root_directory()

        # Verificar si ya existe la carpeta para este expediente
        existing_dir = self.env['dms.directory'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('parent_id', '=', root_dir.id)
        ], limit=1)

        if existing_dir:
            return existing_dir

        # Crear grupo de acceso para este expediente
        dms_access_group_id = self._get_or_create_dms_access_group()

        # Crear la carpeta del expediente
        expedient_dir = self.env['dms.directory'].sudo().create({
            'name': self._get_folder_name(),
            'parent_id': root_dir.id,
            'res_model': self._name,
            'res_id': self.id,
            'group_ids': [(6, 0, [dms_access_group_id])],
        })

        # Guardar referencia en el expediente
        self.dms_directory_id = expedient_dir.id

        return expedient_dir

    # Crear la estrctura de carpetas entro del expediente
    def _create_expedient_folder_structure(self):
        """
        Crea la estructura completa de carpetas para este expediente:
        - Solicitudes
          - [Número de Solicitud]
            - Actualizaciones
              - [Número de Actualización]
            - Reclamaciones
              - [Número de Reclamación]
            - Denegadas
            - Canceladas
            - Aprobadas
              - [Número de Inscripción]
        - Correos
        - Documentos Varios
        """
        self.ensure_one()

        # Crear carpeta principal del expediente si no existe
        expedient_dir = self._create_expedient_directory()

        # Crear carpetas principales
        solicitudes_dir = self._create_subdirectory('Solicitudes', expedient_dir)
        correos_dir = self._create_subdirectory('Correos', expedient_dir)
        documentos_dir = self._create_subdirectory('Documentos Varios', expedient_dir)

        return {
            'expedient_dir': expedient_dir,
            'solicitudes_dir': solicitudes_dir,
            'correos_dir': correos_dir,
            'documentos_dir': documentos_dir
        }

    # Crear subcarpetas si no existen
    def _create_subdirectory(self, name, parent_dir):
        """
        Crea una subcarpeta si no existe.
        """
        existing = self.env['dms.directory'].sudo().search([
            ('name', '=', name),
            ('parent_id', '=', parent_dir.id)
        ], limit=1)

        if not existing:
            existing = self.env['dms.directory'].sudo().create({
                'name': name,
                'parent_id': parent_dir.id,
                'group_ids': [(6, 0, parent_dir.group_ids.ids)] if parent_dir.group_ids else [],
            })

        return existing

    # Obtiene una subcarpeta si no existe la crea
    def _get_subdirectory(self, name, parent_dir):
        """
        Obtiene una subcarpeta existente o la crea si no existe.
        """
        existing = self.env['dms.directory'].sudo().search([
            ('name', '=', name),
            ('parent_id', '=', parent_dir.id)
        ], limit=1)

        return existing if existing else self._create_subdirectory(name, parent_dir)

    # Crear estructura de carpetas para la solicitud
    def _create_request_folder_structure(self, request_id):
        """
        Crea la estructura de carpetas de primer nivel para una solicitud específica.
        """
        self.ensure_one()
        request = self.env['professional_registers.professional_request'].browse(request_id)
        if not request:
            return None

        structure = self._create_expedient_folder_structure()
        solicitudes_dir = structure['solicitudes_dir']

        # 1. Carpeta de la solicitud
        request_dir_name = f"Solicitud-{request.request_number}".replace('/', '-')
        request_dir = self._create_subdirectory(request_dir_name, solicitudes_dir)

        # 2. Crear subcarpetas de procesos AL MISMO NIVEL dentro de la solicitud
        act_dir = self._create_subdirectory('Actualizaciones', request_dir)
        self._create_subdirectory('Documentos Requeridos', act_dir)
        self._create_subdirectory('Correos', act_dir)

        rec_dir = self._create_subdirectory('Reclamaciones', request_dir)
        self._create_subdirectory('Documentos Requeridos', rec_dir)
        self._create_subdirectory('Correos', rec_dir)

        self._create_subdirectory('Inscripcion', request_dir)

        # 3. Carpetas para la documentación inicial y correos generales de la solicitud
        self._create_subdirectory('Documentos Requeridos', request_dir)
        self._create_subdirectory('Correos', request_dir)

        # 4. Pre-crear carpetas de inscripciones aprobadas si ya existen
        inscripcion_dir = self._get_subdirectory('Inscripcion', request_dir)
        inscriptions = self.env['professional_registers.inscription'].search([('request_id', '=', request_id)])
        for inscription in inscriptions.filtered(lambda i: i.states.priority == 1):
            self._create_subdirectory(
                f"Inscripción-{inscription.inscription_number}".replace('/', '-'),
                inscripcion_dir
            )

        return request_dir

    # Adjuntar documentos a un directorio
    def _attach_file_to_directory(self, attachment, directory, custom_name=None):
        """
        Crea un archivo DMS a partir de un adjunto en la carpeta indicada.
        Si se pasa custom_name, se usa ese como base del nombre.
        """
        if not attachment or not directory:
            return

        # 1. Verificar si ya existe un archivo con el mismo attachment_id en este directorio
        existing_by_attachment = self.env['dms.file'].sudo().search([
            ('attachment_id', '=', attachment.id),
            ('directory_id', '=', directory.id)
        ], limit=1)

        if existing_by_attachment:
            return  # Ya está vinculado, no hacemos nada

        # 2. Obtener nombre base y extensión
        original_name = attachment.name
        base_name, extension = self._split_filename(original_name)

        # Si se proporciona un nombre personalizado, lo usamos como base (limpiando espacios y barras)
        if custom_name:
            clean_custom_name = custom_name.replace(' ', '_').replace('/', '-')
            base_name = clean_custom_name

        # 3. Buscar archivos con el mismo nombre base en el directorio para evitar duplicados
        domain = [
            ('directory_id', '=', directory.id),
            ('name', '=like', base_name + '%')
        ]
        existing_files = self.env['dms.file'].sudo().search(domain)

        # 4. Determinar nombre único
        if not existing_files:
            new_name = f"{base_name}{extension}"
        else:
            existing_names = existing_files.mapped('name')
            counter = 1
            while True:
                candidate = f"{base_name} ({counter}){extension}"
                if candidate not in existing_names:
                    new_name = candidate
                    break
                counter += 1

        # 5. Crear el archivo DMS con el nombre único
        self.env['dms.file'].sudo().create({
            'name': new_name,
            'content': attachment.datas,
            'mimetype': attachment.mimetype,
            'directory_id': directory.id,
            'attachment_id': attachment.id,
            'res_model': attachment.res_model,
            'res_id': attachment.res_id,
        })

    def _split_filename(self, filename):
        """Devuelve (base_name, extension) donde extensión incluye el punto."""
        if '.' in filename:
            parts = filename.rsplit('.', 1)
            return parts[0], '.' + parts[1]
        else:
            return filename, ''
