# professional_request_update_history.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProfessionalRequestUpdateHistory(models.Model):
    _name = 'professional_registers.request_update_history'
    _description = 'Historial de Cambios de Estado de Solicitud de Actualización'
    _order = 'date desc'

    update_id = fields.Many2one(
        'professional_registers.professional_request_update',
        string='Solicitud de Actualización',
        required=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one('res.company', string="Compañía", related='update_id.company_id', store=True, readonly=True)
    state_id = fields.Many2one('security.state_configuration', string='Estado Anterior', required=True)
    state_id_new = fields.Many2one('security.state_configuration', string='Estado Actual', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    date = fields.Date('Fecha', required=True)
    observation = fields.Text('Observación')