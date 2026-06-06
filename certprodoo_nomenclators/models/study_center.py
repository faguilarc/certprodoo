# -*- coding: utf-8 -*-
"""
StudyCenter — Nomenclador de Centros de Estudio.

En O14 era nomenclators.study_centers.
"""

from odoo import models, fields, api, _


class StudyCenter(models.Model):
    """Centro de estudio donde se forma el profesional."""
    _name = "certprodoo.study.center"
    _description = "Centro de Estudio"
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
    teaching_level_id = fields.Many2one(
        "certprodoo.teaching.level",
        string="Nivel de Enseñanza",
        tracking=True,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe un centro de estudio con ese nombre en esta compañía!",
        ),
    ]
