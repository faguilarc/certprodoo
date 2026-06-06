from odoo import models, fields, api, exceptions, _
from datetime import datetime
import base64
from odoo.tools import html_sanitize
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import re


class SolicitudObservacionWizard(models.TransientModel):
    _name = "solicitud.observacion.wizard"
    _description = "Wizard para Observaciones de Cambio de Estado"

    PHONE_MIN_LENGTH = 8
    PHONE_MAX_LENGTH = 15
    INTERNATIONAL_MIN_LENGTH = 7
    INTERNATIONAL_MAX_LENGTH = 15

    # Campos para los tres tipos de solicitudes
    solicitud_id = fields.Many2one(
        "professional_registers.professional_request",
        string="Solicitud de Inscripción"
    )

    update_id = fields.Many2one(
        "professional_registers.professional_request_update",
        string="Solicitud de Actualización"
    )

    claim_id = fields.Many2one(
        "professional_registers.claim_request",
        string="Solicitud de Reclamación"
    )

    # Campos para determinar el tipo de registro activo
    active_record = fields.Reference(
        string='Registro Activo',
        selection='_get_active_record_types',
        compute='_compute_active_record',
        store=False
    )

    active_model = fields.Char(
        string='Modelo Activo',
        compute='_compute_active_record',
        store=False
    )


    estado_destino = fields.Char("Estado Destino")

    email_to = fields.Char(string='Destinatario', required=True)
    action_type = fields.Selection([
        ('detention', 'Detención'),
        ('denial', 'Denegación'),
        ('cancellation', 'Cancelación')
    ], string='Tipo de Acción', required=True)

    cause_ids = fields.Many2many(
        'nomenclators.detention_causes',
        string='Causas',
        domain="[('cause_type', '=', action_type)]"
    )

    observaciones = fields.Text("Observaciones")
    counter = fields.Integer("Días hábiles", default=0)

    preview_email = fields.Html('Vista Previa Email', compute='_compute_preview')
    preview_document = fields.Html('Vista Previa Documento', compute='_compute_preview')

    # Añade este campo al modelo
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'solicitud_observacion_wizard_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Documentos Adjuntos'
    )

    phone_from = fields.Char('Teléfono')
    email_from = fields.Char('Correo')

    @api.model
    def _get_active_record_types(self):
        """Devuelve los tipos de registros que puede manejar el wizard"""
        return [
            ('professional_registers.professional_request', 'Solicitud de Inscripción'),
            ('professional_registers.professional_request_update', 'Solicitud de Actualización'),
            ('professional_registers.claim_request', 'Solicitud de Reclamación')
        ]

    @api.depends('solicitud_id', 'update_id', 'claim_id')
    def _compute_active_record(self):
        """Determina el registro activo y su modelo"""
        for record in self:
            if record.solicitud_id:
                record.active_record = f"professional_registers.professional_request,{record.solicitud_id.id}"
                record.active_model = 'professional_registers.professional_request'
            elif record.update_id:
                record.active_record = f"professional_registers.professional_request_update,{record.update_id.id}"
                record.active_model = 'professional_registers.professional_request_update'
            elif record.claim_id:
                record.active_record = f"professional_registers.claim_request,{record.claim_id.id}"
                record.active_model = 'professional_registers.claim_request'
            else:
                record.active_record = False
                record.active_model = False

    # Añadimos la constraint de Python para validación más compleja
    @api.constrains('counter')
    def _check_counter(self):
        for record in self:
            if record.action_type == 'detention' and record.counter == 0:
                raise ValidationError("El valor del campo días hábiles no puede ser cero!")

    @api.constrains('email_to', 'email_from')
    def _validate_email(self):
        for record in self:
            if record.email_from:
                # 1. Validación básica de formato
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', record.email_from):
                    raise ValidationError(
                        _('Formato de correo electrónico inválido. Ejemplo válido: usuario@dominio.com'))

                # # 2. Validación de dominios no permitidos
                # invalid_domains = ['gmail.com', 'yahoo.com', 'hotmail.com']  # Lista personalizable
                # domain = record.email.split('@')[-1].lower()
                # if domain in invalid_domains:
                #     raise ValidationError(
                #         _('No se permiten correos de dominios gratuitos. Use su correo institucional.'))

                # # 3. Validación de unicidad (opcional)
                # if self.search_count([('email_from', '=', record.email), ('id', '!=', record.id)]):
                #     raise ValidationError(_('Este correo electrónico ya está registrado por otro profesional'))

    @api.constrains('phone_from')
    def _check_phone(self):
        for record in self:
            if record.phone_from:
                phone = record.phone_from.strip()

                # Verificar que no esté vacío
                if not phone:
                    raise ValidationError("El teléfono no puede estar vacío.")

                # Patrón que permite + al inicio y caracteres comunes de formato
                phone_pattern = r'^\+?[0-9\s\-\(\)]+$'

                if not re.match(phone_pattern, phone):
                    raise ValidationError(
                        "Formato de teléfono inválido. Use solo números, + al inicio (opcional), "
                        "y caracteres de separación como espacios, guiones o paréntesis."
                    )

                # Limpiar el número (eliminar +, espacios, guiones, paréntesis)
                clean_phone = re.sub(r'[^\+0-9]', '', phone)
                digits_only = clean_phone.replace('+', '')

                # Validar longitud
                if clean_phone.startswith('+'):
                    # Número internacional
                    if len(digits_only) < self.INTERNATIONAL_MIN_LENGTH or len(
                            digits_only) > self.INTERNATIONAL_MAX_LENGTH:
                        raise ValidationError(
                            f"Número internacional inválido. Debe tener entre "
                            f"{self.INTERNATIONAL_MIN_LENGTH} y {self.INTERNATIONAL_MAX_LENGTH} dígitos "
                            f"después del código de país."
                        )
                else:
                    # Número local
                    if len(digits_only) < self.PHONE_MIN_LENGTH or len(digits_only) > self.PHONE_MAX_LENGTH:
                        raise ValidationError(
                            f"Número local inválido. Debe tener entre {self.PHONE_MIN_LENGTH} "
                            f"y {self.PHONE_MAX_LENGTH} dígitos.")

    @api.depends('cause_ids', 'observaciones', 'action_type', 'solicitud_id', 'update_id', 'claim_id')
    def _compute_preview(self):
        for record in self:
            try:
                solicitud_data = record._get_solicitud_data()
                record.preview_email = record._generate_email_body(solicitud_data)
            except Exception as e:
                record.preview_email = f"<p>Error generando vista previa: {str(e)}</p>"
            try:
                record.preview_document = record._generate_preview_document(solicitud_data)
            except Exception as e:
                record.preview_document = f"<p>Error generando vista previa del documento: {str(e)}</p>"

    def _get_professional_request_data(self):
        """Obtiene datos de ProfessionalRequest"""
        solicitud = self.solicitud_id

        # Obtener el nombre del nuevo estado
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_new = self.env['security.state_configuration'].search([
            ('priority', '=', int(self.estado_destino)),
            ('model', '=', model.id)
        ], limit=1)

        return {
            'tipo': 'inscripción',
            'solicitud_no': solicitud.request_number or '',
            'solicitante': solicitud.full_name or '',
            'identificacion': solicitud.identity or '',
            'email': solicitud.email or '',
            'telefono': solicitud.phone or '',
            'estado_actual': solicitud.states.name if solicitud.states else '',
            'estado_nuevo': state_new.name if state_new else 'Nuevo Estado',
            'fecha_cambio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usuario_cambio': self.env.user.name,
            'observaciones': self.observaciones or '',
            'fecha_solicitud': solicitud.create_date.strftime('%Y-%m-%d') if solicitud.create_date else '',
            'tipo_solicitud': solicitud.procedure_type.name if solicitud.procedure_type else '',
            'dias_habiles': self.counter or '',
            'action_type': self.action_type,
            'causas': self.cause_ids,
            'phone_from': self.phone_from,
            'email_from': self.email_from,
            'registro': solicitud
        }

    def _get_update_request_data(self):
        """Obtiene datos de ProfessionalRequestUpdate"""
        update = self.update_id

        # Obtener el nombre del nuevo estado
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_new = self.env['security.state_configuration'].search([
            ('priority', '=', int(self.estado_destino)),
            ('model', '=', model.id)
        ], limit=1)

        return {
            'tipo': 'actualización',
            'solicitud_no': update.request_number or '',
            'solicitante': update.full_name or '',
            'identificacion': update.identity or '',
            'email': update.email or update.original_request_id.email or '',
            'telefono': update.phone or '',
            'estado_actual': update.states.name if update.states else '',
            'estado_nuevo': state_new.name if state_new else 'Nuevo Estado',
            'fecha_cambio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usuario_cambio': self.env.user.name,
            'observaciones': self.observaciones or '',
            'fecha_solicitud': update.date_request.strftime('%Y-%m-%d') if update.date_request else '',
            'tipo_solicitud': 'Actualización',
            'dias_habiles': self.counter or '',
            'action_type': self.action_type,
            'causas': self.cause_ids,
            'phone_from': self.phone_from,
            'email_from': self.email_from,
            'registro': update
        }

    def _get_claim_request_data(self):
        """Obtiene datos de ClaimRequest"""
        claim = self.claim_id

        # Obtener la etiqueta del estado nuevo
        state_labels = {
            'rejected': 'Sin lugar',
            'cancelled': 'Con lugar en parte'
        }
        estado_nuevo = state_labels.get(self.estado_destino, self.estado_destino)

        return {
            'tipo': 'reclamación',
            'solicitud_no': claim.request_number or '',
            'solicitante': claim.full_name or '',
            'identificacion': claim.identity or '',
            'email': claim.original_request_id.email if claim.original_request_id else '',
            'telefono': '',
            'estado_actual': claim.claim_status or '',
            'estado_nuevo': estado_nuevo,
            'fecha_cambio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usuario_cambio': self.env.user.name,
            'observaciones': self.observaciones or '',
            'fecha_solicitud': claim.date_request.strftime('%Y-%m-%d') if claim.date_request else '',
            'tipo_solicitud': f'Reclamación - {dict(claim._fields["claim_type"].selection).get(claim.claim_type, "")}',
            'dias_habiles': self.counter or '',
            'action_type': self.action_type,
            'causas': self.cause_ids,
            'phone_from': self.phone_from,
            'email_from': self.email_from,
            'registro': claim
        }

    def _get_solicitud_data(self):
        """Obtiene los datos de la solicitud según el tipo"""
        self.ensure_one()

        if self.solicitud_id:
            return self._get_professional_request_data()
        elif self.update_id:
            return self._get_update_request_data()
        elif self.claim_id:
            return self._get_claim_request_data()
        else:
            raise UserError("No se encontró ningún registro asociado.")

    def _generate_email_body(self, solicitud_data):
        """Genera el cuerpo del email usando la plantilla QWeb"""
        self.ensure_one()
        template = self.env.ref('professional_registers.email_template_state_change')
        body_html = self.env['ir.qweb']._render(
            template.id,
            {'solicitud_data': solicitud_data, 'env': self.env}
        )
        return self.env['mail.render.mixin']._replace_local_links(body_html)

    def _generate_preview_document(self, data):
        """Genera la vista previa del documento de notificación"""
        try:
            template = self.env.ref('professional_registers.report_notification_document')

            return self.env['ir.qweb']._render(template.id, {'data': data, 'user': self.env.user})
        except Exception as e:
            return f'<p>Error: {str(e)}</p>'

    def _actualizar_estado_solicitud(self):
        """Actualiza el estado de la solicitud según el tipo"""
        if self.solicitud_id:
            self._actualizar_professional_request()
        elif self.update_id:
            self._actualizar_update_request()
        elif self.claim_id:
            self._actualizar_claim_request()
        else:
            raise UserError("No se encontró ningún registro para actualizar.")

    def _actualizar_professional_request(self):
        """Actualiza el estado de ProfessionalRequest"""
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search([
            ('priority', '=', int(self.estado_destino)),
            ('model', '=', int(model.id))
        ], limit=1)

        if not state_priority:
            raise exceptions.ValidationError("¡Estado destino no configurado!")

        # Crear registro histórico
        self.env['professional_registers.professional_request_history'].create({
            'request_id': self.solicitud_id.id,
            'state_id': self.solicitud_id.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'observation': f"Cambio de estado a {state_priority.name}",
            'counter': self.counter if self.action_type == 'detention' else 0
        })

        # Actualizar solicitud
        self.solicitud_id.write({
            'states': state_priority.id,
            'priority': int(self.estado_destino),
            'user_on_charge': self.env.uid
        })

        # Actualizar estado en módulo de ayuda si existe
        register = self.env['professional_registers.request_help'].search([
            ('request_id', '=', int(self.solicitud_id.id))
        ])

        state_str = self.env['professional_registers.professional_request'].get_string_state(
            int(self.estado_destino), 'professional_registers.professional_request'
        )

        if register:
            register.write({
                'state': state_str,
                'counter': self.counter
            })

        # Generar notificaciones
        self.env['professional_registers.professional_request'].generate_notifications(int(self.estado_destino))

    def _actualizar_update_request(self):
        """Actualiza el estado de ProfessionalRequestUpdate"""
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search([
            ('priority', '=', int(self.estado_destino)),
            ('model', '=', int(model.id))
        ], limit=1)

        if not state_priority:
            raise exceptions.ValidationError("¡Estado destino no configurado!")

        # Crear registro histórico
        self.env['professional_registers.request_update_history'].create({
            'update_id': self.update_id.id,
            'state_id': self.update_id.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'observation': f"Cambio de estado a {state_priority.name}"
        })

        # Actualizar solicitud de actualización
        self.update_id.write({
            'states': state_priority.id,
            'priority': int(self.estado_destino),
        })

    def _actualizar_claim_request(self):
        """Actualiza el estado de ClaimRequest"""
        # Actualizar estado de la reclamación
        self.claim_id.write({
            'claim_status': self.estado_destino,
            'resolution_date': fields.Date.today(),
            'resolution_user': self.env.user.id,
            'resolution_text': self.observaciones or "Reclamación procesada."
        })

        # Si es denegación (rejected) o cancelación (cancelled), también actualizar el estado general
        if self.estado_destino in ['rejected', 'cancelled']:
            if self.estado_destino == 'rejected':
                priority = 8  # Denegado
            else:
                priority = 7  # Cancelado

            model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
            state_priority = self.env['security.state_configuration'].search([
                ('priority', '=', priority),
                ('model', '=', int(model.id))
            ], limit=1)

            if state_priority:
                self.claim_id.write({
                    'states': state_priority.id,
                    'priority': priority
                })

    def _enviar_correo(self):
        """Envía un correo con los datos de la solicitud y el cambio de estado"""
        self.ensure_one()

        # Obtener datos de la solicitud
        solicitud_data = self._get_solicitud_data()

        if self.action_type == 'denial' and not self.attachment_ids:
            raise UserError("Debe adjuntar algun documento si la acción es denegar!!")

        # Determinar el email destino
        if self.solicitud_id:
            email_destino = self.solicitud_id.email
        elif self.update_id:
            email_destino = self.update_id.email or (
                        self.update_id.original_request_id and self.update_id.original_request_id.email)
        elif self.claim_id:
            email_destino = self.claim_id.original_request_id.email if self.claim_id.original_request_id else ''
        else:
            raise UserError("No se puede determinar el destinatario del correo.")

        if not email_destino:
            raise UserError("La solicitud no tiene un email asociado.")

        # Renderizar el cuerpo del correo
        body_html = self._generate_email_body(solicitud_data)

        # Sanitizar el HTML
        sanitized_html = html_sanitize(body_html)

        # Buscar o crear el partner
        partner = self.env['res.partner'].search(
            [('email', '=', email_destino)],
            limit=1
        )
        if not partner:
            partner = self.env['res.partner'].create({
                'name': solicitud_data['solicitante'],
                'email': email_destino
            })

        # Determinar asunto según tipo de acción
        subject_map = {
            'detention': f"Detención de solicitud - {solicitud_data['solicitud_no']}",
            'denial': f"Denegación de solicitud - {solicitud_data['solicitud_no']}",
            'cancellation': f"Cancelación de solicitud - {solicitud_data['solicitud_no']}"
        }
        subject = subject_map.get(self.action_type,
                                  f"Actualización de estado - {solicitud_data['solicitud_no']}")

        # Preparar valores del correo
        mail_values = {
            'subject': subject,
            'body_html': sanitized_html,
            'email_to': email_destino,
            'email_from': self.env.user.email or self.env.company.email,
            'partner_ids': [(4, partner.id)],
        }

        # Añadir documentos adjuntos adicionales
        if self.attachment_ids:
            mail_values['attachment_ids'] = [(4, att.id) for att in self.attachment_ids]

        # Crear y enviar correo
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def action_send_and_generate(self):
        """Acción principal: actualiza estado, envía correo y genera documento"""
        self.ensure_one()

        # 1. Actualizar el estado de la solicitud
        self._actualizar_estado_solicitud()

        # Guardar PDF en expediente
        expedient = self._get_expedient()
        if expedient and expedient.dms_directory_id:
            # Generar PDF (usando el método existente)
            attachment = self._generar_pdf_adjunto()  # Devuelve un ir.attachment
            if attachment:
                # Buscar o crear carpeta "Notificaciones"
                notif_dir = expedient._get_or_create_subdir('Notificaciones')
                # Crear archivo DMS
                self.env['dms.file'].create({
                    'name': attachment.name,
                    'content': attachment.datas,
                    'mimetype': 'application/pdf',
                    'directory_id': notif_dir.id,
                    'attachment_id': attachment.id,
                    'res_model': self._name,
                    'res_id': self.id,
                })

        # 2. Enviar el correo con la información
        self._enviar_correo()

        # 3. Mostrar notificación de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notificación enviada',
                'message': 'El cambio de estado se ha procesado correctamente y se ha enviado la notificación.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _generar_pdf_adjunto(self):
        """Genera un PDF adjunto para acciones específicas"""
        report = self.env.ref('professional_registers.action_report_notification')
        pdf_content, _ = report._render_qweb_pdf([self.id])

        attachment = self.env['ir.attachment'].create({
            'name': f'Notificación_{self.action_type}_{self.id}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })

        return attachment


    #METODOS A MIGRAR PARA EL MODUO DE EXPEDIENTE

    def _get_expedient(self):
        self.ensure_one()
        if self.solicitud_id:
            return self.solicitud_id.expedient_id
        elif self.update_id:
            return self.update_id.expedient_id
        elif self.claim_id:
            return self.claim_id.expedient_id
        return False

