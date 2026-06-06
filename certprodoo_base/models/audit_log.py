# -*- coding: utf-8 -*-
"""
AuditLog — Registro centralizado de auditoría.

Reemplaza security.traces con un modelo genérico que no depende
del módulo de seguridad. Es creado automáticamente por AuditMixin.
"""

from odoo import models, fields, api


class AuditLog(models.Model):
    """Registro de auditoría del sistema.

    Cada operación CRUD en modelos que usan AuditMixin
    genera un registro aquí automáticamente.
    """
    _name = "certprodoo.base.audit.log"
    _description = "Registro de Auditoría"
    _order = "create_date desc"
    _rec_name = "model_name"

    model_name = fields.Char(
        string="Modelo",
        required=True,
        index=True,
        help="Nombre técnico del modelo (ej. professional_registers.inscription).",
    )
    res_id = fields.Integer(
        string="ID del Registro",
        required=True,
        index=True,
        help="ID del registro afectado dentro del modelo.",
    )
    record_display_name = fields.Char(
        string="Nombre del Registro",
        help="Nombre visible del registro afectado.",
    )
    action = fields.Selection(
        [
            ("create", "Creación"),
            ("write", "Edición"),
            ("unlink", "Eliminación"),
            ("state_change", "Cambio de Estado"),
            ("read", "Lectura"),
        ],
        string="Acción",
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user,
        index=True,
    )
    description = fields.Text(
        string="Descripción",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    # ─── Métodos de consulta ────────────────────────────────────

    @api.model
    def get_audit_trail(self, model_name, res_id):
        """Retorna el historial de auditoría de un registro.

        Args:
            model_name: Nombre del modelo.
            res_id: ID del registro.

        Returns:
            recordset: Registros de auditoría ordenados por fecha.
        """
        return self.search(
            [("model_name", "=", model_name), ("res_id", "=", res_id)],
            order="create_date desc",
        )

    @api.model
    def cleanup_old_logs(self, days=365):
        """Elimina registros de auditoría más antiguos que N días.

        Args:
            days: Número de días a conservar (default 365).

        Returns:
            int: Número de registros eliminados.
        """
        from datetime import timedelta

        cutoff = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([("create_date", "<", cutoff)])
        count = len(old_logs)
        old_logs.unlink()
        return count
