# -*- coding: utf-8 -*-
"""
ResCountryState Inherit — Extiende provincia/estado.

En O14 era nomenclators.models.res_country_state.
Mejoras O17:
- Eliminado fields_view_get / fields_get
- Eliminado unlink con referencias incorrectas
"""

from odoo import models, fields, api, _


class ResCountryState(models.Model):
    """Extensión de provincia/estado para CertProdoo."""
    _inherit = "res.country.state"
