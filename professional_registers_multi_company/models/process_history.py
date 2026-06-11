# -*- coding: utf-8 -*-

from odoo import models, fields


class ProcessHistoryCompany(models.Model):
    _inherit = 'professional_registers.process_history'

    company_id = fields.Many2one(
        related='process_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
