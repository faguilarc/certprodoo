# -*- coding: utf-8 -*-
"""
SecurityRole — Roles de usuario del sistema.

Define perfiles de permisos que se asignan a usuarios.
Cada rol tiene un conjunto de permisos (role_permission_ids)
que determinan qué opciones puede ver y con qué nivel de acceso.

En O14 era security.roles. En O17:
- Hereda AuditMixin (reemplaza traces manuales)
- Usa ir.rule para filtrado por compañía (reemplaza search_read override)
- Los permisos se aplican via ir.rule computados dinámicamente
"""

from odoo import models, fields, api, _


class SecurityRole(models.Model):
    """Rol de seguridad del sistema.

    Define un perfil de permisos. Los usuarios con este rol
    heredan los permisos definidos en role_permission_ids.

    Los roles por defecto son: Administrador, Editor,
    Editor-Administrador, Cliente, Cliente Online.
    """
    _name = "certprodoo.security.role"
    _description = "Rol de Seguridad"
    _rec_name = "name"
    _inherit = ["certprodoo.audit.mixin"]
    _order = "name"

    name = fields.Char(
        string="Rol",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Descripción",
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario Asignado",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        tracking=True,
    )
    is_default = fields.Boolean(
        string="Rol por Defecto",
        default=False,
        help="Los roles por defecto no se pueden eliminar.",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    # ─── Relaciones ────────────────────────────────────────────

    role_permission_ids = fields.One2many(
        "certprodoo.security.role.permission",
        "role_id",
        string="Permisos del Rol",
    )
    user_count = fields.Integer(
        string="Usuarios con este Rol",
        compute="_compute_user_count",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique (name, company_id)",
            "El nombre del rol debe ser único por compañía!",
        ),
    ]

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("name")
    def _compute_user_count(self):
        for role in self:
            role.user_count = self.env["res.users"].search_count([
                ("certprodoo_role_id", "=", role.id),
            ])

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
                    _("No se puede eliminar el rol por defecto '%s'.") % record.name
                )
        return super().unlink()

    # ─── Métodos de Acción ─────────────────────────────────────

    def action_view_users(self):
        """Abre la vista de usuarios con este rol."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Usuarios con rol %s") % self.name,
            "res_model": "res.users",
            "view_mode": "tree,form",
            "domain": [("certprodoo_role_id", "=", self.id)],
        }
