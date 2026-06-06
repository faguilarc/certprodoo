from odoo import models, fields


class ExpedientHistory(models.Model):
    _name = 'professional_registers.expedient_history'
    _description = 'Historial del Expediente'
    _order = 'date desc'

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente', required=True,
                                   ondelete='cascade')
    date = fields.Datetime('Fecha', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    title = fields.Char('Título', required=True)
    description = fields.Text('Descripción')

    # Referencia al registro que provocó el cambio
    reference_model = fields.Char('Modelo de Referencia')
    reference_id = fields.Integer('ID de Referencia')