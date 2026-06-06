# -*- coding: utf-8 -*-
"""
ResCity Inherit — Extiende municipio con código.

En O14 era nomenclators.models.res_city.
Mejoras O17:
- Fix: unlink() tenía bug con msg indefinido
- Eliminado fields_view_get / fields_get
"""

from odoo import models, fields, api, _


class ResCity(models.Model):
    """Extensión de municipio para CertProdoo."""
    _inherit = "res.city"

    code = fields.Char(
        string="Código",
        tracking=True,
        help="Código del municipio según nomenclador cubano.",
    )
