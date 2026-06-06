# -*- coding: utf-8 -*-
"""
SecurityOption — Opciones securizables del sistema.

Mapea un nombre de pantalla/funcionalidad a un modelo (ir.model).
Cada "opción" representa una funcionalidad del sistema que puede
tener permisos controlados por el motor de permisos.

En O14 era security.options.
"""

from odoo import models, fields, api, _


class SecurityOption(models.Model):
    """Opción securizable del sistema.

    Cada opción es una referencia nombrada a un modelo de Odoo
    que puede ser controlada por el sistema de permisos.

    Por ejemplo:
    - "Solicitudes Profesionales" → professional_registers.inscription
    - "Firma Digital" → digital.signature.request
    - "Reclamaciones" → claims.claim

    Los permisos se definen sobre estas opciones, no directamente
    sobre los modelos, lo que permite una capa de abstracción.
    """
    _name = "certprodoo.security.option"
    _description = "Opción de Seguridad"
    _rec_name = "name"
    _inherit = ["certprodoo.audit.mixin"]
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
        help="Nombre descriptivo de la opción (ej. 'Solicitudes Profesionales').",
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        tracking=True,
        ondelete='cascade',
        help="Modelo de Odoo al que hace referencia esta opción.",
    )
    model_name = fields.Char(
        string="Nombre Técnico",
        compute="_compute_model_name",
        store=True,
        help="Nombre técnico del modelo (ej. professional_registers.inscription).",
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

    # ─── Relaciones ────────────────────────────────────────────

    role_permission_ids = fields.One2many(
        "certprodoo.security.role.permission",
        "option_id",
        string="Permisos por Rol",
    )
    user_permission_ids = fields.One2many(
        "certprodoo.security.user.permission",
        "option_id",
        string="Permisos por Usuario",
    )

    _sql_constraints = [
        (
            "model_name_uniq",
            "unique (name, model_id)",
            "Ya existe una opción con ese nombre para el modelo seleccionado!",
        ),
    ]

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("model_id")
    def _compute_model_name(self):
        for option in self:
            option.model_name = option.model_id.model if option.model_id else ""

    # ─── CRUD Overrides ───────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
            if not vals.get("user_id"):
                vals["user_id"] = self.env.uid
        return super().create(vals_list)
