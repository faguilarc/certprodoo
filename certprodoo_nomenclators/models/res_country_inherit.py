# -*- coding: utf-8 -*-
"""
ResCountry Inherit — Extiende país con código de país.

En O14 era nomenclators.models.res_country.
Mejoras O17:
- Fix: unlink() buscaba campo 'city' en vez de country
- Eliminado fields_view_get / fields_get (usar vistas en O17)
"""

from odoo import models, fields, api, _


class ResCountry(models.Model):
    """Extensión de país para CertProdoo."""
    _inherit = "res.country"

    country_code = fields.Char(
        string="Código del País",
        tracking=True,
        help="Código adicional del país para integraciones.",
    )

    _sql_constraints = [
        (
            "country_code_uniq",
            "unique(country_code)",
            "Ya existe un país con ese código!",
        ),
    ]
