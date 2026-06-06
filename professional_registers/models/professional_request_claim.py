from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import html_sanitize


class ClaimRequest(models.Model):
    _name = 'professional_registers.claim_request'
    _description = 'Solicitud de Reclamación'
    _inherit = ['professional_registers.base_process_request', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'request_number'

    # Campos específicos para reclamaciones
    original_request_id = fields.Many2one(
        'professional_registers.professional_request',
        string='Solicitud original',
        required=True,
        readonly=True
    )

    profile_id = fields.Many2one(
        'professional_registers.profile',
        string='Perfil asociado',
        readonly=True
    )

    claim_type = fields.Selection([
        ('denied', 'Reclamación por Denegación'),
        ('cancelled', 'Reclamación por Cancelación'),
    ], string='Tipo de Reclamación', required=True)

    claim_reason = fields.Text('Motivos de la reclamación', required=True)

    # Estado de la reclamación
    claim_status = fields.Selection([
        ('draft', 'Borrador'),
        ('in_process', 'En Proceso'),
        ('evaluating', 'En Validación'),
        ('approved', 'Con lugar'),
        ('cancelled', 'Con lugar en parte'),
        ('rejected', 'Sin lugar'),
    ], string='Estado de Reclamación', default='draft')

    # Documentación específica
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        'claim_evidence_attachments_rel',
        'claim_id',
        'attachment_id',
        string="Evidencias adjuntas"
    )

    # Respuesta a la reclamación
    response_date = fields.Date('Fecha de respuesta')
    response_user = fields.Many2one('res.users', string="Respondido por")
    response_text = fields.Text('Respuesta a la reclamación')
    show_answer = fields.Boolean('ver respuesta',  compute='_compute_show_answer', default=False)

    # Resolución final
    resolution_date = fields.Date('Fecha de resolución')
    resolution_user = fields.Many2one('res.users', string="Resuelto por")
    resolution_text = fields.Text('Resolución final')

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente')

    # Campos auxiliares
    # Campos específicos para reclamaciones
    original_request_id = fields.Many2one(
        'professional_registers.professional_request',
        string='Solicitud original',
        required=True,
        readonly=True
    )

    # NUEVOS CAMPOS PARA EL ENCABEZADO
    image = fields.Image(
        string="Foto",
        compute='_compute_image',
        store=True,  # Opcional: si quieres que se almacene en BD
        max_width=1920,
        max_height=1920
    )

    @api.depends('original_request_id.image', 'profile_id.image')
    def _compute_image(self):
        for record in self:
            image = False
            if record.original_request_id and record.original_request_id.image:
                image = record.original_request_id.image
            elif record.profile_id and record.profile_id.image:
                image = record.profile_id.image
            # Si no hay imagen, se queda en False (vacío)
            record.image = image

    full_name = fields.Char(
        string="Nombre completo",
        compute="_compute_full_name",
        store=True
    )

    identity = fields.Char(
        string="Identificación",
        compute="_compute_identity",
        store=True
    )

    id_fuc = fields.Char(
        string="ID FUC",
        compute="_compute_id_fuc",
        store=True
    )

    def get_procedure_default(self):
        procedure = self.env['nomenclators.procedure_types'].search([('comodel_name', '=', 'claim')])
        return procedure.id

    procedure_type = fields.Many2one('nomenclators.procedure_types', string="Tipo de trámite*",
                                     default=get_procedure_default)

    # MÉTODOS COMPUTE PARA LOS NUEVOS CAMPOS
    @api.depends('original_request_id')
    def _compute_full_name(self):
        for record in self:
            if record.original_request_id:
                # Ajusta según los campos reales en professional_request
                record.full_name = record.original_request_id.full_name or \
                                   f"{record.original_request_id.first_name or ''} {record.original_request_id.last_name or ''}".strip()
            else:
                record.full_name = False

    @api.depends('original_request_id')
    def _compute_identity(self):
        for record in self:
            if record.original_request_id:
                # Ajusta según el campo de identificación en professional_request
                record.identity = record.original_request_id.identity

            else:
                record.identity = False


    def _compute_show_answer(self):
        for record in self:
            if self.env.user.has_group('security.group_professional_superadmin'):
                # Ajusta según el campo de identificación en professional_request
                record.show_answer = True

            elif self.env.user.has_group('security.group_professional_client_online'):
                record.show_answer = False if not record.response_date or not record.response_user or not record.response_text else True

    @api.depends('original_request_id')
    def _compute_id_fuc(self):
        for record in self:
            if record.original_request_id:
                # Ajusta según el campo ID FUC en professional_request
                record.id_fuc = record.original_request_id.id_fuc
            else:
                record.id_fuc = False

    # Métodos específicos
    def _get_sequence_code(self):
        return 'professional.claim.request'

    def _get_states_domain(self):
        # Estados para el proceso de reclamación
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([
            ('model', '=', int(model.id)),
            ('id', 'in', [1, 2, 3, 6, 8])  # IDs de estados para reclamaciones
        ], order="priority asc")
        return [('id', 'in', states.ids)]

    def _get_default_state(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([
            ('model', '=', int(model.id))
        ], order="priority asc")
        return states[0].id if states else False

    def submit_claim(self):
        """Enviar la reclamación para procesamiento"""
        self.ensure_one()

        # Validar que se hayan adjuntado evidencias
        if not self.evidence_attachment_ids:
            raise ValidationError("Debe adjuntar al menos un documento como evidencia")

        # Cambiar estado a "En Proceso"
        state_in_process = self.env['security.state_configuration'].search([
            ('model.model', '=', 'professional_registers.professional_request'),
            ('priority', '=', 2)
        ])

        self.write({

            'states': state_in_process.id,
            'priority': 2,
            'claim_status': 'in_process'
        })

        # Añadir al historial
        self.add_history(self.id, state_in_process.id, "Reclamación enviada para procesamiento")

        # Generar notificaciones
        self.generate_notifications(2)

        return True

    def evaluate_claim(self):
        """Iniciar evaluación de la reclamación"""
        self.ensure_one()

        # Cambiar estado a "En Evaluación"
        state_evaluating = self.env['security.state_configuration'].search([
            ('model.model', '=', 'professional_registers.professional_request'),
            ('priority', '=', 3)
        ])

        self.write({
            'states': state_evaluating.id,
            'claim_status': 'evaluating',
            'priority': 3,
            'user_on_charge': self.env.user.id
        })

        # Añadir al historial
        self.add_history(self.id, state_evaluating.id, "Reclamación en evaluación")

        if not self.original_request_id.email:
            raise UserError("No se puede enviar notificación: la solicitud no tiene email asociado")

        # Obtener la etiqueta legible del campo selection
        claim_type_label = dict(self._fields['claim_type'].selection).get(self.claim_type)

        # Renderizar cuerpo del correo
        body_html = f"""
           <div style="font-family: Arial, sans-serif; line-height: 1.5;">
               <h2 style="color: #2c3e50;">Notificación de Cambio de Estado</h2>
               <p>Estimado/a {self.full_name},</p>
               <p>Le informamos que su solicitud <strong>{self.request_number}</strong> ha cambiado a estado: <strong>{state_evaluating.name}</strong>.</p>

               <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
               <ul>
                   <li><strong>Número:</strong> {self.request_number}</li>
                   <li><strong>Tipo:</strong> {claim_type_label}</li>
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
        partner = self.env['res.partner'].search([('email', '=', self.original_request_id.email)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.full_name,
                'email': self.original_request_id.email
            })

        # Preparar valores del correo
        mail_values = {
            'subject': f"Solicitud en Validación - {self.request_number}",
            'body_html': sanitized_html,
            'email_to': self.original_request_id.email,
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
                'message': f'Se notificó al profesional ({self.original_request_id.email}) que su solicitud está en validación',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def approve_claim(self):
        """Aprobar la reclamación y revertir el estado de la solicitud original"""
        self.ensure_one()
        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        # Cambiar estado a "Aprobada"
        state_approved = self.env['security.state_configuration'].search([
            ('model.model', '=', 'professional_registers.professional_request'),
            ('priority', '=', 6)
        ])

        # Revertir el estado de la solicitud original
        original_request = self.original_request_id
        if self.claim_type == 'denied':
            # Si fue denegada, volver a estado de validación
            state_validation = self.env['security.state_configuration'].search([
                ('model.model', '=', 'professional_registers.professional_request'),
                ('priority', '=', 3)
            ])

            self.env['professional_registers.professional_request_history'].create({
                'request_id': original_request.id,
                'state_id': original_request.states.id,
                'user_id': self.env.user.id,
                'date': current_date,
                'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_validation.id).name}"
            })

            original_request.write({
                'states': state_validation.id,
                'priority': 3
            })


        elif self.claim_type == 'cancelled':
            # Si fue cancelada, volver a estado en proceso
            state_process = self.env['security.state_configuration'].search([
                ('model.model', '=', 'professional_registers.professional_request'),
                ('priority', '=', 2)
            ])

            self.env['professional_registers.professional_request_history'].create({
                'request_id': original_request.id,
                'state_id': original_request.states.id,
                'user_id': self.env.user.id,
                'date': current_date,
                'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_process.id).name}"
            })

            original_request.write({
                'states': state_process.id,
                'priority': 2
            })

        self.write({
            'priority': 6,
            'states': state_approved.id,
            'claim_status': 'approved',
            'resolution_date': fields.Date.today(),
            'resolution_user': self.env.user.id,
            'resolution_text': "Reclamación aprobada. Solicitud original revertida."
        })

        # Añadir al historial
        self.add_history(self.id, state_approved.id, "Reclamación aprobada")

        # Actualizar estado de la reclamación

        # Generar notificaciones
        self.generate_notifications(4)

        return True

    # def reject_claim(self):
    #     """Rechazar la reclamación"""
    #     self.ensure_one()
    #
    #     # Cambiar estado a "Rechazada"
    #     state_rejected = self.env['security.state_configuration'].search([
    #         ('model.model', '=', 'professional_registers.professional_request'),
    #         ('priority', '=', 8)
    #     ])
    #
    #     self.write({
    #         'priority': 8,
    #         'states': state_rejected.id,
    #         'claim_status': 'rejected',
    #         'resolution_date': fields.Date.today(),
    #         'resolution_user': self.env.user.id,
    #         'resolution_text': "Reclamación rechazada."
    #     })
    #
    #     # Añadir al historial
    #     self.add_history(self.id, state_rejected.id, "Reclamación rechazada")
    #
    #     if not self.original_request_id.email:
    #         raise UserError("No se puede enviar notificación: la solicitud no tiene email asociado")
    #     else:
    #         # Obtener datos para el correo
    #
    #         # Obtener la etiqueta legible del campo selection
    #         claim_type_label = dict(self._fields['claim_type'].selection).get(self.claim_type)
    #
    #         # Renderizar cuerpo del correo
    #         body_html = f"""
    #            <div style="font-family: Arial, sans-serif; line-height: 1.5;">
    #                <h2 style="color: #2c3e50;">Notificación de Cambio de Estado</h2>
    #                <p>Estimado/a {self.full_name},</p>
    #                <p>Le informamos que su solicitud <strong>{self.request_number}</strong> ha cambiado a estado: <strong>{state_rejected.name}</strong>.</p>
    #
    #                <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
    #                <ul>
    #                    <li><strong>Número:</strong> {self.request_number}</li>
    #                    <li><strong>Tipo de reclamación:</strong> {claim_type_label}</li>
    #                    <li><strong>Fecha:</strong> {self.resolution_date}</li>
    #                    <li><strong>Responsable:</strong> {self.env.user.partner_id.name}</li>
    #                </ul>
    #
    #                <p style="margin-top: 20px;">
    #                    Puede consultar el estado de su solicitud en cualquier momento accediendo al sistema.
    #                </p>
    #
    #                <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
    #                    Este es un mensaje automático, por favor no responda directamente a este correo.
    #                </p>
    #            </div>
    #            """
    #
    #         # Sanitizar el HTML
    #         sanitized_html = html_sanitize(body_html)
    #
    #         # Buscar o crear el partner asociado
    #         partner = self.env['res.partner'].search([('email', '=', self.original_request_id.email)], limit=1)
    #         if not partner:
    #             partner = self.env['res.partner'].create({
    #                 'name': self.full_name,
    #                 'email': self.email
    #             })
    #
    #         # Preparar valores del correo
    #         mail_values = {
    #             'subject': f"Solicitud en Validación - {self.request_number}",
    #             'body_html': sanitized_html,
    #             'email_to': self.original_request_id.email,
    #             'email_from': self.env.user.email or self.env.company.email,
    #             'partner_ids': [(4, partner.id)],
    #             'model': self._name,
    #             'res_id': self.id,
    #         }
    #
    #         # Crear y enviar el correo
    #         mail = self.env['mail.mail'].create(mail_values)
    #         mail.send()
    #
    #         # Mostrar notificación al usuario
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Solicitud Denegada',
    #                 'message': f'Se notificó al profesional ({self.original_request_id.email}) que su solicitud está denegada',
    #                 'sticky': False,
    #                 'next': {'type': 'ir.actions.act_window_close'},
    #             }
    #         }
    #
    #     # Generar notificaciones
    #     self.generate_notifications(5)
    #
    #     return True
    #
    # def cancel_claim(self):
    #     """Rechazar la reclamación"""
    #     self.ensure_one()
    #
    #     # Cambiar estado a "Rechazada"
    #     state_rejected = self.env['security.state_configuration'].search([
    #         ('model.model', '=', 'professional_registers.professional_request'),
    #         ('priority', '=', 8)
    #     ])
    #
    #     self.write({
    #         'priority': 8,
    #         'states': state_rejected.id,
    #         'claim_status': 'rejected',
    #         'resolution_date': fields.Date.today(),
    #         'resolution_user': self.env.user.id,
    #         'resolution_text': "Reclamación rechazada."
    #     })
    #
    #     # Añadir al historial
    #     self.add_history(self.id, state_rejected.id, "Reclamación rechazada")
    #
    #     if not self.original_request_id.email:
    #         raise UserError("No se puede enviar notificación: la solicitud no tiene email asociado")
    #     else:
    #         # Obtener datos para el correo
    #
    #         # Obtener la etiqueta legible del campo selection
    #         claim_type_label = dict(self._fields['claim_type'].selection).get(self.claim_type)
    #
    #         # Renderizar cuerpo del correo
    #         body_html = f"""
    #            <div style="font-family: Arial, sans-serif; line-height: 1.5;">
    #                <h2 style="color: #2c3e50;">Notificación de Cambio de Estado</h2>
    #                <p>Estimado/a {self.full_name},</p>
    #                <p>Le informamos que su solicitud <strong>{self.request_number}</strong> ha cambiado a estado: <strong>{state_rejected.name}</strong>.</p>
    #
    #                <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
    #                <ul>
    #                    <li><strong>Número:</strong> {self.request_number}</li>
    #                    <li><strong>Tipo de reclamación:</strong> {claim_type_label}</li>
    #                    <li><strong>Fecha:</strong> {self.resolution_date}</li>
    #                    <li><strong>Responsable:</strong> {self.env.user.partner_id.name}</li>
    #                </ul>
    #
    #                <p style="margin-top: 20px;">
    #                    Puede consultar el estado de su solicitud en cualquier momento accediendo al sistema.
    #                </p>
    #
    #                <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
    #                    Este es un mensaje automático, por favor no responda directamente a este correo.
    #                </p>
    #            </div>
    #            """
    #
    #         # Sanitizar el HTML
    #         sanitized_html = html_sanitize(body_html)
    #
    #         # Buscar o crear el partner asociado
    #         partner = self.env['res.partner'].search([('email', '=', self.original_request_id.email)], limit=1)
    #         if not partner:
    #             partner = self.env['res.partner'].create({
    #                 'name': self.full_name,
    #                 'email': self.email
    #             })
    #
    #         # Preparar valores del correo
    #         mail_values = {
    #             'subject': f"Solicitud en Validación - {self.request_number}",
    #             'body_html': sanitized_html,
    #             'email_to': self.original_request_id.email,
    #             'email_from': self.env.user.email or self.env.company.email,
    #             'partner_ids': [(4, partner.id)],
    #             'model': self._name,
    #             'res_id': self.id,
    #         }
    #
    #         # Crear y enviar el correo
    #         mail = self.env['mail.mail'].create(mail_values)
    #         mail.send()
    #
    #         # Mostrar notificación al usuario
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Solicitud Denegada',
    #                 'message': f'Se notificó al profesional ({self.original_request_id.email}) que su solicitud está denegada',
    #                 'sticky': False,
    #                 'next': {'type': 'ir.actions.act_window_close'},
    #             }
    #         }
    #
    #     # Generar notificaciones
    #     self.generate_notifications(5)
    #
    #     return True

    def reject_claim(self):
        """Abre wizard para denegar reclamación"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Rechazar Reclamación",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_claim_id": self.id,
                "default_action_type": "denial",
                "default_estado_destino": "rejected",
                "default_email_to": self.original_request_id.email if self.original_request_id else '',
            },
        }

    def cancel_claim(self):
        """Abre wizard para cancelar reclamación"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Cancelar Reclamación",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_claim_id": self.id,
                "default_action_type": "cancellation",
                "default_estado_destino": "cancelled",
                "default_email_to": self.original_request_id.email if self.original_request_id else '',
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
            """

        template_id.write({
            'body_html': body
        })
        ctx.update(
            {
                "default_model": "professional_registers.claim_request",
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
        """Generar notificaciones según el estado"""
        # Implementación específica para notificaciones
        # ...
        pass

    def go_to_claim(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.claim_request',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

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

    @api.model
    def create(self, vals):

        # Generar número de solicitud
        if 'request_number' not in vals or not vals['request_number']:
            vals['request_number'] = self.env['ir.sequence'].next_by_code('professional.claim.request') or 'REC00000'

        vals['history_ids'] = []
        # === CREAR LA SOLICITUD ===
        request = super(ClaimRequest, self).create(vals)

        return request
