# -*- coding: utf-8 -*-
"""
TeachingLevel — Nomenclador de Niveles de Enseñanza.

En O14 era nomenclators.teaching_level.
"""

from odoo import models, fields, api, _


class TeachingLevel(models.Model):
    """Nivel de enseñanza del sistema educativo."""
    _name = "certprodoo.teaching.level"
    _description = "Nivel de Enseñanza"
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

    # ─── Relaciones ────────────────────────────────────────────

    study_center_ids = fields.One2many(
        "certprodoo.study.center",
        "teaching_level_id",
        string="Centros de Estudio",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe un nivel de enseñanza con ese nombre en esta compañía!",
        ),
    ]
