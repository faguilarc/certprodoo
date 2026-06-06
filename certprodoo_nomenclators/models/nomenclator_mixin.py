# -*- coding: utf-8 -*-
"""
BaseNomencatorMixin — Mixin base para todos los nomencladores.

Proporciona campos y lógica común:
- code: Código identificativo del registro
- active: Para archivar/desarchivar
- company_id: Multi-compañía
- user_id: Usuario responsable

Reemplaza la repetición de campos idénticos en cada modelo O14
y el patrón manual de user_id/company_id en create().

En O14 cada modelo repetía: user_id, company_id, y el override de
create() para auto-asignarlos. Ahora se hereda automáticamente.
"""

from odoo import models, fields, api, _


class BaseNomencatorMixin(models.AbstractModel):
    """Mixin base para todos los nomencladores del sistema.

    Hereda de certprodoo.audit.mixin para trazabilidad automática
    (reemplaza security.traces de O14).

    Campos comunes:
    - code: Código opcional del registro
    - active: Archivar/desarchivar
    - company_id: Multi-compañía con default
    - user_id: Usuario responsable con default

    Los modelos que hereden este mixin deben definir:
    - name: fields.Char() (requerido en cada modelo)
    """
    _name = "certprodoo.nomenclator.mixin"
    _description = "Mixin Base Nomenclador"
    _inherit = ["certprodoo.audit.mixin", "mail.thread", "mail.activity.mixin"]

    code = fields.Char(
        string="Código",
        tracking=True,
        help="Código identificativo del registro.",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario Responsable",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ─── CRUD Overrides ───────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-asigna company_id y user_id si no se proporcionan."""
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
            if not vals.get("user_id"):
                vals["user_id"] = self.env.uid
        return super().create(vals_list)
