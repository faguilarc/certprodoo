# -*- coding: utf-8 -*-
"""
Specialty — Nomenclador de Especialidades.

En O14 era nomenclators.specialties.
Mejoras O17:
- Hereda BaseNomencatorMixin
- Relación Many2one con profesión
"""

from odoo import models, fields, api, _


class Specialty(models.Model):
    """Especialidad dentro de una profesión."""
    _name = "certprodoo.specialty"
    _description = "Especialidad"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "profession_id, name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Descripción",
        tracking=True,
    )
    profession_id = fields.Many2one(
        "certprodoo.profession",
        string="Profesión",
        required=True,
        tracking=True,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "name_profession_uniq",
            "unique(name, profession_id, company_id)",
            "Ya existe esa especialidad para esta profesión en esta compañía!",
        ),
    ]
