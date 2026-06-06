# -*- coding: utf-8 -*-
"""
Structure — Nomenclador de Estructuras Organizativas.

En O14 era nomenclators.structures.
Usado para la sección "Sitio Web" del portal.
"""

from odoo import models, fields, api, _


class Structure(models.Model):
    """Estructura organizativa del sistema."""
    _name = "certprodoo.structure"
    _description = "Estructura"
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
