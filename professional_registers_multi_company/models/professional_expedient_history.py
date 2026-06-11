# -*- coding: utf-8 -*-

from odoo import models, fields


class ExpedientHistoryCompany(models.Model):
    _inherit = 'professional_registers.expedient_history'

    company_id = fields.Many2one(
        related='expedient_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
