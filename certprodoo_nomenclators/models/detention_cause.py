# -*- coding: utf-8 -*-
"""
DetentionCause — Nomenclador de Causas de Detención/Denegación/Cancelación.

En O14 era nomenclators.detention_causes.
Mejoras O17:
- Fix: validación de campos usa part.name en vez de self.name
- email_template y document_template se mantienen (se usan en flujo de estados)
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DetentionCause(models.Model):
    """Causa de detención, denegación o cancelación de un trámite."""
    _name = "certprodoo.detention.cause"
    _description = "Causa de Estado"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "cause_type, name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    description = fields.Char(
        string="Descripción",
        required=True,
        tracking=True,
    )
    cause_type = fields.Selection(
        [("detention", "Detención"),
         ("denial", "Denegación"),
         ("cancellation", "Cancelación")],
        string="Tipo de Causa",
        required=True,
        tracking=True,
    )
    email_template = fields.Html(
        string="Plantilla de Correo",
        tracking=True,
        help="Plantilla HTML para el correo automático cuando se aplica esta causa.",
    )
    document_template = fields.Html(
        string="Plantilla de Documento",
        tracking=True,
        help="Plantilla HTML para el documento generado cuando se aplica esta causa.",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe una causa con ese nombre en esta compañía!",
        ),
    ]

    # ─── Constraints ──────────────────────────────────────────

    @api.constrains("name")
    def _check_name(self):
        for rec in self:
            if rec.name:
                if len(rec.name) < 3 or len(rec.name) > 100:
                    raise ValidationError(
                        _("El nombre debe tener entre 3 y 100 caracteres.")
                    )
                if rec.name != rec.name.lstrip():
                    raise ValidationError(
                        _("El nombre no debe comenzar con espacios.")
                    )

    @api.constrains("description")
    def _check_description(self):
        for rec in self:
            if rec.description:
                if len(rec.description) < 10 or len(rec.description) > 255:
                    raise ValidationError(
                        _("La descripción debe tener entre 10 y 255 caracteres.")
                    )
                if rec.description != rec.description.lstrip():
                    raise ValidationError(
                        _("La descripción no debe comenzar con espacios.")
                    )
