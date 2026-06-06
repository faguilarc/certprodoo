# -*- coding: utf-8 -*-
"""
Profession — Nomenclador de Profesiones.

En O14 era nomenclators.professions.
Mejoras O17:
- Hereda BaseNomencatorMixin
- Fix: _order por nombre
- Relación con especialidades via One2many
"""

from odoo import models, fields, api, _


class Profession(models.Model):
    """Profesión del sistema de registro profesional."""
    _name = "certprodoo.profession"
    _description = "Profesión"
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

    specialty_ids = fields.One2many(
        "certprodoo.specialty",
        "profession_id",
        string="Especialidades",
    )
    specialty_count = fields.Integer(
        string="Especialidades",
        compute="_compute_specialty_count",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe una profesión con ese nombre en esta compañía!",
        ),
    ]

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("specialty_ids")
    def _compute_specialty_count(self):
        for rec in self:
            rec.specialty_count = len(rec.specialty_ids)
