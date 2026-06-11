# -*- coding: utf-8 -*-

from odoo import models, fields


class StopProcessWizardCompany(models.Model):
    _inherit = 'stop.process.wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )
