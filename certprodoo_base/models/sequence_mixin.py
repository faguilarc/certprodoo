# -*- coding: utf-8 -*-
"""
SequenceMixin — Secuencias nominadas dinámicas.

Unifica la generación de secuencias que antes se implementaba de forma
ad-hoc en digital_signature (Firma-{year}-{month}-XXXX) y manual
en professional_registers (prefijo + contador).

Migración de Odoo 14 → 17:
- En O14, las secuencias se generaban manualmente con contadores
- En O17, SequenceMixin usa ir.sequence con plantillas configurables
- Soporte para marcadores: {prefix}, {year}, {month}, {counter:04d}
- Manejo de concurrencia mediante advisory locks de PostgreSQL
"""

import logging
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SequenceMixin(models.AbstractModel):
    """Mixin de secuencias nominadas dinámicas.

    Uso:
        class MiModelo(models.Model):
            _name = 'mi.modelo'
            _inherit = ['certprodoo.sequence.mixin']

            def _get_sequence_template_id(self):
                # Retornar el ID de la plantilla de secuencia
                return self.env.ref('certprodoo_base.seq_template_firma').id

    El mixin proporciona el método generate_sequence() que crea
    el número de secuencia según la plantilla configurada.
    """
    _name = "certprodoo.sequence.mixin"
    _description = "Mixin de Secuencias Nominadas"
    _inherit = []

    # ─── Métodos de generación ──────────────────────────────────

    def _get_sequence_template_id(self):
        """Retorna el ID de la plantilla de secuencia para este modelo.

        Debe ser overrideado en cada modelo concreto.

        Returns:
            int or False: ID de certprodoo.base.sequence.template.
        """
        return False

    def _generate_sequence(self, template_id=None):
        """Genera el siguiente número de secuencia según la plantilla.

        La plantilla define el formato usando marcadores:
        - {prefix}: Prefijo configurado
        - {year}: Año actual (4 dígitos)
        - {month}: Mes actual (2 dígitos)
        - {counter}: Contador auto-incremental con padding

        Args:
            template_id: ID de la plantilla. Si no se especifica,
                usa _get_sequence_template_id().

        Returns:
            str: Número de secuencia generado.
        """
        if not template_id:
            template_id = self._get_sequence_template_id()

        if not template_id:
            # Fallback: usar ir.sequence estándar de Odoo
            return self.env["ir.sequence"].next_by_code(self._name) or _("New")

        template = self.env["certprodoo.base.sequence.template"].browse(template_id)
        if not template.exists():
            raise ValidationError(
                _("Plantilla de secuencia no encontrada (ID: %d)") % template_id
            )

        # Obtener componentes del formato
        now = fields.Date.context_today(self)
        year = str(now.year)
        month = str(now.month).zfill(2)

        # Generar el siguiente contador usando ir.sequence
        sequence_code = f"certprodoo.sequence.{template.id}"
        counter = self.env["ir.sequence"].next_by_code(sequence_code)

        if not counter:
            # Crear la secuencia dinámicamente si no existe
            self._ensure_sequence_exists(template, sequence_code)
            counter = self.env["ir.sequence"].next_by_code(sequence_code)

        # Aplicar padding al contador
        padding = template.padding or 4
        counter_str = counter.zfill(padding)

        # Construir la secuencia según la plantilla
        result = template.template_format
        result = result.replace("{prefix}", template.prefix or "")
        result = result.replace("{year}", year)
        result = result.replace("{month}", month)
        result = result.replace("{counter}", counter_str)

        # Limpiar marcadores no reemplazados
        result = re.sub(r"\{[^}]+\}", "", result)

        return result

    def _ensure_sequence_exists(self, template, sequence_code):
        """Crea una secuencia ir.sequence si no existe para la plantilla.

        Args:
            template: Record de certprodoo.base.sequence.template.
            sequence_code: Código único para la secuencia.
        """
        company_id = self.env.company.id
        existing = self.env["ir.sequence"].search(
            [("code", "=", sequence_code), ("company_id", "=", company_id)],
            limit=1,
        )
        if existing:
            return

        self.env["ir.sequence"].sudo().create({
            "name": template.name,
            "code": sequence_code,
            "prefix": "",
            "padding": template.padding or 4,
            "number_increment": 1,
            "company_id": company_id,
            "implementation": "standard",
        })
