# -*- coding: utf-8 -*-
"""
WhoEnrolls — Nomenclador de "Quiénes se Inscriben".

En O14 era nomenclators.who_enrrols (typo corregido).
Usado para la sección "Sitio Web" del portal.
"""

from odoo import models, fields, api, _


class WhoEnrolls(models.Model):
    """Descripción de quiénes se inscriben en el sistema."""
    _name = "certprodoo.who.enrolls"
    _description = "Quiénes se Inscriben"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Text(
        string="Descripción",
        required=True,
        tracking=True,
    )
