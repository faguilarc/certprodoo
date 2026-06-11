# -*- coding: utf-8 -*-

from odoo import models, fields


class ExpedientCommunicationCompany(models.Model):
    _inherit = 'professional_registers.expedient_communication'

    company_id = fields.Many2one(
        related='expedient_id.company_id',
        string='Compañía',
        store=True,
        readonly=True,
    )
