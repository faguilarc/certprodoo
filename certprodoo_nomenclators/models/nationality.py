# -*- coding: utf-8 -*-
"""
Nationality — Nomenclador de Nacionalidades.

En O14 era nomenclators.nationality.
Mejoras O17:
- Hereda BaseNomencatorMixin (code, active, company_id, user_id)
- AuditMixin reemplaza security.traces
- Fix bug O14: unlink() buscaba campo 'profession' en vez de 'nationality'
"""

from odoo import models, fields, api, _


class Nationality(models.Model):
    """Nacionalidad del profesional."""
    _name = "certprodoo.nationality"
    _description = "Nacionalidad"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    validate_fuc = fields.Boolean(
        string="Validar FUC",
        default=False,
        help="Si está marcado, los profesionales con esta nacionalidad "
             "requieren validación FUC.",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe una nacionalidad con ese nombre en esta compañía!",
        ),
    ]
