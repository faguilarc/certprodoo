# ai_chat/models/ai_chat.py

from odoo import models, fields, api

class AiChat(models.Model):
    _name = 'ai.chat'
    _description = 'AI Chat Session'
    _order = 'create_date DESC'

    name = fields.Char('Session Title', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    message_ids = fields.One2many('ai.chat.message', 'chat_id', string='Messages')
    provider_id = fields.Many2one('ai.provider', 'AI Provider', required=True, default=lambda self: self.env['ai.provider'].get_default_provider())

    @api.depends('create_date')
    def _compute_name(self):
        for chat in self:
            chat.name = f"Chat Session {chat.create_date.strftime('%Y-%m-%d %H:%M')}"

