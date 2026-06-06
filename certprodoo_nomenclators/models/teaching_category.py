# -*- coding: utf-8 -*-
"""
TeachingCategory — Nomenclador de Categorías Docentes.

En O14 era nomenclators.teaching_categories.
"""

from odoo import models, fields, api, _


class TeachingCategory(models.Model):
    """Categoría docente del sistema educativo."""
    _name = "certprodoo.teaching.category"
    _description = "Categoría Docente"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Descripción",
        tracking=True,
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe una categoría docente con ese nombre en esta compañía!",
        ),
    ]
