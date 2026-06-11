# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PrDocumentCompany(models.Model):
    _inherit = 'professional_registers.pr_document'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )

    @api.model
    def create(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(PrDocumentCompany, self).create(vals)

    @api.model
    def _action_populate_company_id(self):
        """Asignar compañía a registros existentes que no tengan company_id."""
        records = self.search([('company_id', '=', False)])
        if records:
            records.write({'company_id': self.env.company.id})
