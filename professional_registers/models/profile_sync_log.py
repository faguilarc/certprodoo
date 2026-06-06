from odoo import models, fields, api


class ProfileSyncLog(models.Model):
    _name = 'professional_registers.profile_sync_log'
    _description = 'Registro de Sincronización de Perfil'
    _order = 'date desc'

    profile_id = fields.Many2one('professional_registers.profile', string='Perfil', required=True,ondelete='cascade')
    date = fields.Datetime('Fecha', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True, default=lambda self: self.env.user)
    source_model = fields.Char('Modelo Origen', required=True)
    source_id = fields.Integer('ID Origen', required=True)
    inscriptions_updated = fields.Integer('Inscripciones Actualizadas', required=True)
    details = fields.Text('Detalles de la Sincronización')
    sync_type = fields.Selection([
        ('profile', 'Actualización de Perfil'),
        ('update', 'Actualización de Solicitud'),
        ('manual', 'Sincronización Manual'),
    ], string='Tipo de Sincronización', required=True, default='manual')

    @api.model
    def create(self, vals):
        record = super(ProfileSyncLog, self).create(vals)

        # Enviar notificación si se actualizaron inscripciones
        if record.inscriptions_updated > 0:
            record._send_notification()

        return record

    def _send_notification(self):
        """Envía una notificación sobre la sincronización realizada"""
        message = f"Se han sincronizado {self.inscriptions_updated} inscripciones con el perfil {self.profile_id.full_name}"

        # Notificar a los usuarios con permisos de administración
        admin_users = self.env['res.users'].search([
            ('groups_id', 'in', [
                self.env.ref('base.group_system').id,
                self.env.ref('security.group_professional_superadmin').id
            ])
        ])

        for user in admin_users:
            self.env['mail.message'].sudo().create({
                'message_type': "notification",
                'body': message,
                'subject': "Sincronización de Perfil Realizada",
                'model': self._name,
                'res_id': self.id,
                'partner_ids': [(4, user.partner_id.id)],
            })