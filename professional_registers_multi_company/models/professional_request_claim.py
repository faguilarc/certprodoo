# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProfessionalRequestClaimCompany(models.Model):
    _inherit = 'professional_registers.claim_request'

    # company_id se hereda de base_process_request, pero nos aseguramos
    # el default en create()
    @api.model
    def create(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(ProfessionalRequestClaimCompany, self).create(vals)
