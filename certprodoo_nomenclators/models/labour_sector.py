# -*- coding: utf-8 -*-
"""
LabourSector — Nomenclador de Tipos de Entidad / Sector Laboral.

En O14 era nomenclators.labour_sector.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LabourSector(models.Model):
    """Tipo de entidad o sector laboral."""
    _name = "certprodoo.labour.sector"
    _description = "Tipo de Entidad"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe un tipo de entidad con ese nombre en esta compañía!",
        ),
    ]

    # ─── Constraints ──────────────────────────────────────────

    @api.constrains("name")
    def _check_name(self):
        for rec in self:
            if rec.name:
                if len(rec.name) < 3 or len(rec.name) > 100:
                    raise ValidationError(
                        _("El nombre debe tener entre 3 y 100 caracteres.")
                    )
