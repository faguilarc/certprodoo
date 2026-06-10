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

        inscriptions = self.env['professional_registers.inscription'].search(
            [('company_id', 'in', company_access.company_ids.ids)])
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