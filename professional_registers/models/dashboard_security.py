# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class DashboardSecurity(models.Model):
    _name = "professional_register.dashboard"
    _description = "Estadísticas de Registros Profesionales"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_professional_request(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        domain = []
        # Solo filtrar por company_id si el campo existe (requiere módulo professional_registers_multi_company)
        if 'company_id' in self.env['professional_registers.professional_request']._fields:
            domain.append(('company_id', 'in', company_access.company_ids.ids))
        if self.env["res.users"].has_group("security.group_professional_register_employee"):
            domain.append(('user_id', '=', int(user.id)))
        professional_request = self.env['professional_registers.professional_request'].search(domain)
        quantity = len(professional_request)
        return quantity


    @api.model
    def get_full_data(self, values=None):
        info = []

        total_professional_request = self.get_count_professional_request(values)
        # total_inscriptions = self.get_count_inscriptions(values)

        info.append(
            {
                "professional_request": total_professional_request,
                # "inscriptions": total_inscriptions,
            }
        )
        return info


class DashboardSecurityInscriptions(models.Model):
    _name = "professional_register.dashboard_inscriptions"
    _description = "Estadísticas de Inscription es"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_inscriptions(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        domain = []
        # Solo filtrar por company_id si el campo existe (requiere módulo professional_registers_multi_company)
        if 'company_id' in self.env['professional_registers.inscription']._fields:
            domain.append(('company_id', 'in', company_access.company_ids.ids))
        inscriptions = self.env['professional_registers.inscription'].search(domain)
        quantity = len(inscriptions)
        return quantity

    @api.model
    def get_full_data(self, values=None):
        info = []

        total_inscriptions = self.get_count_inscriptions(values)

        info.append(
            {
                "inscriptions": total_inscriptions,
            }
        )
        return info
