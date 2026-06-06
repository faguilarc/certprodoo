# -*- coding: utf-8 -*-
"""
ProcessHistory — Historial de cambios de estado.

Registra cada transición de estado en los modelos que heredan
de BaseProcessRequest. Es creado automáticamente por
StateMixin._log_state_change().
"""

from odoo import models, fields, api, _


class ProcessHistory(models.Model):
    """Registro de cambio de estado de una solicitud.

    Cada vez que un registro cambia de estado, se crea un
    registro aquí con el estado anterior, el nuevo, el usuario
    que lo ejecutó y la fecha/hora.

    La relación One2many se declara en BaseProcessRequest.history_ids.
    """
    _name = "certprodoo.base.process.history"
    _description = "Historial de Cambio de Estado"
    _order = "date desc, id desc"
    _rec_name = "date"

    res_id = fields.Integer(
        string="ID del Registro",
        required=True,
        index=True,
        help="ID del registro dentro de su modelo.",
    )
    model_name = fields.Char(
        string="Modelo",
        required=True,
        index=True,
        help="Nombre técnico del modelo al que pertenece el registro.",
    )
    old_state = fields.Char(
        string="Estado Anterior",
        help="Código del estado anterior al cambio.",
    )
    new_state = fields.Char(
        string="Estado Nuevo",
        required=True,
        help="Código del estado después del cambio.",
    )
    old_state_label = fields.Char(
        string="Etiqueta Estado Anterior",
        help="Nombre legible del estado anterior.",
    )
    new_state_label = fields.Char(
        string="Etiqueta Estado Nuevo",
        help="Nombre legible del estado nuevo.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user,
        required=True,
        help="Usuario que ejecutó el cambio de estado.",
    )
    date = fields.Datetime(
        string="Fecha y Hora",
        default=fields.Datetime.now,
        required=True,
    )
    observation = fields.Text(
        string="Observación",
        help="Observación ingresada durante el cambio de estado.",
    )
    transition_id = fields.Many2one(
        "certprodoo.base.state.transition",
        string="Transición",
        help="Transición que se ejecutó (si aplica).",
    )
    is_automatic = fields.Boolean(
        string="Automático",
        default=False,
        help="Si True, el cambio fue generado automáticamente por un timer.",
    )
    email_sent = fields.Boolean(
        string="Correo Enviado",
        default=False,
        help="Si True, se envió un correo automático asociado a esta transición.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    # ─── Métodos de consulta ────────────────────────────────────

    @api.model
    def get_process_history(self, model_name, res_id):
        """Retorna el historial de cambios de estado de un registro.

        Args:
            model_name: Nombre técnico del modelo.
            res_id: ID del registro.

        Returns:
            recordset: Registros de historial ordenados por fecha.
        """
        return self.search(
            [("model_name", "=", model_name), ("res_id", "=", res_id)],
            order="date desc",
        )

    @api.model
    def get_last_state_change(self, model_name, res_id):
        """Retorna el último cambio de estado de un registro.

        Args:
            model_name: Nombre técnico del modelo.
            res_id: ID del registro.

        Returns:
            recordset: Último registro de historial.
        """
        return self.search(
            [("model_name", "=", model_name), ("res_id", "=", res_id)],
            order="date desc",
            limit=1,
        )

    @api.model
    def get_state_duration(self, model_name, res_id, state_code):
        """Calcula cuánto tiempo estuvo un registro en un estado específico.

        Útil para los timers de auto-transición.

        Args:
            model_name: Nombre técnico del modelo.
            res_id: ID del registro.
            state_code: Código del estado a medir.

        Returns:
            float: Duración en horas, o 0 si aún está en ese estado.
        """
        from datetime import datetime

        entries = self.search(
            [("model_name", "=", model_name), ("res_id", "=", res_id),
             ("new_state", "=", state_code)],
            order="date desc",
            limit=1,
        )
        if not entries:
            return 0.0

        # Buscar la salida de ese estado
        exit_entries = self.search(
            [("model_name", "=", model_name), ("res_id", "=", res_id),
             ("old_state", "=", state_code)],
            order="date asc",
            limit=1,
        )

        start = entries.date
        end = exit_entries.date if exit_entries else fields.Datetime.now()

        delta = end - start
        return delta.total_seconds() / 3600.0
