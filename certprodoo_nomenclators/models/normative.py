# -*- coding: utf-8 -*-
"""
Normative — Nomenclador de Normativas Legales.

En O14 era nomenclators.normative.
Mejoras O17:
- Usa ir.attachment Many2many correctamente
- name cambiado a Char (más apropiado que Text)
"""

from odoo import models, fields, api, _


class Normative(models.Model):
    """Normativa legal del sistema."""
    _name = "certprodoo.normative"
    _description = "Normativa"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "certprodoo_normative_attachment_rel",
        "normative_id",
        "attachment_id",
        string="Documentos Adjuntos",
        help="Archivos adjuntos de la normativa.",
    )
