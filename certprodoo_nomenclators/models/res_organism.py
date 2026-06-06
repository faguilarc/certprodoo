# -*- coding: utf-8 -*-
"""
ResOrganism — Nomenclador de Organismos Gubernamentales.

En O14 era res.organism (modelo nuevo, no herencia).
Mejoras O17:
- Fix: constraint de código usaba self.code en vez de rec.code
- Agregado company_id para multi-compañía
- _rec_name = siglas para mostrar acrónimo
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResOrganism(models.Model):
    """Organismo gubernamental cubano."""
    _name = "certprodoo.organism"
    _description = "Organismo"
    _order = "code"
    _rec_name = "siglas"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Organismo",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Código",
        required=True,
        tracking=True,
        help="Código numérico del organismo (1-3 dígitos).",
    )
    siglas = fields.Char(
        string="Siglas",
        required=True,
        tracking=True,
        help="Acrónimo del organismo (ej. MINDUS, CIMEX).",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "Ya existe un organismo con ese nombre!",
        ),
        (
            "code_uniq",
            "unique(code)",
            "Ya existe un organismo con ese código!",
        ),
    ]

    # ─── Constraints ──────────────────────────────────────────

    @api.constrains("code")
    def _check_code(self):
        for rec in self:
            if rec.code and not re.match(r'^[0-9]{1,3}$', rec.code):
                raise ValidationError(
                    _("El código debe tener entre 1 y 3 dígitos numéricos.")
                )
