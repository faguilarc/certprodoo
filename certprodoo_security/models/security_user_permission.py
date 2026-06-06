# -*- coding: utf-8 -*-
"""
SecurityUserPermission — Permisos por Usuario.

Permite sobreescribir los permisos del rol a nivel de usuario.
Si un usuario tiene un permiso explícito aquí, toma precedencia
sobre el permiso de su rol.

En O14 era security.permits_option.
"""

from odoo import models, fields, api, _


class SecurityUserPermission(models.Model):
    """Permiso específico de usuario para una Opción.

    Permite otorgar o restringir permisos a un usuario
    de forma individual, independiente de su rol.

    La precedencia es:
    1. Permiso de usuario (este modelo) — máxima prioridad
    2. Permiso del rol del usuario
    3. Permiso por defecto (propias, sin escritura)
    """
    _name = "certprodoo.security.user.permission"
    _description = "Permiso por Usuario"
    _rec_name = "user_id"
    _inherit = ["certprodoo.audit.mixin"]
    _order = "user_id, option_id"

    option_id = fields.Many2one(
        "certprodoo.security.option",
        string="Opción",
        required=True,
        tracking=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        required=True,
        tracking=True,
        ondelete="cascade",
    )
    perm_show = fields.Selection(
        [("propias", "Solo las Propias"),
         ("todas", "Todas")],
        string="Visibilidad",
        default="propias",
        required=True,
        tracking=True,
    )
    field_write = fields.Boolean(
        string="Permiso de Escritura",
        default=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    _sql_constraints = [
        (
            "user_opt_uniq",
            "unique (user_id, option_id)",
            "La combinación de usuario y opción ya existe!",
        ),
    ]

    # ─── CRUD Overrides ───────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
        return super().create(vals_list)
