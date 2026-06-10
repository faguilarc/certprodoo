from odoo import models, fields


class ProcessHistory(models.Model):
    _name = 'professional_registers.process_history'
    _description = 'Historial de Procesos'
    _order = 'date desc'

    process_id = fields.Many2one('professional_registers.claim_request', string='reclamacion', required=True)
    company_id = fields.Many2one('res.company', string="Compañía", related='process_id.company_id', store=True, readonly=True)
    state_id = fields.Many2one('security.state_configuration', string='Estado', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    date = fields.Datetime('Fecha', default=fields.Datetime.now)
    observation = fields.Text('Observación')