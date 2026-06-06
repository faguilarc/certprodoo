# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProcedureSuspensionHistory(models.Model):
    _name = 'procedure.suspension.history'
    _description = 'Histórico de Suspensiones de Trámites'
    _order = 'stop_date desc'

    procedure_type_id = fields.Many2one(
        'nomenclators.procedure_types',
        string='Trámite',
        required=True,
        ondelete='cascade'
    )
    stop_date = fields.Datetime('Fecha de Detención', required=True)
    resume_date = fields.Datetime('Fecha de Reanudación')
    stop_reasons = fields.Many2many(
        'nomenclators.detention_causes',
        string='Causas de Detención',
        required=True,

    )

    stopped_by = fields.Many2one(
        'res.users',
        string='Detenido por',
        default=lambda self: self.env.uid,
        readonly=True
    )
    resumed_by = fields.Many2one(
        'res.users',
        string='Reanudado por',
        readonly=True
    )
    state = fields.Selection(
        [('stopped', 'Detenido'), ('resumed', 'Activo')],
        string='Estado',
        compute='_compute_state',
        store=True
    )

    @api.depends('resume_date')
    def _compute_state(self):
        for record in self:
            record.state = 'resumed' if record.resume_date else 'stopped'

