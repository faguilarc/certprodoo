from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExpedientCommunication(models.Model):
    _name = 'professional_registers.expedient_communication'
    _description = 'Comunicaciones del Expediente'
    _order = 'date desc'

    expedient_id = fields.Many2one(
        'professional_registers.expedient',
        string='Expediente',
        required=True,
        ondelete='cascade'
    )

    company_id = fields.Many2one('res.company', string="Compañía", related='expedient_id.company_id', store=True, readonly=True)

    # Campos básicos
    date = fields.Datetime('Fecha', default=fields.Datetime.now, required=True)
    subject = fields.Char('Asunto', required=True)
    body = fields.Html('Contenido', required=True)

    # Tipo de comunicación (ampliado)
    communication_type = fields.Selection([
        ('email_sent', 'Email Enviado'),
        ('email_received', 'Email Recibido'),
        ('notification', 'Notificación del Sistema'),
        ('sms', 'SMS'),
        ('phone_call', 'Llamada Telefónica'),
        ('meeting', 'Reunión'),
        ('other', 'Otro'),
    ], string='Tipo', default='email_sent')

    # Participantes
    partner_id = fields.Many2one('res.partner', string='Contacto')
    user_id = fields.Many2one('res.users', string='Usuario')

    # Referencia a mensajes originales
    mail_message_id = fields.Many2one(
        'mail.message',
        string='Mensaje Original',
        help="Mensaje original del sistema (mail.message)"
    )
    mail_mail_id = fields.Many2one(
        'mail.mail',
        string='Correo Electrónico',
        help="Correo electrónico original (mail.mail)"
    )

    # Estado de la comunicación (ampliado)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviado'),
        ('outgoing', 'Saliente'),
        ('delivered', 'Entregado'),
        ('received', 'Recibido'),
        ('read', 'Leído'),
        ('exception', 'Fallido'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='sent')

    # Dirección de la comunicación
    direction = fields.Selection([
        ('outgoing', 'Saliente'),
        ('incoming', 'Entrante'),
    ], string='Dirección', compute='_compute_direction', store=True)

    # Adjuntos
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'ir_attach_expedient_comm_rel',
        string='Adjuntos'
    )

    # Campos calculados
    has_original = fields.Boolean(
        'Tiene Original',
        compute='_compute_has_original',
        store=True
    )

    # Campos para relacionar con otros registros
    res_model = fields.Char('Modelo Relacionado')
    res_id = fields.Integer('ID Relacionado')

    @api.depends('mail_message_id', 'mail_mail_id')
    def _compute_has_original(self):
        for record in self:
            record.has_original = bool(record.mail_message_id or record.mail_mail_id)

    @api.depends('communication_type')
    def _compute_direction(self):
        for record in self:
            if record.communication_type in ['email_sent', 'notification', 'sms', 'phone_call', 'meeting']:
                record.direction = 'outgoing'
            elif record.communication_type in ['email_received']:
                record.direction = 'incoming'
            else:
                record.direction = False

    def action_view_original(self):
        """Abre el mensaje o correo original"""
        self.ensure_one()

        if self.mail_message_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mail.message',
                'res_id': self.mail_message_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.mail_mail_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mail.mail',
                'res_id': self.mail_mail_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            raise ValidationError("Esta comunicación no tiene un original asociado.")

    def action_view_related_record(self):
        """Abre el registro relacionado si existe"""
        self.ensure_one()

        if self.res_model and self.res_id:
            try:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': self.res_model,
                    'res_id': self.res_id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            except Exception:
                raise ValidationError("No se puede acceder al registro relacionado.")
        else:
            raise ValidationError("Esta comunicación no tiene un registro relacionado.")

    @api.model
    def create_from_mail_message(self, message, expedient_id):
        """
        Crea una comunicación a partir de un mail.message
        """
        # Determinar el tipo de comunicación
        if message.subtype_id and message.subtype_id.name == 'notifications':
            comm_type = 'notification'
        elif message.author_id and message.author_id.id == self.env.user.partner_id.id:
            comm_type = 'email_sent'
        else:
            comm_type = 'email_received'

        # Determinar el estado
        if hasattr(message, 'notification_ids') and message.notification_ids:
            notification = message.notification_ids[0]
            state = 'read' if notification.read else 'delivered'
        else:
            state = 'sent'

        # Obtener destinatarios
        recipients = []
        if message.partner_ids:
            recipients = [partner.email for partner in message.partner_ids if partner.email]

        return self.create({
            'expedient_id': expedient_id,
            'date': message.date,
            'subject': message.subject or 'Sin asunto',
            'body': message.body,
            'communication_type': comm_type,
            'partner_id': message.author_id.id if message.author_id else False,
            'user_id': self.env.user.id,
            'mail_message_id': message.id,
            'state': state,
            'attachment_ids': [(6, 0, message.attachment_ids.ids)],
            'res_model': message.model,
            'res_id': message.res_id,
        })

    @api.model
    def create_from_mail_mail(self, mail, expedient_id):
        """
        Crea una comunicación a partir de un mail.mail
        """
        # Determinar el tipo de comunicación
        professional_email = self.env['professional_registers.expedient'].browse(expedient_id).professional_id.email

        if mail.email_from and professional_email in mail.email_from:
            comm_type = 'email_sent'
        else:
            comm_type = 'email_received'

        # Obtener destinatarios
        recipients = []
        if mail.recipient_ids:
            recipients = [partner.email for partner in mail.recipient_ids if partner.email]
        elif mail.email_to:
            recipients = mail.email_to.split(',')

        return self.create({
            'expedient_id': expedient_id,
            'date': mail.date,
            'subject': mail.subject,
            'body': mail.body_html,
            'communication_type': comm_type,
            'partner_id': mail.author_id.id if mail.author_id else False,
            'user_id': self.env.user.id,
            'mail_mail_id': mail.id,
            'state': mail.state,
            'attachment_ids': [(6, 0, mail.attachment_ids.ids)],
        })

    def action_create_manual(self):
        """
        Crea una comunicación manual
        """
        return {
            'name': 'Crear Comunicación Manual',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.expedient_communication',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_expedient_id': self.expedient_id.id,
            }
        }