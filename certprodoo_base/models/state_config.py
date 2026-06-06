# -*- coding: utf-8 -*-
"""
StateConfig — Configuración de estados por modelo.

Reemplaza security.state_configuration con un modelo independiente
del módulo de seguridad. Es consumido por StateMixin.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StateConfig(models.Model):
    """Configuración de estados para un modelo.

    Define los estados disponibles y su orden (prioridad) para
    cada modelo que usa StateMixin.
    """
    _name = "certprodoo.base.state.config"
    _description = "Configuración de Estados"
    _order = "model_name, priority asc"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre del Estado",
        required=True,
        translate=True,
    )
    code = fields.Char(
        string="Código",
        required=True,
        help="Código interno del estado (ej. 'draft', 'approved').",
    )
    model_name = fields.Char(
        string="Modelo",
        required=True,
        index=True,
        help="Nombre técnico del modelo al que aplica este estado.",
    )
    priority = fields.Integer(
        string="Prioridad",
        required=True,
        default=1,
        help="Orden del estado. Menor valor = estado inicial.",
    )
    fold = fields.Boolean(
        string="Plegar en Kanban",
        default=False,
        help="Si True, los registros en este estado se pliegan en la vista Kanban.",
    )
    description = fields.Text(
        string="Descripción",
    )
    is_final = fields.Boolean(
        string="Estado Final",
        default=False,
        help="Si True, los registros en este estado no pueden cambiar a otro estado.",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    _sql_constraints = [
        (
            "code_model_uniq",
            "unique (code, model_name)",
            "El código de estado debe ser único por modelo!",
        ),
        (
            "priority_model_uniq",
            "unique (priority, model_name)",
            "La prioridad debe ser única por modelo!",
        ),
    ]

    @api.constrains("is_final")
    def _check_is_final(self):
        """No permite que haya más de 2 estados finales por modelo."""
        for record in self:
            final_count = self.search_count([
                ("model_name", "=", record.model_name),
                ("is_final", "=", True),
                ("id", "!=", record.id),
            ])
            if final_count >= 3:
                raise ValidationError(
                    _("No pueden haber más de 3 estados finales por modelo.")
                )
