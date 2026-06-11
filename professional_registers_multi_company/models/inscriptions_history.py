# -*- coding: utf-8 -*-

from odoo import models, fields


class InscriptionHistoryCompany(models.Model):
    _inherit = 'professional_registers.inscription_history'

    company_id = fields.Many2one(
        related='inscription_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
