# -*- coding: utf-8 -*-

from odoo import models, fields


class RequestUpdateHistoryCompany(models.Model):
    _inherit = 'professional_registers.request_update_history'

    company_id = fields.Many2one(
        related='update_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
