from odoo import fields, models


class EmailAddress(models.Model):
    _inherit = "mail.compose.message"
    _name = "send.email"

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "email_ir_attachments_rel",
        "wizard_id",
        "attachment_id",
        "Attachments",
    )

    partner_ids = fields.Many2many(
        "res.partner",
        "email_res_partner_rel",
        "wizard_id",
        "partner_id",
        "Additional Contacts",
    )

    # # New fields
    # subject = fields.Char('Subject')
    # body = fields.Html('Body')
    # email_from = fields.Char('From')
    # email_to = fields.Char('To')
    # model_id = fields.Many2one('ir.model', string='Related Model')
    # res_id = fields.Integer('Related Document ID')
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('sent', 'Sent'),
    #     ('error', 'Error')
    # ], default='draft')
    #
    # @api.model
    # def create_notification_email(self, template_xmlid, record, partner_ids=None):
    #     """Create email notification from template for specific record"""
    #     template = self.env.ref(template_xmlid, raise_if_not_found=False)
    #     if not template:
    #         return False
    #
    #     values = {
    #         'model_id': record._name,
    #         'res_id': record.id,
    #         'partner_ids': [(6, 0, partner_ids)] if partner_ids else False,
    #         'subject': template.subject,
    #         'body': template.body_html,
    #         'email_from': template.email_from,
    #         'state': 'draft'
    #     }
    #     return self.create(values)
    #
    # def send_email(self):
    #     """Send email using mail.template capabilities"""
    #     self.ensure_one()
    #     try:
    #         mail_values = {
    #             'subject': self.subject,
    #             'body_html': self.body,
    #             'email_from': self.email_from,
    #             'email_to': self.email_to,
    #             'attachment_ids': [(6, 0, self.attachment_ids.ids)],
    #             'partner_ids': [(6, 0, self.partner_ids.ids)],
    #             'model': self.model_id.model,
    #             'res_id': self.res_id,
    #         }
    #
    #         mail = self.env['mail.mail'].create(mail_values)
    #         mail.send()
    #         self.write({'state': 'sent'})
    #         return True
    #     except Exception as e:
    #         self.write({'state': 'error'})
    #         _logger.error("Error sending email: %s", str(e))
    #         return False
    #
    # @api.model
    # def send_automatic_notification(self, record, template_xmlid, partner_ids=None):
    #     """Generic method to send automatic notifications for any model"""
    #     email = self.create_notification_email(template_xmlid, record, partner_ids)
    #     if email:
    #         return email.send_email()
    #     return False
