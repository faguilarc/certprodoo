# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProfessionalRequestCompany(models.Model):
    _inherit = 'professional_registers.professional_request'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )

    @api.model
    def create(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(ProfessionalRequestCompany, self).create(vals)

    def _action_populate_company_id(self):
        """Asignar compañía a registros existentes que no tengan company_id."""
        records = self.search([('company_id', '=', False)])
        if records:
            records.write({'company_id': self.env.company.id})
