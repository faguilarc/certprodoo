# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BaseProcessRequestCompany(models.Model):
    _inherit = 'professional_registers.base_process_request'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )
