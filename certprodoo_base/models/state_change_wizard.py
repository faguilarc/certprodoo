# -*- coding: utf-8 -*-
"""
StateChangeWizard — Wizard para cambiar de estado con observación.

Permite al usuario cambiar el estado de una solicitud seleccionando
la transición deseada y agregando una observación. El wizard:
- Muestra solo las transiciones válidas según el estado actual
- Obliga a ingresar observación si la transición lo requiere
- Ejecuta la transición usando el motor de flujo (con emails, etc.)
- Registra el cambio en el historial

Uso desde cualquier modelo que herede certprodoo.base.process:
    <button name="%(certprodoo_base.action_state_change_wizard)d"
            type="action"
            string="Cambiar Estado"
            class="oe_highlight"/>
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StateChangeWizard(models.TransientModel):
    """Wizard para cambio de estado guiado.

    Flujo:
    1. El usuario presiona "Cambiar Estado" en el formulario
    2. Se abre el wizard mostrando las transiciones disponibles
    3. El usuario selecciona la transición y agrega observación
    4. El wizard ejecuta la transición con todo el flujo configurado
    """
    _name = "certprodoo.base.state.change.wizard"
    _description = "Asistente de Cambio de Estado"

    # ─── Campos del Wizard ─────────────────────────────────────

    model_name = fields.Char(
        string="Modelo",
        required=True,
        help="Nombre técnico del modelo del registro.",
    )
    res_id = fields.Integer(
        string="ID del Registro",
        required=True,
        help="ID del registro que se va a cambiar de estado.",
    )
    current_state = fields.Char(
        string="Estado Actual",
        readonly=True,
        help="Estado actual del registro.",
    )
    current_state_label = fields.Char(
        string="Etiqueta Estado Actual",
        readonly=True,
    )
    transition_id = fields.Many2one(
        "certprodoo.base.state.transition",
        string="Transición",
        required=True,
        domain="[('model_name', '=', model_name), ('from_code', '=', current_state), ('active', '=', True)]",
        help="Transición a ejecutar. Solo se muestran las válidas para el estado actual.",
    )
    observation = fields.Text(
        string="Observación",
        help="Observación del cambio de estado. Requerida si la transición lo exige.",
    )
    target_state = fields.Char(
        string="Estado Destino",
        compute="_compute_target_state",
        help="Estado al que se cambiará al ejecutar la transición.",
    )
    target_state_label = fields.Char(
        string="Etiqueta Estado Destino",
        compute="_compute_target_state",
    )
    require_observation = fields.Boolean(
        string="Requiere Observación",
        compute="_compute_require_observation",
        help="Si True, la observación es obligatoria.",
    )
    will_send_email = fields.Boolean(
        string="Se Enviará Correo",
        compute="_compute_will_send_email",
        help="Si True, se enviará un correo automático con esta transición.",
    )
    has_timer = fields.Boolean(
        string="Tiene Temporizador",
        compute="_compute_has_timer",
        help="Si True, esta transición tiene reglas de temporizador.",
    )

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("transition_id")
    def _compute_target_state(self):
        for wizard in self:
            if wizard.transition_id:
                wizard.target_state = wizard.transition_id.to_code
                # Buscar la etiqueta del estado destino
                state_config = self.env["certprodoo.base.state.config"].search(
                    [("model_name", "=", wizard.model_name),
                     ("code", "=", wizard.transition_id.to_code)],
                    limit=1,
                )
                wizard.target_state_label = state_config.name if state_config else wizard.transition_id.to_code
            else:
                wizard.target_state = False
                wizard.target_state_label = False

    @api.depends("transition_id")
    def _compute_require_observation(self):
        for wizard in self:
            wizard.require_observation = wizard.transition_id.require_observation if wizard.transition_id else False

    @api.depends("transition_id")
    def _compute_will_send_email(self):
        for wizard in self:
            wizard.will_send_email = wizard.transition_id.auto_email if wizard.transition_id else False

    @api.depends("transition_id")
    def _compute_has_timer(self):
        for wizard in self:
            wizard.has_timer = bool(wizard.transition_id.timer_rule_ids) if wizard.transition_id else False

    # ─── Métodos de Acción ─────────────────────────────────────

    def action_execute(self):
        """Ejecuta la transición seleccionada.

        Valida que:
        - La observación esté presente si es requerida
        - El registro exista y esté en el estado correcto
        - El usuario tenga permisos para la transición

        Luego ejecuta la transición con todo el flujo configurado.
        """
        self.ensure_one()

        # Validar observación requerida
        if self.require_observation and not self.observation:
            raise ValidationError(
                _("Esta transición requiere una observación. "
                  "Por favor ingrese una observación antes de continuar.")
            )

        # Obtener el registro
        model = self.env.get(self.model_name)
        if not model:
            raise ValidationError(_("Modelo no encontrado: %s") % self.model_name)

        record = model.browse(self.res_id)
        if not record.exists():
            raise ValidationError(_("Registro no encontrado."))

        # Validar que el estado no ha cambiado desde que se abrió el wizard
        if record.state != self.current_state:
            raise ValidationError(
                _("El estado del registro ha cambiado desde que se abrió "
                  "este asistente. El estado actual es: %s") % record.state
            )

        # Ejecutar la transición
        try:
            self.transition_id.execute_transition(record, observation=self.observation)
        except ValidationError:
            raise
        except Exception as e:
            _logger.error(
                "Error ejecutando transición %s: %s",
                self.transition_id.label, e,
            )
            raise ValidationError(
                _("Error al ejecutar la transición: %s") % str(e)
            )

        return {"type": "ir.actions.act_window_close"}

    # ─── Método de Contexto ────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        """Configura el wizard con los datos del registro actual.

        Espera que el contexto tenga:
        - active_model: Modelo del registro
        - active_id: ID del registro
        """
        defaults = super().default_get(fields_list)

        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            model = self.env.get(active_model)
            if model:
                record = model.browse(active_id)
                if record.exists() and hasattr(record, 'state'):
                    state_config = self.env["certprodoo.base.state.config"].search(
                        [("model_name", "=", active_model),
                         ("code", "=", record.state)],
                        limit=1,
                    )
                    defaults.update({
                        'model_name': active_model,
                        'res_id': active_id,
                        'current_state': record.state,
                        'current_state_label': state_config.name if state_config else record.state,
                    })

        return defaults
