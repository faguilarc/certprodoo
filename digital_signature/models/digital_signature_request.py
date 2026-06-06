# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import secrets
import hashlib


class DigitalSignatureRequest(models.Model):
    _name = 'digital.signature.request'
    _description = 'Solicitud de Firma Digital'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos de identificación
    name = fields.Char(
        string='Referencia',
        readonly=True,
        default=lambda self: _('New'),
        copy=False
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submitted', 'Enviada'),
        ('processing', 'En Proceso'),
        ('pending_verification', 'Pendiente de Verificación'),
        ('verified', 'Verificada'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
    ], string='Estado', default='draft', tracking=True)

    # Relaciones
    inscription_id = fields.Many2one(
        'professional_registers.inscription',
        string='Inscripción',
        required=True
    )

    config_id = fields.Many2one(
        'digital.signature.config',
        string='Configuración',
        required=True
    )

    # Datos de la solicitud
    level = fields.Selection([
        ('personal', 'Nivel Personal'),
        ('institution', 'Nivel Institución')
    ], string='Nivel', required=True)

    request_type = fields.Selection([
        ('affiliation', 'Filiación'),
        ('renewal', 'Renovación')
    ], string='Tipo de Solicitud', required=True)

    # Snapshot de datos
    snapshot_name = fields.Char('Nombre y Apellidos')
    snapshot_identity = fields.Char('CI / Pasaporte')
    snapshot_email = fields.Char('Correo Electrónico')
    snapshot_profession = fields.Char('Profesión')
    snapshot_specialty = fields.Char('Especialidad')
    snapshot_organism = fields.Char('Organismo')
    snapshot_entity = fields.Char('Empresa / Entidad')
    snapshot_job = fields.Char('Cargo')

    # Términos y condiciones
    terms_html = fields.Html('Términos Aceptados', readonly=True)
    terms_accepted = fields.Boolean('Términos Aceptados')
    terms_accepted_date = fields.Datetime('Fecha de Aceptación')

    # Verificación por correo
    verification_token = fields.Char(
        'Token de Verificación',
        readonly=True,
        copy=False
    )
    verification_date = fields.Datetime(
        'Fecha de Verificación',
        readonly=True,
        copy=False
    )
    verification_ip = fields.Char(
        'IP de Verificación',
        readonly=True,
        copy=False
    )
    verification_expiry = fields.Datetime(
        'Vencimiento de Verificación',
        readonly=True,
        compute='_compute_verification_expiry',
        store=True
    )

    # Fechas importantes
    request_date = fields.Datetime(
        'Fecha de Solicitud',
        default=fields.Datetime.now
    )
    validity_days = fields.Integer(
        'Días de Validez',
        related='config_id.validity_days'
    )
    expiry_date = fields.Date(
        'Fecha de Expiración',
        compute='_compute_expiry_date',
        store=True
    )

    # Campos para administración
    admin_notes = fields.Text('Notas del Administrador')
    certificate_number = fields.Char('Número de Certificado')
    certificate_file = fields.Binary('Archivo de Certificado')
    certificate_filename = fields.Char('Nombre del Archivo')

    @api.depends('request_date', 'validity_days')
    def _compute_expiry_date(self):
        for record in self:
            if record.request_date and record.validity_days:
                request_date = fields.Date.from_string(
                    fields.Date.context_today(self)
                )
                record.expiry_date = request_date + timedelta(
                    days=record.validity_days
                )
            else:
                record.expiry_date = False

    @api.depends('request_date')
    def _compute_verification_expiry(self):
        for record in self:
            if record.request_date:
                record.verification_expiry = record.request_date + timedelta(days=7)
            else:
                record.verification_expiry = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'digital.signature.request'
            ) or _('New')

        # Generar token de verificación único
        vals['verification_token'] = self._generate_verification_token()

        return super().create(vals)

    def _generate_verification_token(self):
        """Genera un token único de verificación"""
        random_bytes = secrets.token_bytes(32)
        timestamp = str(datetime.now().timestamp()).encode('utf-8')
        token = hashlib.sha256(random_bytes + timestamp).hexdigest()[:32]
        return token

    def get_verification_url(self):
        """Genera la URL de verificación"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/digital_signature/verify/{self.id}/{self.verification_token}"

    def action_submit(self):
        for record in self:
            if not record.terms_accepted:
                raise UserError(_("Debe aceptar los términos y condiciones."))

            # Verificar que la inscripción esté aprobada
            if record.inscription_id.priority != 1:
                raise UserError(_(
                    "La inscripción debe estar aprobada para solicitar firma digital. "
                    "Estado actual: %s" % record.inscription_id.states.name
                ))

            record.state = 'pending_verification'

            # Enviar correo de verificación al usuario
            record._send_verification_email()

            # También enviar notificación al admin
            record._send_submission_email()

    def action_verify_by_email(self, token, ip_address=None):
        """Verifica la solicitud cuando el usuario hace clic en el correo"""
        self.ensure_one()

        if self.state != 'pending_verification':
            return {
                'success': False,
                'message': _("Esta solicitud no está pendiente de verificación.")
            }

        # Verificar token
        if self.verification_token != token:
            return {
                'success': False,
                'message': _("Token de verificación inválido.")
            }

        # Verificar que no haya expirado
        if self.verification_expiry and fields.Datetime.now() > self.verification_expiry:
            return {
                'success': False,
                'message': _("El enlace de verificación ha expirado.")
            }

        # Verificar que el carnet de la solicitud coincida con el de la inscripción
        if self.snapshot_identity != self.inscription_id.identity:
            return {
                'success': False,
                'message': _(
                    "El carnet de identidad no coincide con la inscripción. "
                    "Solicitud: %s, Inscripción: %s" % (
                        self.snapshot_identity,
                        self.inscription_id.identity
                    )
                )
            }

        # Verificar que la inscripción esté aprobada
        if self.inscription_id.states.id != 9:
            return {
                'success': False,
                'message': _(
                    "La inscripción asociada no está aprobada. "
                    "Estado: %s" % self.inscription_id.states.name
                )
            }

        # Marcar como verificada
        self.write({
            'state': 'verified',
            'verification_date': fields.Datetime.now(),
            'verification_ip': ip_address,
        })

        # Enviar notificación al admin de que fue verificada
        self._send_verification_notification_email()

        return {
            'success': True,
            'message': _("Solicitud verificada correctamente."),
            'request_name': self.name,
            'verification_date': self.verification_date,
        }

    def action_resend_verification(self):
        """Reenvía el correo de verificación"""
        for record in self:
            if record.state != 'pending_verification':
                raise UserError(_("Solo se puede reenviar verificación a solicitudes pendientes."))

            # Actualizar token si ha expirado
            if record.verification_expiry and fields.Datetime.now() > record.verification_expiry:
                record.verification_token = self._generate_verification_token()

            record._send_verification_email()

            # Registrar en el chatter
            record.message_post(
                body=_("Correo de verificación reenviado a %s" % record.snapshot_email)
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Correo Reenviado',
                'message': 'El correo de verificación ha sido reenviado al usuario.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_process(self):
        self.write({'state': 'processing'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def _send_submission_email(self):
        """Envía email al administrador"""
        template = self.env.ref(
            'digital_signature.email_template_digital_signature_admin',
            raise_if_not_found=False
        )
        if template and self.config_id.notify_admin:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.config_id.admin_email,
                    'email_from': self.env.user.email or self.env.company.email,
                }
            )

    def _send_verification_email(self):
        """Envía email de verificación al usuario"""
        template = self.env.ref(
            'digital_signature.email_template_digital_signature_verification',
            raise_if_not_found=False
        )
        if template and self.config_id.notify_user:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.snapshot_email,
                    'email_from': self.config_id.admin_email or self.env.company.email,
                }
            )

    def _send_verification_notification_email(self):
        """Notifica al admin que el usuario verificó"""
        template = self.env.ref(
            'digital_signature.email_template_digital_signature_verified',
            raise_if_not_found=False
        )
        if template and self.config_id.notify_admin:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.config_id.admin_email,
                    'email_from': self.env.user.email or self.env.company.email,
                }
            )


    def get_selection_label(self, field_name):
        """Método genérico para obtener etiquetas de selección"""
        self.ensure_one()
        field = self._fields.get(field_name)
        if field and field.type == 'selection':
            # Busca el valor en la selección
            for key, label in field.selection:
                if key == getattr(self, field_name):
                    return label
        return ''