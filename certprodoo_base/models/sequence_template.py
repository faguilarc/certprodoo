# -*- coding: utf-8 -*-
"""
SequenceTemplate — Plantillas de secuencias nominadas.

Define el formato de las secuencias que SequenceMixin generará.
Ejemplo: {prefix}-{year}-{month}-{counter:04d} → Firma-2026-06-0001
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SequenceTemplate(models.Model):
    """Plantilla de secuencia nominada.

    Define el formato y configuración de una secuencia.
    SequenceMixin usa estas plantillas para generar números únicos.

    Marcadores disponibles en template_format:
    - {prefix}: Valor del campo prefix
    - {year}: Año actual (4 dígitos)
    - {month}: Mes actual (2 dígitos)
    - {counter}: Contador auto-incremental con padding
    """
    _name = "certprodoo.base.sequence.template"
    _description = "Plantilla de Secuencia"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
    )
    prefix = fields.Char(
        string="Prefijo",
        help="Prefijo para la secuencia (ej. 'Firma', 'SOL').",
    )
    template_format = fields.Char(
        string="Formato",
        required=True,
        default="{prefix}-{year}-{month}-{counter}",
        help="Formato de la secuencia. Marcadores: {prefix}, {year}, {month}, {counter}",
    )
    model_name = fields.Char(
        string="Modelo",
        help="Nombre técnico del modelo que usa esta secuencia.",
    )
    padding = fields.Integer(
        string="Relleno",
        default=4,
        help="Número de dígitos del contador (ej. 4 → 0001).",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    @api.constrains("template_format")
    def _check_template_format(self):
        for record in self:
            if not record.template_format:
                continue
            # Verificar que contenga al menos {counter}
            if "{counter}" not in record.template_format:
                raise ValidationError(
                    _("El formato debe contener el marcador {counter}.")
                )
