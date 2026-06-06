# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class DashboardSecurity(models.Model):
    _name = "security.dashboard"
    _description = "Estadísticas de Seguridad"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_users(self, values=None):
        user = self.env.user
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )
        users = (
            self.env["res.users"]
            .sudo()
            .search_count(
                [
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                    ("company_id", "in", company_access.company_ids.ids),
                ]
            )
        )
        return users

    @api.model
    def get_count_users_active(self, values=None):
        user = self.env.user
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        users = (
            self.env["res.users"]
            .sudo()
            .search_count(
                [
                    ("active", "=", True),
                    ("company_id", "in", company_access.company_ids.ids),
                ]
            )
        )
        return users

    @api.model
    def get_count_company(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )
        cantidad = len(company_access.company_ids)
        return cantidad

    @api.model
    def get_count_roles(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        rol = self.env["security.roles"].search([("name", "=", "Administrador")])
        roles = self.env["security.roles"].search(
            [
                "|",
                ("company", "in", company_access.company_ids.ids),
                ("id", "=", rol.id),
            ]
        )
        cantidad = len(roles)
        return cantidad

    @api.model
    def get_full_data(self, values=None):
        info = []

        # total_usuarios = self.get_count_users(values)
        total_usuarios_active = self.get_count_users_active(values)
        total_company = self.get_count_company(values)
        total_roles = self.get_count_roles(values)

        info.append(
            {
                # "users": total_usuarios,
                "user_active": total_usuarios_active,
                "companies": total_company,
                "roles": total_roles,
            }
        )
        return info
