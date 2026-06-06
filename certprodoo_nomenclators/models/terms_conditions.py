# -*- coding: utf-8 -*-
"""
TermsConditions — Nomenclador de Términos y Condiciones.

En O14 era nomenclators.terms_conditions.
Usado para la sección "Sitio Web" del portal.
"""

from odoo import models, fields, api, _


class TermsConditions(models.Model):
    """Términos y condiciones del sistema."""
    _name = "certprodoo.terms.conditions"
    _description = "Términos y Condiciones"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Título",
        required=True,
        tracking=True,
    )
    content = fields.Html(
        string="Contenido",
        tracking=True,
        help="Contenido HTML de los términos y condiciones.",
    )
