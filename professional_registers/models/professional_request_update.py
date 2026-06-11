# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
import json
from lxml import etree

from odoo.exceptions import ValidationError, UserError
from odoo.tools import html_sanitize


class ProfessionalRequestUpdate(models.Model):
    _name = 'professional_registers.professional_request_update'
    _description = 'Solicitud de Actualización de Profesional'
    _rec_name = 'request_number'
    _order = 'date_request desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    request_number = fields.Char('Nro. solicitud', readonly=True)

    original_request_id = fields.Many2one(
        'professional_registers.professional_request',
        string='Solicitud original',

        readonly=True
    )
    profile_id = fields.Many2one(
        'professional_registers.profile',
        string='Perfil asociado',
        readonly=True
    )
    related_image = fields.Image(
        string="Foto",
        compute='_compute_related_image',
        store=True,  # Opcional: si quieres que se almacene en BD
        max_width=1920,
        max_height=1920
    )

    @api.depends('original_request_id.image', 'profile_id.image')
    def _compute_related_image(self):
        for record in self:
            image = False
            if record.original_request_id and record.original_request_id.image:
                image = record.original_request_id.image
            elif record.profile_id and record.profile_id.image:
                image = record.profile_id.image
            # Si no hay imagen, se queda en False (vacío)
            record.related_image = image

    # Campos de control
    date_request = fields.Date('Fecha solicitud', default=lambda self: fields.Date.context_today(self))

    user_id = fields.Many2one('res.users', string="Usuario solicitante", default=lambda self: self.env.user)
    observation = fields.Text('Observación')

    def _get_states(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        # Solo estados 1,2,3,6,8 para actualización
        states = self.env['security.state_configuration'].search(
            [('model', '=', int(model.id)), ('id', 'in', [1, 2, 3, 6, 8])],
            order="priority asc"
        )
        return [('id', 'in', states.ids)]

    def _get_default_value(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([('model', '=', int(model.id))], order="priority asc")
        if states:
            return states[0].id

    # Estados (solo 1,2,3,6,8)
    states = fields.Many2one('security.state_configuration', string='Estados', domain=_get_states,
                             default=_get_default_value)
    priority = fields.Integer('prioridad', default=1)

    # Historial de cambios
    history_ids = fields.One2many(
        'professional_registers.request_update_history',
        'update_id',
        string='Histórico de Cambios de Estado'
    )

    # Campos editables (agrupados por categorías)

    # === Datos Personales ===
    name = fields.Char('Nombre')
    first_last_name = fields.Char('Primer apellido')
    second_last_name = fields.Char('Segundo apellido')
    full_name = fields.Char('Nombre y apellidos', compute='_compute_full_name', store=True)
    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")
    identity = fields.Char('CI o Pasaporte')
    id_fuc = fields.Char('Id FUC')
    sex = fields.Selection([('male', 'Masculino'), ('female', 'Femenino')], string="Sexo")
    address = fields.Text('Dirección particular')
    country = fields.Many2one('res.country', string="País")
    country_states = fields.Many2one('res.country.state', string="Provincia")
    city = fields.Many2one('res.city', string="Municipio")
    phone = fields.Char('Teléfono')
    email = fields.Char('Correo')
    image = fields.Image("Foto", max_width=1920, max_height=1920)
    # === Datos Académicos ===
    teaching_level = fields.Many2one('nomenclators.teaching_level', string="Nivel de enseñanza")
    study_center = fields.Many2one('nomenclators.study_centers', string="Centros de estudios")
    degree_date = fields.Date('Fecha de graduación')
    volume = fields.Char('Tomo')
    folio = fields.Char('Folio')
    number = fields.Char('Número')
    convalidation_degree_tittle = fields.Date('Fecha convalidación de título exp en el extranjero')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    specialties = fields.Many2one('nomenclators.specialties', string="Especialidad")

    # === Datos Científicos y de Investigación ===
    def _get_years(self):
        current_year = datetime.utcnow().year
        years = []
        for year in range(1950, current_year + 1):
            years.append((str(year), str(year)))
        return years

    investigations = fields.Boolean('Investigaciones', tracking=True, default=False)
    investigations_year = fields.Selection(
        selection='_get_years',
        string='Año de la investigación'
    )

    degree_sciences = fields.Selection([('anything', 'Ninguno'), ('esp', 'Esp.'), ('msc', 'Msc.'), ('dr', 'Dr.')],
                                       string="Categoría científica")
    degree_sciences_year = fields.Selection(
        selection='_get_years', string='Año de categoría científica')

    teaching_category = fields.Many2one('nomenclators.teaching_categories', string="Categoría docente")
    teaching_category_date = fields.Date('Fecha de categ. docente')

    unaicc_date = fields.Date('Fecha ingreso UNAICC')

    # === Datos Laborales ===
    retired = fields.Boolean('Jubilado', default=False, tracking=True)
    date = fields.Date('Fecha Jubilación')
    history_work = fields.One2many('professional_registers.work_history', 'update_request',
                                   string="Vinculo laboral")
    professional_language = fields.One2many('nomenclators.professional_language', 'update_request', string="Idioma")

    # === Documentación ===
    attachment_ids = fields.Many2many('ir.attachment', 'professional_request_upd_attach', string="Documentos adjuntos")
    certificate_attachment = fields.Many2many(
        "ir.attachment",
        "professional_update_ir_attachments_rel",
        "update_id",
        "attachment_id",
        "Certificación",
    )

    # === Otros ===
    user = fields.Char('Usuario')
    password = fields.Char('Contraseña')

    # Depurar este atributo no se usa
    documents_required = fields.One2many(
        'professional_registers.pr_document',
        'update_request',
        string="Documentos requeridos"
    )

    user_on_charge = fields.Many2one('res.users', string="Responsable")
    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente')

    def get_procedure_default(self):
        procedure = self.env['nomenclators.procedure_types'].search([('comodel_name', '=', 'update')])
        return procedure.id

    procedure_type = fields.Many2one('nomenclators.procedure_types', string="Tipo de trámite*",
                                     default=get_procedure_default)

    # Métodos para el flujo de estados
    def _get_years(self):
        current_year = datetime.utcnow().year
        years = []
        for year in range(1950, current_year + 1):
            years.append((str(year), str(year)))
        return years

    @api.depends('name', 'first_last_name', 'second_last_name')
    def _compute_full_name(self):
        for record in self:
            name_parts = [record.name, record.first_last_name, record.second_last_name]
            record.full_name = ' '.join(filter(None, name_parts))

    @api.model
    def create(self, vals):
        # Generar número de solicitud
        if 'request_number' not in vals or not vals['request_number']:
            vals['request_number'] = self.env['ir.sequence'].next_by_code('professional.request.update') or 'UPD00000'

        # Obtener la solicitud original y el perfil
        original_request = self.env['professional_registers.professional_request'].browse(
            vals.get('original_request_id'))
        profile = self.env['professional_registers.profile'].browse(vals.get('profile_id'))

        # Función auxiliar para obtener el ID si es un record
        def safe_id(value):
            return value.id if hasattr(value, 'id') and value else False

            # 'request' o cualquier otro caso
            # Campos de la solicitud

        request_fields = [
            'name', 'first_last_name', 'second_last_name', 'nationality_id', 'full_name', 'identity', 'id_fuc',
            'sex',
            'address', 'country', 'country_states', 'city', 'phone', 'email', 'teaching_level', 'study_center',
            'degree_date', 'volume', 'folio', 'number', 'convalidation_degree_tittle', 'profession', 'specialties',
            'investigations', 'investigations_year', 'degree_sciences', 'degree_sciences_year', 'teaching_category',
            'teaching_category_date', 'unaicc_date', 'user', 'password', 'image', 'date', 'retired'
        ]

        # Copiar valores de la solicitud original si no se especifican en vals
        for field in request_fields:
            if field not in vals or not vals.get(field):
                if original_request and field in original_request:
                    value = original_request[field]
                    # Solo convertir a ID si es Many2one
                    if self._fields.get(field) and self._fields[field].type == 'many2one':
                        vals[field] = safe_id(value)
                    else:
                        vals[field] = value

        # === CREAR LA SOLICITUD ===
        request = super(ProfessionalRequestUpdate, self).create(vals)

        # === COPIAR RELACIONES (One2many/Many2many) ===
        # Priorizar el perfil si está disponible, sino usar la solicitud original
        source_record = profile if profile else original_request

        if source_record:
            # Copiar history_work
            for work in source_record.history_work:
                work.copy({
                    'update_request': request.id,
                    'profile': profile.id,
                    'profesional_request': original_request.id
                })

            # Copiar professional_language
            for lang in source_record.professional_language:
                lang.copy({
                    'update_request': request.id,
                    'profile': profile.id,
                    'profesional_request': original_request.id
                })

        if original_request and original_request.documents_required:
            for doc_line in original_request.documents_required:
                doc_line.copy({
                    'update_request': request.id,
                    'request': False,  # Limpiar relación con solicitud original
                })

        # === COPIAR CERTIFICADOS (si existe solicitud original) ===
        if original_request and original_request.certificate_attachment:
            request.certificate_attachment = [(6, 0, original_request.certificate_attachment.ids)]

        return request

    def _detect_changes(self):
        """Detecta qué campos han cambiado respecto a los datos originales"""
        self.ensure_one()
        changed_fields = []

        # Determinar la fuente original: perfil o solicitud
        profile_source = None
        request_source = None
        if self.profile_id:
            profile_source = self.env['professional_registers.profile'].search([
                ('identity', '=', self.profile_id.identity)
            ], limit=1)
            if not profile_source:
                return changed_fields
        if self.original_request_id:
            request_source = self.original_request_id

        # === 1. Comparar campos simples (char, integer, date, boolean, etc.) ===
        simple_fields = [
            'name', 'first_last_name', 'second_last_name', 'full_name', 'identity', 'id_fuc',
            'sex', 'address', 'phone', 'email', 'user', 'password', 'date', 'retired',

        ]
        for field in simple_fields:
            val1 = getattr(self, field, None)
            val2 = getattr(profile_source, field, None)
            # Normalizar valores: False, None, '' → todos se tratan como "vacío"
            val1_norm = val1 or False
            val2_norm = val2 or False
            if val1_norm != val2_norm:
                changed_fields.append(field)

        simple_fields = [
            'degree_date', 'volume', 'folio', 'number', 'convalidation_degree_tittle',
            'investigations', 'investigations_year', 'degree_sciences', 'degree_sciences_year',
            'teaching_category_date', 'unaicc_date'
        ]
        for field in simple_fields:
            val1 = getattr(self, field, None)
            val2 = getattr(request_source, field, None)
            # Normalizar valores: False, None, '' → todos se tratan como "vacío"
            val1_norm = val1 or False
            val2_norm = val2 or False
            if val1_norm != val2_norm:
                changed_fields.append(field)

        # === 2. Comparar campos Many2one (por ID) ===
        many2one_fields = [
            'nationality_id', 'country', 'country_states', 'city',

        ]
        for field in many2one_fields:
            id1 = getattr(self, field, self.env['res.users']).id or False
            id2 = getattr(profile_source, field, self.env['res.users']).id or False
            if id1 != id2:
                changed_fields.append(field)

        many2one_fields = [

            'teaching_level', 'study_center', 'profession', 'specialties', 'teaching_category'
        ]
        for field in many2one_fields:
            id1 = getattr(self, field, self.env['res.users']).id or False
            id2 = getattr(request_source, field, self.env['res.users']).id or False
            if id1 != id2:
                changed_fields.append(field)

        # === 3. Comparar relaciones One2many (por IDs y por contenido) ===
        # history_work
        if not self._records_equal_by_ids_and_fields(
                self.history_work, profile_source.history_work,
                ['institution', 'position', 'start_date', 'end_date']
        ):
            changed_fields.append('history_work')

        # professional_language
        if not self._records_equal_by_ids_and_fields(
                self.professional_language, profile_source.professional_language,
                ['language', 'proficiency_level', 'speaking', 'writing', 'reading']
        ):
            changed_fields.append('professional_language')

        return changed_fields

    def _records_equal_by_ids_and_fields(self, recs1, recs2, fields):
        """Compara dos recordsets por IDs y por valores de campos específicos."""
        if len(recs1) != len(recs2):
            return False
        # Convertir a listas ordenadas por ID para comparación consistente
        list1 = sorted(recs1, key=lambda r: r.id)
        list2 = sorted(recs2, key=lambda r: r.id)
        for r1, r2 in zip(list1, list2):
            for field in fields:
                v1 = getattr(r1, field, None) or False
                v2 = getattr(r2, field, None) or False
                # Para Many2one, comparar IDs
                if hasattr(v1, 'id'):
                    v1 = v1.id or False
                if hasattr(v2, 'id'):
                    v2 = v2.id or False
                if v1 != v2:
                    return False
        return True

    # Métodos para el flujo de estados
    def process(self):
        """Procesa la solicitud de actualización si hay cambios"""
        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 2), ('model', '=', int(model.id))]
        )

        # Detectar cambios
        changed_fields = self._detect_changes()

        # Si no hay cambios, mostrar mensaje y no procesar
        if not changed_fields:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Cambios',
                    'message': 'No se detectaron cambios en los datos. No es necesario procesar la solicitud.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        total_attachments = len(self.attachment_ids) + len(self.certificate_attachment)
        if total_attachments == 0:
            raise exceptions.ValidationError(
                "Debe adjuntar al menos un documento de respaldo en Documentación Requerida  para procesar la solicitud."
            )

        # Validar documentos requeridos por línea
        for doc_line in self.documents_required:
            if doc_line.documents.is_document_required and doc_line.checked:
                if not doc_line.attachment_ids:
                    raise exceptions.ValidationError(
                        f"El documento '{doc_line.documents.name}' es obligatorio y debe tener adjuntos."
                    )

        # Crear historial de cambio de estado
        self.env['professional_registers.request_update_history'].create({
            'update_id': self.id,
            'state_id': self.states.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {state_priority.name}"
        })

        # Actualizar estado de la solicitud
        self.write({
            'states': state_priority.id,
            'priority': 2,
            'date_request': current_date
        })

        # Generar notificaciones
        self.generate_notifications(2)

    def validation(self):
        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 3), ('model', '=', int(model.id))]
        )

        if not self.attachment_ids:
            raise exceptions.ValidationError(f"Debe adjuntar el documento de forma obligatoria!!!")

        # Crear historial
        self.env['professional_registers.request_update_history'].create({
            'update_id': self.id,
            'state_id': self.states.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {state_priority.name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 3,
            'user_on_charge': self.env.uid
        })

        self.generate_notifications(3)

        if not self.original_request_id.email and not self.profile_id.email:
            raise UserError("No se puede enviar notificación: la solicitud no tiene email asociado")

        # Renderizar cuerpo del correo
        body_html = f"""
           <div style="font-family: Arial, sans-serif; line-height: 1.5;">
               <h2 style="color: #2c3e50;">Notificación de Cambio de Estado</h2>
               <p>Estimado/a {self.full_name},</p>
               <p>Le informamos que su solicitud <strong>{self.request_number}</strong> ha cambiado a estado: <strong>{state_priority.name}</strong>.</p>

               <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
               <ul>
                   <li><strong>Número:</strong> {self.request_number}</li>           
                   <li><strong>Fecha:</strong> {self.date_request}</li>
                   <li><strong>Responsable:</strong> {self.env.user.partner_id.name}</li>
               </ul>

               <p style="margin-top: 20px;">
                   Puede consultar el estado de su solicitud en cualquier momento accediendo al sistema.
               </p>

               <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
                   Este es un mensaje automático, por favor no responda directamente a este correo.
               </p>
           </div>
           """

        # Sanitizar el HTML
        sanitized_html = html_sanitize(body_html)

        # Buscar o crear el partner asociado
        partner = self.env['res.partner'].search(
            [('email', '=', self.original_request_id.email or self.profile_id.email)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.full_name,
                'email': self.original_request_id.email or self.profile_id.email
            })

        # Preparar valores del correo
        mail_values = {
            'subject': f"Solicitud en Validación - {self.request_number}",
            'body_html': sanitized_html,
            'email_to': self.original_request_id.email or self.profile_id.email,
            'email_from': self.env.user.email or self.env.company.email,
            'partner_ids': [(4, partner.id)],
            'model': self._name,
            'res_id': self.id,
        }

        # Crear y enviar el correo
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        # Mostrar notificación al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Solicitud en Validación',
                'message': f'Se notificó al profesional ({self.original_request_id.email or self.profile_id.email}) que su solicitud está en validación',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def approved(self):
        """Aprueba la solicitud de actualización y sincroniza los datos comunes con el perfil y las solicitudes asociadas."""
        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')

        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 6), ('model', '=', int(model.id))],
            limit=1
        )

        # Validar documentos requeridos

        if not self.attachment_ids:
            raise exceptions.ValidationError(f"Debe adjuntar el documento de forma obligatoria!!!")

        # Detectar campos que han cambiado
        changed_fields = self._detect_changes()

        # Obtener perfil y solicitud original
        profile = self.profile_id
        original_request = self.original_request_id

        if not profile and not original_request:
            raise exceptions.ValidationError("No se encontró el perfil ni la solicitud original asociada.")

        # Determinar los campos comunes entre perfil y solicitud
        request_fields = set(self._fields.keys())
        profile_fields = set(self.env['professional_registers.profile']._fields.keys())
        common_fields = list(request_fields.intersection(profile_fields) - {
            'id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'display_name'
        })

        # Preparar valores actualizados
        vals_to_sync = {}
        for field in changed_fields:
            if field in common_fields:
                vals_to_sync[field] = getattr(self, field)

        #  Actualizar el perfil (si aplica)
        if profile and vals_to_sync:
            profile.write(vals_to_sync)

        #  Actualizar la solicitud original (si aplica)
        if original_request and vals_to_sync:
            original_request.write(vals_to_sync)

        #  Actualizar todas las solicitudes asociadas al mismo perfil (coherencia global)
        if profile and vals_to_sync:
            # === 1. Comparar campos simples (char, integer, date, boolean, etc.) ===
            simple_fields = [
                'name', 'first_last_name', 'second_last_name', 'full_name', 'identity', 'id_fuc',
                'sex', 'address', 'phone', 'email', 'user', 'password', 'date', 'retired',

            ]
            values = {}
            for item in vals_to_sync:
                if item in simple_fields:
                    values[item] = vals_to_sync[item]

            other_requests = self.env['professional_registers.professional_request'].search([
                ('profile_id', '=', profile.id),
                ('identity', '=', profile.identity),
                ('id', '!=', original_request.id if original_request else 0)
            ])
            for n in other_requests:
                n.write(values)

        #  Actualizar relaciones dependientes si hubo cambios
        if 'history_work' in changed_fields:
            if profile:
                profile.history_work.unlink()
                for work in self.history_work:
                    work.copy({
                        'profile': profile.id,
                        'update_request': False,
                        'profesional_request': False
                    })
            if original_request:
                original_request.history_work.unlink()
                for work in self.history_work:
                    work.copy({
                        'profesional_request': original_request.id,
                        'update_request': False,
                        'profile': False
                    })

        if 'professional_language' in changed_fields:
            if profile:
                profile.professional_language.unlink()
                for lang in self.professional_language:
                    lang.copy({
                        'profile': profile.id,
                        'update_request': False,
                        'profesional_request': False
                    })
            if original_request:
                original_request.professional_language.unlink()
                for lang in self.professional_language:
                    lang.copy({
                        'profesional_request': original_request.id,
                        'update_request': False,
                        'profile': False
                    })

        # Actualizar adjuntos de certificación (si existen)
        if self.certificate_attachment and original_request:
            original_request.certificate_attachment = [(6, 0, self.certificate_attachment.ids)]

        #  Sincronizar con inscripciones (si hay perfil asociado)
        if profile:
            profile.sync_profile_to_inscriptions(
                'update', 'professional_registers.professional_request_update', self.id
            )

        # === SINCRONIZAR DOCUMENTOS PERSONALES ===
        for doc_line in self.documents_required:
            if doc_line.documents.is_personal_document and doc_line.attachment_ids:
                # Este documento es personal (CI o Currículum)
                # Sincronizar con el perfil
                if profile:
                    # Buscar o crear la línea correspondiente en el perfil
                    profile_doc = profile.documents_required.filtered(
                        lambda d: d.documents.id == doc_line.documents.id
                    )
                    if profile_doc:
                        profile_doc.write({'attachment_ids': [(6, 0, doc_line.attachment_ids.ids)]})
                    else:
                        doc_line.copy({
                            'profile': profile.id,
                            'request': False,
                            'update_request': False,
                        })

                # Sincronizar con la solicitud original
                if original_request:
                    original_doc = original_request.documents_required.filtered(
                        lambda d: d.documents.id == doc_line.documents.id
                    )
                    if original_doc:
                        original_doc.write({'attachment_ids': [(6, 0, doc_line.attachment_ids.ids)]})

                # Sincronizar con OTRAS solicitudes del mismo perfil (mismo CI)
                if profile:
                    other_requests = self.env['professional_registers.professional_request'].search([
                        ('profile_id', '=', profile.id),
                        ('identity', '=', profile.identity),
                        ('id', '!=', original_request.id if original_request else 0)
                    ])
                    for req in other_requests:
                        req_doc = req.documents_required.filtered(
                            lambda d: d.documents.id == doc_line.documents.id
                        )
                        if req_doc:
                            req_doc.write({'attachment_ids': [(6, 0, doc_line.attachment_ids.ids)]})

        #  Crear historial de cambio de estado
        self.env['professional_registers.request_update_history'].create({
            'update_id': self.id,
            'state_id': self.states.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {state_priority.name}"
        })

        #  Actualizar estado de la solicitud
        self.write({
            'states': state_priority.id,
            'priority': 6,
        })

        #  Generar notificaciones
        self.generate_notifications(6)

        #  Mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Solicitud Aprobada',
                'message': 'La solicitud ha sido aprobada y los datos se sincronizaron correctamente en perfil y solicitudes asociadas.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    # def denied(self):
    #     current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
    #     model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
    #     state_priority = self.env['security.state_configuration'].search(
    #         [('priority', '=', 8), ('model', '=', int(model.id))]
    #     )
    #
    #     # Crear historial
    #     self.env['professional_registers.request_update_history'].create({
    #         'update_id': self.id,
    #         'state_id': self.states.id,
    #         'user_id': self.env.user.id,
    #         'date': current_date,
    #         'observation': f"Cambio de estado a {state_priority.name}"
    #     })
    #
    #     self.write({
    #         'states': state_priority.id,
    #         'priority': 8,
    #     })
    #
    #     self.generate_notifications(8)

    # En professional_request_update.py, modificar el método denied()
    def denied(self):
        """Abre wizard para denegar actualización"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Denegar Solicitud de Actualización",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_update_id": self.id,
                "default_action_type": "denial",
                "default_estado_destino": 8,  # Denegado
                "default_email_to": self.email or (self.original_request_id and self.original_request_id.email) or '',
            },
        }

    def send_email(self):
        self.ensure_one()
        ir_model_data = self.env["ir.model.data"]
        try:
            compose_form_id = ir_model_data.get_object_reference(
                "professional_registers", "email_form"
            )[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})

        template_id = self.env['mail.template'].search([('name', '=', 'Professional Register comment')])
        user = self.env['res.users'].search([('login', '=', str(self.original_request_id.user))])
        body = """
                Escriba aqui 
            """

        template_id.write({
            'body_html': body
        })
        ctx.update(
            {
                "default_model": "professional_registers.professional_request_update",
                "default_res_id": self.id,
                "default_composition_mode": "comment",  # "comment",# mass_mail
                "force_email": True,
                "default_body": body,
                # "default_subject": 'dad',
                'default_template_id': template_id.id,
                # "mark_rfq_as_sent": True,
                'mark_so_as_sent': True,
                "default_partner_ids": user.partner_id.ids,
            }
        )

        return {
            "name": "Envío de comentarios a profesional",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }

    def generate_notifications(self, state_priority):
        # Implementar notificaciones según el estado
        # ...
        pass

    # Métodos onchange para validaciones
    @api.onchange('country_states')
    def onchange_country_states(self):
        if self.country_states:
            cities = self.env['res.city'].search([('state_id', '=', int(self.country_states.id))])
            return dict(
                value=dict(city=None),
                domain=dict(city=[('id', 'in', cities.ids)])
            )

    @api.onchange('country')
    def onchange_country(self):
        if self.country:
            states = self.env['res.country.state'].search([('country_id', '=', int(self.country.id))])
            return dict(
                value=dict(country_states=None),
                domain=dict(country_states=[('id', 'in', states.ids)])
            )

    @api.onchange('profession')
    def onchange_profession(self):
        if self.profession:
            specialties = self.env['nomenclators.specialties'].search([('profession_id', '=', int(self.profession.id))])
            return dict(
                value=dict(specialties=None),
                domain=dict(specialties=[('id', 'in', specialties.ids)])
            )

    @api.onchange('retired')
    def _onchange_retired(self):
        if not self.retired:
            self.date = False

    @api.onchange('investigations')
    def _onchange_investigations(self):
        if not self.investigations:
            self.investigations_year = False

    @api.onchange('degree_sciences')
    def _onchange_degree_sciences(self):
        if not self.degree_sciences or self.degree_sciences == 'anything':
            self.degree_sciences_year = False

    def go_to_original_request(self):
        """Abre la solicitud original asociada a esta solicitud de actualización"""
        self.ensure_one()

        # Obtener la vista de formulario de la solicitud original
        ir_model_data = self.env['ir.model.data']
        try:
            form_id = ir_model_data.get_object_reference('professional_registers', 'professional_request_form_view')[1]
        except ValueError:
            form_id = False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'res_id': self.original_request_id.id,
            'view_mode': 'form',
            'views': [(form_id, 'form')] if form_id else False,
            'target': 'current',
            'context': {
                'active_id': self.original_request_id.id,
                'active_model': 'professional_registers.professional_request',
            }
        }

    # En professional_request_update.py

    def view_profile(self):
        """Abre el perfil asociado a esta solicitud de actualización"""
        self.ensure_one()

        if not self.profile_id:
            raise exceptions.ValidationError('No hay perfil asociado a esta solicitud.')

        # Obtener la vista de formulario del perfil
        ir_model_data = self.env['ir.model.data']
        try:
            form_id = ir_model_data.get_object_reference('professional_registers', 'profile_form_view')[1]
        except ValueError:
            form_id = False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.profile',
            'res_id': self.profile_id.id,
            'view_mode': 'form',
            'views': [(form_id, 'form')] if form_id else False,
            'target': 'current',

            'context': {
                'active_id': self.profile_id.id,
                'active_model': 'professional_registers.profile',
            }
        }
