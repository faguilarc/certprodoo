# -*- coding: utf-8 -*-
"""
SecurityDashboard — Estadísticas de seguridad.

Provee endpoints RPC para el dashboard OWL del módulo de seguridad.
En O14 usaba AbstractAction (JS viejo). En O17 se reescribe como
OWL component con estos endpoints como fuente de datos.
"""

from odoo import models, fields, api


class SecurityDashboard(models.Model):
    """Estadísticas del módulo de seguridad.

    Modelo transitorio que provee datos al dashboard
    a través de métodos RPC llamados desde el frontend.
    """
    _name = "certprodoo.security.dashboard"
    _description = "Dashboard de Seguridad"
    _transient = True

    name = fields.Char(string="Nombre", default="Dashboard")

    # ─── Métodos RPC para el Dashboard ────────────────────────

    @api.model
    def get_count_users(self):
        """Retorna el total de usuarios (activos + inactivos)."""
        return self.env["res.users"].search_count([
            ("company_ids", "in", self.env.user.company_ids.ids),
        ])

    @api.model
    def get_count_users_active(self):
        """Retorna el total de usuarios activos."""
        return self.env["res.users"].search_count([
            ("active", "=", True),
            ("company_ids", "in", self.env.user.company_ids.ids),
        ])

    @api.model
    def get_count_users_by_type(self):
        """Retorna conteo de usuarios por tipo.

        Usa el campo user_type añadido por certprodoo_security.
        Si el campo no existe (módulo no instalado correctamente),
        retorna conteos vacíos.
        """
        result = {}
        try:
            for utype in ["client", "client_online", "system"]:
                result[utype] = self.env["res.users"].search_count([
                    ("user_type", "=", utype),
                    ("active", "=", True),
                    ("company_ids", "in", self.env.user.company_ids.ids),
                ])
        except Exception:
            result = {"client": 0, "client_online": 0, "system": 0}
        return result

    @api.model
    def get_count_companies(self):
        """Retorna el número de compañías accesibles."""
        return len(self.env.user.company_ids)

    @api.model
    def get_count_roles(self):
        """Retorna el número de roles de la compañía."""
        return self.env["certprodoo.security.role"].search_count([
            ("company_id", "in", self.env.user.company_ids.ids),
        ])

    @api.model
    def get_count_options(self):
        """Retorna el número de opciones securizables."""
        return self.env["certprodoo.security.option"].search_count([
            ("company_id", "in", self.env.user.company_ids.ids),
        ])

    @api.model
    def get_count_permissions(self):
        """Retorna el número de permisos configurados."""
        role_perms = self.env["certprodoo.security.role.permission"].search_count([
            ("company_id", "in", self.env.user.company_ids.ids),
        ])
        user_perms = self.env["certprodoo.security.user.permission"].search_count([
            ("company_id", "in", self.env.user.company_ids.ids),
        ])
        return {"role_permissions": role_perms, "user_permissions": user_perms}

    @api.model
    def get_full_data(self):
        """Retorna todos los datos del dashboard en una sola llamada."""
        return {
            "total_users": self.get_count_users(),
            "active_users": self.get_count_users_active(),
            "users_by_type": self.get_count_users_by_type(),
            "companies": self.get_count_companies(),
            "roles": self.get_count_roles(),
            "options": self.get_count_options(),
            "permissions": self.get_count_permissions(),
        }
