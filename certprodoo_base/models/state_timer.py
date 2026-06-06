# -*- coding: utf-8 -*-
"""
StateTimer — Reglas de auto-transición por tiempo.

Permite configurar que un registro cambie automáticamente de estado
después de estar un tiempo determinado en un estado. Por ejemplo:
- Si una solicitud lleva 5 días en "validación", pasar a "aprobada"
- Si una solicitud lleva 3 días en "proceso", enviar recordatorio
- Al cambiar automáticamente, se puede enviar un correo notificando

El cron job `certprodoo_base.state_timer_cron` ejecuta las
verificaciones periódicamente.
"""

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StateTimer(models.Model):
    """Regla de auto-transición por tiempo.

    Define que si un registro permanece en un estado durante
    un tiempo determinado, se ejecuta una acción automática:
    - Cambio de estado automático
    - Envío de correo de notificación/recordatorio
    - Ambos

    Uso:
        Se configura desde CertProdoo → Configuración → Transiciones.
        Al crear una transición, se le pueden agregar reglas de timer.

        Ejemplo: Transición "draft → processing"
        Timer: Duración 7 días → Auto-transición a "cancelled"
               con correo de notificación
    """
    _name = "certprodoo.base.state.timer"
    _description = "Regla de Temporizador de Estado"
    _order = "model_name, from_code"
    _rec_name = "display_name"

    # ─── Campos Básicos ────────────────────────────────────────

    model_name = fields.Char(
        string="Modelo",
        required=True,
        index=True,
        help="Nombre técnico del modelo al que aplica esta regla.",
    )
    from_code = fields.Char(
        string="Estado a Monitorizar",
        required=True,
        help="Código del estado que se monitoriza. "
             "El timer comienza cuando un registro entra en este estado.",
    )
    to_code = fields.Char(
        string="Estado Destino Auto",
        required=True,
        help="Código del estado al que se cambiará automáticamente "
             "al expirar el tiempo.",
    )
    transition_id = fields.Many2one(
        "certprodoo.base.state.transition",
        string="Transición Asociada",
        ondelete="cascade",
        help="Transición que se usará para ejecutar el cambio automático. "
             "Si se configura, se respetan las reglas de correo de la transición.",
    )

    # ─── Configuración de Tiempo ───────────────────────────────

    duration = fields.Integer(
        string="Duración",
        required=True,
        default=1,
        help="Cantidad de tiempo antes de ejecutar la auto-transición.",
    )
    duration_unit = fields.Selection(
        [("minutes", "Minutos"),
         ("hours", "Horas"),
         ("days", "Días"),
         ("weeks", "Semanas")],
        string="Unidad de Tiempo",
        required=True,
        default="days",
        help="Unidad de medida de la duración.",
    )
    duration_timedelta = fields.Float(
        string="Duración (Horas)",
        compute="_compute_duration_timedelta",
        store=True,
        help="Duración convertida a horas para comparaciones.",
    )

    # ─── Configuración de Acción ───────────────────────────────

    action_type = fields.Selection(
        [("state_change", "Cambio de Estado"),
         ("email_only", "Solo Correo"),
         ("state_change_and_email", "Cambio de Estado + Correo")],
        string="Tipo de Acción",
        required=True,
        default="state_change_and_email",
        help="Qué hacer al expirar el timer:\n"
             "- Cambio de Estado: Solo cambia el estado\n"
             "- Solo Correo: Envía correo sin cambiar estado (recordatorio)\n"
             "- Ambos: Cambia estado y envía correo",
    )

    # ─── Configuración de Correo ───────────────────────────────

    auto_email = fields.Boolean(
        string="Correo Automático",
        default=True,
        help="Si True, se envía un correo al ejecutarse el timer.",
    )
    email_template_id = fields.Many2one(
        "mail.template",
        string="Plantilla de Correo",
        domain="[('model_id.model', '=', model_name)]",
        help="Plantilla de correo a usar cuando se ejecuta el timer. "
             "Si la transición asociada tiene plantilla, se usa esa.",
    )
    email_recipients = fields.Selection(
        [("applicant", "Solicitante"),
         ("responsible", "Responsable"),
         ("applicant_and_responsible", "Solicitante y Responsable"),
         ("custom", "Personalizado")],
        string="Destinatarios",
        default="applicant_and_responsible",
    )
    attach_documents = fields.Boolean(
        string="Adjuntar Documentos",
        default=False,
        help="Si True, se incluyen los documentos adjuntos del registro.",
    )

    # ─── Estado ────────────────────────────────────────────────

    active = fields.Boolean(
        string="Activo",
        default=True,
    )
    last_execution = fields.Datetime(
        string="Última Ejecución",
        readonly=True,
        help="Última vez que este timer ejecutó una acción.",
    )

    _sql_constraints = [
        (
            "timer_uniq",
            "unique (model_name, from_code, to_code)",
            "Ya existe un timer para esta combinación de modelo y estados!",
        ),
    ]

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("duration", "duration_unit")
    def _compute_duration_timedelta(self):
        """Convierte la duración a horas para comparaciones rápidas."""
        multipliers = {
            "minutes": 1.0 / 60.0,
            "hours": 1.0,
            "days": 24.0,
            "weeks": 168.0,
        }
        for record in self:
            record.duration_timedelta = record.duration * multipliers.get(
                record.duration_unit, 24.0
            )

    # ─── Métodos de Ejecución ──────────────────────────────────

    def _get_expiry_datetime(self, entry_date):
        """Calcula la fecha/hora en que expira el timer.

        Args:
            entry_date: Fecha/hora en que el registro entró al estado.

        Returns:
            datetime: Fecha/hora de expiración.
        """
        deltas = {
            "minutes": timedelta(minutes=self.duration),
            "hours": timedelta(hours=self.duration),
            "days": timedelta(days=self.duration),
            "weeks": timedelta(weeks=self.duration),
        }
        return entry_date + deltas.get(self.duration_unit, timedelta(days=self.duration))

    @api.model
    def _cron_check_timers(self):
        """Cron job: verifica y ejecuta timers expirados.

        Para cada regla de timer activa:
        1. Busca registros en el estado monitorizado
        2. Verifica si el tiempo ha expirado
        3. Ejecuta la acción configurada (cambio de estado, correo, o ambos)

        Se ejecuta cada hora por defecto (configurable en ir.cron).
        """
        now = fields.Datetime.now()
        timer_rules = self.search([("active", "=", True)])

        _logger.info("Cron de timers: verificando %d reglas activas", len(timer_rules))

        for rule in timer_rules:
            try:
                rule._check_and_execute(now)
            except Exception as e:
                _logger.error(
                    "Error ejecutando timer %s: %s",
                    rule.display_name, e,
                )

    def _check_and_execute(self, now=None):
        """Verifica y ejecuta esta regla de timer.

        Busca registros en el estado from_code y verifica si
        el tiempo ha expirado desde que entraron en ese estado.

        Args:
            now: Fecha/hora actual (para testing).
        """
        now = now or fields.Datetime.now()
        model_name = self.model_name

        # Obtener el modelo dinámicamente
        model = self.env.get(model_name)
        if not model:
            _logger.warning("Timer: modelo %s no encontrado", model_name)
            return

        # Buscar registros en el estado monitorizado
        records = model.search([
            ("state", "=", self.from_code),
        ])

        if not records:
            return

        for record in records:
            try:
                self._check_record_timer(record, now)
            except Exception as e:
                _logger.error(
                    "Error verificando timer para %s#%d: %s",
                    model_name, record.id, e,
                )

    def _check_record_timer(self, record, now):
        """Verifica si un registro específico ha expirado su timer.

        Args:
            record: Registro a verificar.
            now: Fecha/hora actual.
        """
        # Buscar la última entrada al estado actual en el historial
        history_model = self.env["certprodoo.base.process.history"]
        last_entry = history_model.search(
            [("model_name", "=", self.model_name),
             ("res_id", "=", record.id),
             ("new_state", "=", self.from_code)],
            order="date desc",
            limit=1,
        )

        if not last_entry:
            # Si no hay historial, usar create_date como fallback
            entry_date = record.create_date
            if not entry_date:
                return
        else:
            entry_date = last_entry.date

        # Calcular expiración
        expiry = self._get_expiry_datetime(entry_date)

        if now >= expiry:
            _logger.info(
                "Timer expirado para %s#%d: estado %s → %s",
                self.model_name, record.id, self.from_code, self.to_code,
            )
            self._execute_timer_action(record)

    def _execute_timer_action(self, record):
        """Ejecuta la acción del timer sobre un registro.

        Args:
            record: Registro sobre el que ejecutar la acción.
        """
        observation = _(
            "Cambio automático por temporizador: "
            "el registro llevaba más de %(duration)d %(unit)s en estado '%(state)s'"
        ) % {
            "duration": self.duration,
            "unit": dict(self._fields["duration_unit"].selection).get(
                self.duration_unit, self.duration_unit
            ),
            "state": self.from_code,
        }

        if self.action_type in ("state_change", "state_change_and_email"):
            # Usar la transición asociada si existe
            if self.transition_id:
                try:
                    self.transition_id.sudo().execute_transition(
                        record, observation=observation,
                    )
                except ValidationError as e:
                    _logger.warning(
                        "Timer: transición bloqueada para %s#%d: %s",
                        self.model_name, record.id, e,
                    )
                    return
            else:
                # Cambio directo sin transición
                record.sudo().write({"state": self.to_code})
                # Registrar en historial
                record._log_state_change(
                    self.from_code, self.to_code,
                    observation=observation,
                    is_automatic=True,
                )

        if self.action_type in ("email_only", "state_change_and_email"):
            if self.auto_email:
                self._send_timer_email(record, observation)

        # Actualizar última ejecución
        self.last_execution = fields.Datetime.now()

    def _send_timer_email(self, record, observation=None):
        """Envía el correo asociado al timer.

        Args:
            record: Registro origen.
            observation: Observación del cambio automático.
        """
        from ..utils.email_helpers import get_default_email_from

        state_labels = dict(record._fields.get('state', self._fields.get('from_code', {})).selection) if 'state' in record._fields else {}
        from_label = state_labels.get(self.from_code, self.from_code)
        to_label = state_labels.get(self.to_code, self.to_code)

        if self.email_template_id:
            try:
                email_values = self._get_timer_email_values(record)
                self.email_template_id.send_mail(
                    record.id,
                    force_send=True,
                    email_values=email_values if email_values else None,
                )
                return
            except Exception as e:
                _logger.error("Error enviando correo de timer con plantilla: %s", e)

        # Correo básico
        subject = _("[Automático] %s - Cambio de estado: %s → %s") % (
            record.name or record.display_name, from_label, to_label
        )
        body = _(
            "<p>El registro <strong>%(name)s</strong> ha cambiado de estado "
            "automáticamente por temporizador:</p>"
            "<ul>"
            "<li>Estado anterior: <strong>%(from_state)s</strong></li>"
            "<li>Estado nuevo: <strong>%(to_state)s</strong></li>"
            "<li>Motivo: %(obs)s</li>"
            "</ul>"
        ) % {
            "name": record.display_name,
            "from_state": from_label,
            "to_state": to_label,
            "obs": observation or "",
        }

        try:
            email_to = self._get_timer_recipients(record)
            mail = self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_from': get_default_email_from(self.env),
                'email_to': email_to,
                'model': record._name,
                'res_id': record.id,
            })
            if self.attach_documents and hasattr(record, 'attachment_ids') and record.attachment_ids:
                mail.write({
                    'attachment_ids': [(4, att.id) for att in record.attachment_ids],
                })
            mail.send()
        except Exception as e:
            _logger.error("Error enviando correo básico de timer: %s", e)

    def _get_timer_email_values(self, record):
        """Construye los valores de email para el timer."""
        values = {}
        recipients = self._get_timer_recipients(record)
        if recipients:
            values['email_to'] = recipients
        if self.attach_documents and hasattr(record, 'attachment_ids') and record.attachment_ids:
            values['attachment_ids'] = [(4, att.id) for att in record.attachment_ids]
        return values

    def _get_timer_recipients(self, record):
        """Obtiene los destinatarios del correo del timer."""
        recipients = []
        if self.email_recipients in ("applicant", "applicant_and_responsible"):
            if hasattr(record, 'user_id') and record.user_id.email:
                recipients.append(record.user_id.email)
        if self.email_recipients in ("responsible", "applicant_and_responsible"):
            if hasattr(record, 'user_on_charge') and record.user_on_charge.email:
                recipients.append(record.user_on_charge.email)
        return ','.join(recipients)
