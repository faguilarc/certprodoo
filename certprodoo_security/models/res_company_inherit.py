# -*- coding: utf-8 -*-
"""
ResCompany Inherit — Extiende compañía con usuario responsable.

En O14 era security.models.res_company.
"""

from odoo import models, fields


class ResCompany(models.Model):
    """Extensión de compañía para CertProdoo."""
    _inherit = "res.company"

    responsible_user_id = fields.Many2one(
        "res.users",
        string="Usuario Responsable",
        help="Usuario responsable de la compañía en el sistema CertProdoo.",
    )
