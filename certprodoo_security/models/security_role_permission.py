# -*- coding: utf-8 -*-
"""
SecurityRolePermission — Permisos por Rol.

Define qué puede hacer un rol con una opción específica:
- perm_show: Si puede ver solo sus registros ("propias") o todos ("todas")
- field_write: Si tiene permiso de escritura

En O14 era security.permits_roles.
"""

from odoo import models, fields, api, _


class SecurityRolePermission(models.Model):
    """Permiso asignado a un Rol para una Opción.

    Cada registro define los permisos que tiene un rol
    sobre una opción (modelo) específica:

    - perm_show="propias": Solo ve registros creados por él
    - perm_show="todas": Ve todos los registros de su compañía
    - field_write=True: Puede editar los registros
    - field_write=False: Solo lectura
    """
    _name = "certprodoo.security.role.permission"
    _description = "Permiso por Rol"
    _rec_name = "role_id"
    _inherit = ["certprodoo.audit.mixin"]
    _order = "role_id, option_id"

    role_id = fields.Many2one(
        "certprodoo.security.role",
        string="Rol",
        required=True,
        tracking=True,
        ondelete="cascade",
    )
    option_id = fields.Many2one(
        "certprodoo.security.option",
        string="Opción",
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
        help="Determina qué registros puede ver el rol:\n"
             "- Solo las Propias: Solo registros creados por el usuario\n"
             "- Todas: Todos los registros de la compañía",
    )
    field_write = fields.Boolean(
        string="Permiso de Escritura",
        default=False,
        tracking=True,
        help="Si True, el rol puede editar registros de esta opción.",
    )
    is_default = fields.Boolean(
        string="Permiso por Defecto",
        default=False,
        help="Los permisos por defecto no se pueden eliminar.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    _sql_constraints = [
        (
            "rol_opt_uniq",
            "unique (role_id, option_id)",
            "El rol y la opción no se pueden repetir!",
        ),
    ]

    # ─── CRUD Overrides ───────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
            if not vals.get("user_id"):
                vals["user_id"] = self.env.uid
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.is_default:
                raise ValueError(
                    _("No se puede eliminar un permiso por defecto.")
                )
        return super().unlink()
