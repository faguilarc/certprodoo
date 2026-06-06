# -*- coding: utf-8 -*-
"""
ResCompany Inherit — Extiende compañía con logo CertProdoo.

En O14 el logo era un modelo separado (nomenclators.logo).
En O17 lo ponemos directamente en res.company, que es más limpio
y evita un modelo innecesario.
"""

from odoo import models, fields, api, _


class ResCompany(models.Model):
    """Extensión de compañía para CertProdoo."""
    _inherit = "res.company"

    certprodoo_logo = fields.Binary(
        string="Logo CertProdoo",
        attachment=True,
        help="Logo del sistema CertProdoo para informes y portal web.",
    )
    certprodoo_logo_name = fields.Char(
        string="Nombre del Logo",
    )
