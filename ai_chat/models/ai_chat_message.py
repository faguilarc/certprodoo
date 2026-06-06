from odoo import models, fields

class AiChatMessage(models.Model):
    _name = 'ai.chat.message'
    _description = 'AI Chat Message'
    _order = 'create_date ASC'

    chat_id = fields.Many2one('ai.chat', 'Chat Session', required=True, ondelete='cascade')
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
    ], string='Role', required=True)
    content = fields.Text('Content', required=True)