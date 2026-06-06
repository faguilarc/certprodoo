# -*- coding: utf-8 -*-
"""
AuditMixin — Trazabilidad automática de operaciones CRUD.

Reemplaza la funcionalidad de security.traces del módulo de seguridad,
pero como un mixin desacoplado. Cualquier modelo que incluya este mixin
obtendrá trazabilidad automática sin depender del módulo de seguridad.

Migración de Odoo 14 → 17:
- En O14, security.traces se creaba manualmente en cada create/write/unlink
- En O17, AuditMixin intercepta automáticamente los hooks del ORM
- El modelo de log es genérico y no pertenece a ningún módulo de negocio
- Configurable: se puede desactivar por modelo o excluir campos del chatter
- Los campos de mail.thread (message_ids, etc.) se excluyen automáticamente
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import AccessError

from ..utils.constants import (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_WRITE,
    AUDIT_ACTION_UNLINK,
    AUDIT_ACTION_SELECTION,
)

_logger = logging.getLogger(__name__)

# Modelos que no deben ser auditados (demasiado ruidosos o internos)
_AUDIT_EXCLUDED_MODELS = {
    "certprodoo.base.audit.log",
    "certprodoo.base.process.history",
    "ir.logging",
    "mail.mail",
    "mail.message",
    "mail.followers",
    "mail.notification",
    "mail.activity",
    "bus.bus",
    "ir.attachment",
}

# Campos del chatter y mail.thread que no se deben auditar
_MAIL_FIELDS = {
    "message_ids", "message_follower_ids", "message_partner_ids",
    "message_unread", "message_needaction", "message_has_error",
    "message_is_follower", "activity_ids", "activity_state",
    "activity_date_deadline", "activity_summary", "activity_user_id",
    "website_message_ids",
}


class AuditMixin(models.AbstractModel):
    """Mixin de auditoría para trazabilidad de operaciones CRUD.

    Uso:
        class MiModelo(models.Model):
            _name = 'mi.modelo'
            _inherit = ['certprodoo.audit.mixin']

            # Opcional: desactivar auditoría completa:
            _audit_enable = False

            # Opcional: desactivar solo algunos tipos:
            _audit_log_create = False
            _audit_log_write = False
            _audit_log_unlink = False

            # Opcional: excluir campos adicionales:
            _audit_exclude_fields = {'write_date', 'my_internal_field'}

    El mixin intercepta create, write y unlink para registrar
    automáticamente cada operación en certprodoo.base.audit.log.

    Atributos de clase configurables:
        _audit_enable: Master switch. Si False, no audita nada (default True).
        _audit_exclude_fields: Set de campos a excluir del log de cambios.
        _audit_log_create: Si True (default), registra creaciones.
        _audit_log_write: Si True (default), registra ediciones.
        _audit_log_unlink: Si True (default), registra eliminaciones.
        _audit_exclude_chatter_fields: Si True (default), excluye campos de
            mail.thread del log. Evita que cada mensaje del chatter genere
            una entrada de auditoría cuando el ORM llama a write().
    """
    _name = "certprodoo.audit.mixin"
    _description = "Mixin de Auditoría"
    _inherit = []

    # Campos configurables por modelo
    _audit_enable = True
    _audit_exclude_fields = {"write_date", "write_uid", "create_date", "create_uid"}
    _audit_log_create = True
    _audit_log_write = True
    _audit_log_unlink = True
    _audit_exclude_chatter_fields = True  # Evita que el chatter llene el log

    # ─── Hooks del ORM ──────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self._audit_enable and self._audit_log_create and self._name not in _AUDIT_EXCLUDED_MODELS:
            for record in records:
                self._log_audit_action(
                    action=AUDIT_ACTION_CREATE,
                    record=record,
                    description=_("Creación de registro"),
                )
        return records

    def write(self, vals):
        # Si la auditoría está desactivada para este modelo, saltar
        if not self._audit_enable or not self._audit_log_write or self._name in _AUDIT_EXCLUDED_MODELS:
            return super().write(vals)

        # Construir la lista de campos excluidos
        excluded = set(self._audit_exclude_fields)
        if self._audit_exclude_chatter_fields:
            excluded |= _MAIL_FIELDS

        # Detectar si el write es solo del chatter (solo campos mail.*)
        vals_keys = set(vals.keys())
        chatter_only = vals_keys and vals_keys.issubset(_MAIL_FIELDS | self._audit_exclude_fields)

        # Si el write es solo del chatter, no auditar
        if chatter_only:
            return super().write(vals)

        # Capturar cambios antes de escribir para el log
        changes = {}
        for field_name, new_value in vals.items():
            if field_name not in excluded and hasattr(self, field_name):
                old_value = getattr(self, field_name)
                if old_value != new_value:
                    field = self._fields.get(field_name)
                    if field and not field.compute:
                        changes[field_name] = {
                            "old": self._format_audit_value(old_value),
                            "new": self._format_audit_value(new_value),
                        }

        result = super().write(vals)

        if changes:
            description = _("Edición: %s") % ", ".join(
                "%s: %s → %s" % (k, v["old"], v["new"])
                for k, v in changes.items()
            )
            for record in self:
                self._log_audit_action(
                    action=AUDIT_ACTION_WRITE,
                    record=record,
                    description=description,
                )

        return result

    def unlink(self):
        if self._audit_enable and self._audit_log_unlink and self._name not in _AUDIT_EXCLUDED_MODELS:
            count = len(self)
            description = (
                _("Eliminación de %d registro(s)") % count
                if count > 1
                else _("Eliminación de registro")
            )
            for record in self:
                self._log_audit_action(
                    action=AUDIT_ACTION_UNLINK,
                    record=record,
                    description=description,
                )
        return super().unlink()

    # ─── Métodos de registro ────────────────────────────────────

    def _log_audit_action(self, action, record=None, description=""):
        """Registra una acción de auditoría en el log.

        Args:
            action: Tipo de acción (create/write/unlink/state_change).
            record: Registro afectado (self si no se especifica).
            description: Descripción legible de la acción.
        """
        record = record or self
        try:
            self.env["certprodoo.base.audit.log"].sudo().create({
                "model_name": self._name,
                "res_id": record.id,
                "action": action,
                "user_id": self.env.uid,
                "description": description,
                "record_display_name": record.display_name
                if hasattr(record, "display_name")
                else str(record.id),
            })
        except Exception as e:
            # La auditoría nunca debe romper la operación principal
            _logger.error(
                "Error registrando auditoría para %s#%d: %s",
                self._name,
                record.id,
                e,
            )

    def _format_audit_value(self, value):
        """Formatea un valor para el log de auditoría.

        Convierte recordsets a display_name, fechas a string,
        y maneja valores None/False consistentemente.
        """
        if value is None or value is False:
            return ""
        if isinstance(value, models.BaseModel):
            return value.display_name if len(value) == 1 else str(value.ids)
        if isinstance(value, (list, tuple)):
            return str(value)
        return str(value)
