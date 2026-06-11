# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DashboardSecurityExpedient(models.Model):
    _name = "professional_register.dashboard_expedient"
    _description = "Estadísticas de Expedientes"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_expedients(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        expedients = self.env['professional_registers.expedient'].search(
            [('company_id', 'in', company_access.company_ids.ids)])
        quantity = len(expedients)
        return quantity

    @api.model
    def get_full_data(self, values=None):
        info = []

        total_expedients = self.get_count_expedients(values)

        info.append(
            {
                "expedients": total_expedients,
            }
        )
        return info


class DashboardSecurityUpdates(models.Model):
    _name = "professional_register.dashboard_updates"
    _description = "Estadísticas de Actualizaciones"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_updates(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        domain = []
        domain.append(('company_id', 'in', company_access.company_ids.ids))
        if self.env["res.users"].has_group("security.group_professional_register_employee"):
            domain.append(('user_id', '=', int(user.id)))
        updates = self.env['professional_registers.professional_request_update'].search(domain)
        quantity = len(updates)
        return quantity

    @api.model
    def get_full_data(self, values=None):
        info = []

        total_updates = self.get_count_updates(values)

        info.append(
            {
                "updates": total_updates,
            }
        )
        return info


class DashboardSecurityClaims(models.Model):
    _name = "professional_register.dashboard_claims"
    _description = "Estadísticas de Reclamaciones"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_claims(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        domain = []
        domain.append(('company_id', 'in', company_access.company_ids.ids))
        if self.env["res.users"].has_group("security.group_professional_register_employee"):
            domain.append(('user_id', '=', int(user.id)))
        claims = self.env['professional_registers.claim_request'].search(domain)
        quantity = len(claims)
        return quantity

    @api.model
    def get_full_data(self, values=None):
        info = []

        total_claims = self.get_count_claims(values)

        info.append(
            {
                "claims": total_claims,
            }
        )
        return info
