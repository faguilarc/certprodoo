# -*- coding: utf-8 -*-

from odoo import models, fields


class ProfessionalRequestHistoryCompany(models.Model):
    _inherit = 'professional_registers.professional_request_history'

    company_id = fields.Many2one(
        related='request_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
