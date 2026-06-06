# -*- coding: utf-8 -*-
"""
StateMixin — Máquina de estados configurable.

Extrae la lógica de security.state_configuration del módulo de seguridad
y la convierte en un componente reutilizable. En lugar de depender
directamente de security.state_configuration, el StateMixin define una
API limpia para que cada modelo declare sus estados y transiciones.

Migración de Odoo 14 → 17:
- Los estados dinámicos se almacenan en certprodoo.base.state.config
- Las transiciones permitidas en certprodoo.base.state.transition
- El StateMixin proporciona la API de consulta y validación
- Los modelos de negocio no conocen los detalles de implementación
- Soporte para historial de cambios vía process.history
- Integración con el motor de flujo (emails, timers)
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..utils.constants import (
    STATE_PRIORITY_DRAFT,
)

_logger = logging.getLogger(__name__)


class StateMixin(models.AbstractModel):
    """Mixin de máquina de estados configurable.

    Uso:
        class MiModelo(models.Model):
            _name = 'mi.modelo'
            _inherit = ['certprodoo.state.mixin']

            # El campo state se hereda de BaseProcessRequest.
            # Si el modelo no hereda de BaseProcessRequest,
            # definir el campo state manualmente.

    Atributos de clase configurables:
        _state_model_name: Nombre del modelo (default: self._name).
            Se usa para buscar la configuración de estados.
    """
    _name = "certprodoo.state.mixin"
    _description = "Mixin de Máquina de Estados"
    _inherit = []

    _state_model_name = None  # Override en modelo concreto si _name difiere

    # ─── Métodos de consulta de estados ─────────────────────────

    @api.model
    def _get_state_model_name(self):
        """Retorna el nombre del modelo para buscar estados.
        Override si el _name del modelo difiere del que se usa
        en la configuración de estados.
        """
        return self._state_model_name or self._name

    @api.model
    def _get_state_selection(self):
        """Retorna la lista de estados configurados para este modelo.

        Cada estado se obtiene de certprodoo.base.state.config
        ordenado por prioridad. Si no hay configuración, retorna
        un estado por defecto.
        """
        model_name = self._get_state_model_name()
        states = self.env["certprodoo.base.state.config"].search(
            [("model_name", "=", model_name)],
            order="priority asc",
        )
        if states:
            return [(s.code, s.name) for s in states]
        # Fallback: estado borrador mínimo
        return [("draft", "Borrador")]

    @api.model
    def _get_default_state(self):
        """Retorna el estado por defecto (menor prioridad)."""
        model_name = self._get_state_model_name()
        states = self.env["certprodoo.base.state.config"].search(
            [("model_name", "=", model_name)],
            order="priority asc",
            limit=1,
        )
        if states:
            return states.code
        return "draft"

    def _get_available_states(self):
        """Retorna los estados configurados para este modelo.

        Returns:
            recordset: Estados configurados (certprodoo.base.state.config).
        """
        model_name = self._get_state_model_name()
        return self.env["certprodoo.base.state.config"].search(
            [("model_name", "=", model_name)],
            order="priority asc",
        )

    def _get_next_state(self):
        """Determina el próximo estado válido según la configuración.

        Returns:
            certprodoo.base.state.config or False: Próximo estado.
        """
        self.ensure_one()
        transitions = self.env["certprodoo.base.state.transition"].search(
            [("model_name", "=", self._get_state_model_name()),
             ("from_code", "=", self.state)],
            limit=1,
        )
        if transitions:
            return self.env["certprodoo.base.state.config"].search(
                [("code", "=", transitions.to_code),
                 ("model_name", "=", self._get_state_model_name())],
                limit=1,
            )
        return False

    def _get_available_transitions(self):
        """Retorna las transiciones disponibles para el estado actual.

        Returns:
            recordset: Transiciones configuradas para el estado actual.
        """
        self.ensure_one()
        return self.env["certprodoo.base.state.transition"].search([
            ("model_name", "=", self._get_state_model_name()),
            ("from_code", "=", self.state),
            ("active", "=", True),
        ])

    def _can_transition_to(self, target_state):
        """Verifica si la transición al estado destino es válida.

        Args:
            target_state: Código del estado destino.

        Returns:
            bool: True si la transición es permitida.
        """
        self.ensure_one()
        if not self.state:
            return True  # Primer estado

        transition = self.env["certprodoo.base.state.transition"].search(
            [("model_name", "=", self._get_state_model_name()),
             ("from_code", "=", self.state),
             ("to_code", "=", target_state)],
            limit=1,
        )
        return bool(transition)

    def _validate_transition(self, target_state):
        """Valida que la transición sea permitida, lanza error si no.

        Args:
            target_state: Código del estado destino.

        Raises:
            ValidationError: Si la transición no está permitida.
        """
        self.ensure_one()
        if not self._can_transition_to(target_state):
            current_label = dict(self._fields["state"].selection).get(
                self.state, self.state
            )
            target_label = dict(self._fields["state"].selection).get(
                target_state, target_state
            )
            raise ValidationError(
                _(
                    "No se puede cambiar de '%(current)s' a '%(target)s'. "
                    "La transición no está permitida."
                )
                % {"current": current_label, "target": target_label}
            )

    def _trigger_state_action(self, target_state):
        """Ejecuta acciones asociadas a una transición de estado.

        Override en modelos concretos para agregar lógica específica
        como envío de correos, creación de notificaciones, etc.

        Args:
            target_state: Código del estado destino.
        """
        pass

    def _log_state_change(self, old_state, new_state, observation=None,
                          transition_id=None, old_label=None, new_label=None,
                          is_automatic=False):
        """Registra el cambio de estado en el historial.

        Crea un registro en certprodoo.base.process.history con
        los detalles del cambio.

        Args:
            old_state: Estado anterior.
            new_state: Estado nuevo.
            observation: Observación opcional del cambio.
            transition_id: ID de la transición ejecutada (si aplica).
            old_label: Etiqueta legible del estado anterior.
            new_label: Etiqueta legible del estado nuevo.
            is_automatic: Si True, el cambio fue automático (timer).
        """
        self.ensure_one()

        try:
            self.env["certprodoo.base.process.history"].sudo().create({
                "res_id": self.id,
                "model_name": self._name,
                "old_state": old_state,
                "new_state": new_state,
                "old_state_label": old_label or old_state,
                "new_state_label": new_label or new_state,
                "user_id": self.env.uid,
                "date": fields.Datetime.now(),
                "observation": observation or _("Cambio de estado: %s → %s") % (
                    old_state, new_state
                ),
                "transition_id": transition_id,
                "is_automatic": is_automatic,
            })
        except Exception as e:
            # El historial nunca debe romper la operación principal
            _logger.error(
                "Error registrando cambio de estado para %s#%d: %s",
                self._name, self.id, e,
            )

        # También registrar en el log de auditoría
        if hasattr(self, '_log_audit_action'):
            action_label = _("Cambio automático de estado") if is_automatic else _("Cambio de estado")
            self._log_audit_action(
                action="state_change",
                description="%s: %s → %s%s" % (
                    action_label,
                    old_label or old_state,
                    new_label or new_state,
                    " (%s)" % observation if observation else "",
                ),
            )

    # ─── Métodos de acción para botones ────────────────────────

    def action_change_state(self):
        """Abre el wizard de cambio de estado.

        Se usa como acción de botón en los formularios:
            <button name="action_change_state"
                    type="object"
                    string="Cambiar Estado"
                    class="oe_highlight"/>
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Cambiar Estado"),
            "res_model": "certprodoo.base.state.change.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model_name": self._name,
                "default_res_id": self.id,
                "default_current_state": self.state,
                "active_model": self._name,
                "active_id": self.id,
            },
        }
