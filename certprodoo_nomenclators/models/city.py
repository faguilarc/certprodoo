# -*- coding: utf-8 -*-
"""
City — Nomenclador de Municipios.

Modelo propio de municipio para CertProdoo, independiente de
base_address_city (que no siempre está disponible en O17 CE).

En O14 heredaba de res.city (base_address_city).
En O17 creamos certprodoo.city como modelo autónomo que no
requiere dependencias externas.

Campos:
- name: Nombre del municipio
- code: Código del nomenclador cubano
- state_id: Provincia (res.country.state)
- country_id: País (res.country)
"""

from odoo import models, fields, api, _


class City(models.Model):
    """Municipio del sistema de nomencladores."""
    _name = "certprodoo.city"
    _description = "Municipio"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "state_id, name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    state_id = fields.Many2one(
        "res.country.state",
        string="Provincia",
        tracking=True,
        ondelete="restrict",
        domain="[('country_id.code', '=', 'CU')]",
    )
    country_id = fields.Many2one(
        "res.country",
        string="País",
        default=lambda self: self._default_country(),
        tracking=True,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "name_state_uniq",
            "unique(name, state_id, company_id)",
            "Ya existe un municipio con ese nombre en esta provincia!",
        ),
    ]

    def _default_country(self):
        """Default a Cuba si existe en el sistema."""
        cuba = self.env.ref("base.cu", raise_if_not_found=False)
        return cuba.id if cuba else False
