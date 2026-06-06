# -*- coding: utf-8 -*-
"""
StateTransition — Transiciones permitidas entre estados.

Define qué transiciones de estado están permitidas para cada modelo,
y permite configurar acciones automáticas:
- Envío de correo electrónico
- Adjuntar documentos al correo
- Requerir observación obligatoria
- Restringir por grupo de seguridad

Es consumido por StateMixin._can_transition_to().
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StateTransition(models.Model):
    """Transición permitida entre estados.

    Define qué cambios de estado son válidos para un modelo.
    Sin una transición definida, StateMixin rechazará el cambio.

    Además, permite configurar acciones automáticas:
    - auto_email: Enviar correo al ejecutar la transición
    - email_template_id: Plantilla de correo a usar
    - attach_documents: Incluir documentos adjuntos del registro
    - require_observation: Obligar al usuario a ingresar observación
    - group_id: Restringir la transición a un grupo
    """
    _name = "certprodoo.base.state.transition"
    _description = "Transición de Estado"
    _rec_name = "label"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    model_name = fields.Char(
        string="Modelo",
        required=True,
        index=True,
        tracking=True,
        help="Nombre técnico del modelo al que aplica esta transición.",
    )
    from_code = fields.Char(
        string="Estado Origen",
        required=True,
        tracking=True,
        help="Código del estado de origen.",
    )
    to_code = fields.Char(
        string="Estado Destino",
        required=True,
        tracking=True,
        help="Código del estado de destino.",
    )
    label = fields.Char(
        string="Etiqueta",
        compute="_compute_label",
        store=True,
        readonly=False,
    )
    action_method = fields.Char(
        string="Método de Acción",
        help="Método del modelo a ejecutar durante la transición (opcional). "
             "Se ejecuta DESPUÉS del envío de correo si auto_email=True.",
    )
    require_observation = fields.Boolean(
        string="Requiere Observación",
        default=False,
        help="Si True, el usuario debe ingresar una observación para esta transición.",
    )
    group_id = fields.Many2one(
        "res.groups",
        string="Grupo Permitido",
        help="Grupo de usuarios que puede ejecutar esta transición. "
             "Vacío = todos los usuarios con permiso de escritura.",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    # ─── Configuración de Correo Automático ─────────────────────

    auto_email = fields.Boolean(
        string="Correo Automático",
        default=False,
        tracking=True,
        help="Si True, se envía un correo automáticamente al ejecutar esta transición.",
    )
    email_template_id = fields.Many2one(
        "mail.template",
        string="Plantilla de Correo",
        domain="[('model_id.model', '=', model_name)]",
        tracking=True,
        help="Plantilla de correo a usar cuando se ejecuta esta transición. "
             "La plantilla debe tener el mismo modelo como destino.",
    )
    email_recipients = fields.Selection(
        [("applicant", "Solicitante"),
         ("responsible", "Responsable"),
         ("applicant_and_responsible", "Solicitante y Responsable"),
         ("custom", "Personalizado")],
        string="Destinatarios del Correo",
        default="applicant",
        help="Quién recibe el correo automático:\n"
             "- Solicitante: El campo user_id del registro\n"
             "- Responsable: El campo user_on_charge\n"
             "- Ambos: Ambos campos\n"
             "- Personalizado: Se define en la plantilla",
    )
    attach_documents = fields.Boolean(
        string="Adjuntar Documentos",
        default=False,
        tracking=True,
        help="Si True, los documentos adjuntos del registro (attachment_ids) "
             "se incluyen como adjuntos del correo.",
    )
    email_subject_prefix = fields.Char(
        string="Prefijo del Asunto",
        help="Prefijo para el asunto del correo (ej. '[Aprobado]'). "
             "Se usa si no hay plantilla configurada.",
    )

    # ─── Configuración de Temporizador ──────────────────────────

    timer_rule_ids = fields.One2many(
        "certprodoo.base.state.timer",
        "transition_id",
        string="Reglas de Temporizador",
        help="Reglas de auto-transición por tiempo asociadas a esta transición.",
    )

    _sql_constraints = [
        (
            "transition_uniq",
            "unique (model_name, from_code, to_code)",
            "La transición ya existe para este modelo!",
        ),
    ]

    @api.depends("from_code", "to_code")
    def _compute_label(self):
        for record in self:
            record.label = f"{record.from_code} → {record.to_code}"

    # ─── Métodos de Ejecución ──────────────────────────────────

    def execute_transition(self, record, observation=None):
        """Ejecuta una transición completa sobre un registro.

        Orquesta:
        1. Validar que la transición es permitida
        2. Registrar en el historial
        3. Cambiar el estado del registro
        4. Enviar correo automático (si auto_email)
        5. Ejecutar método de acción (si action_method)
        6. Iniciar timers (si existen)

        Args:
            record: Registro sobre el que ejecutar la transición.
            observation: Observación del usuario (requerida si require_observation).

        Returns:
            bool: True si la transición se ejecutó correctamente.
        """
        self.ensure_one()

        # Validar observación requerida
        if self.require_observation and not observation:
            raise ValidationError(
                _("Esta transición requiere una observación. "
                  "Por favor ingrese una observación antes de continuar.")
            )

        # Validar permisos del grupo
        if self.group_id and not self.env.user.has_group(self.group_id.xml_id):
            raise ValidationError(
                _("No tiene permisos para ejecutar esta transición. "
                  "Se requiere el grupo: %s") % self.group_id.name
            )

        old_state = record.state
        new_state = self.to_code

        # Obtener etiquetas de estados para el historial
        state_labels = dict(record._fields['state'].selection) if 'state' in record._fields else {}
        old_label = state_labels.get(old_state, old_state)
        new_label = state_labels.get(new_state, new_state)

        # Cambiar el estado
        record.write({'state': new_state})

        # Registrar en el historial
        record._log_state_change(
            old_state, new_state,
            observation=observation,
            transition_id=self.id,
            old_label=old_label,
            new_label=new_label,
        )

        # Enviar correo automático
        email_sent = False
        if self.auto_email:
            email_sent = self._send_transition_email(record, observation)

        # Ejecutar método de acción
        if self.action_method and hasattr(record, self.action_method):
            getattr(record, self.action_method)()

        return True

    def _send_transition_email(self, record, observation=None):
        """Envía el correo automático asociado a esta transición.

        Args:
            record: Registro origen del correo.
            observation: Observación del cambio de estado.

        Returns:
            bool: True si el correo se envió correctamente.
        """
        self.ensure_one()

        if self.email_template_id:
            # Usar la plantilla configurada
            try:
                email_values = self._get_email_values(record)
                self.email_template_id.send_mail(
                    record.id,
                    force_send=True,
                    email_values=email_values if email_values else None,
                )
                _logger.info(
                    "Correo automático enviado para transición %s del registro %s#%d",
                    self.label, record._name, record.id,
                )
                return True
            except Exception as e:
                _logger.error(
                    "Error enviando correo automático para transición %s: %s",
                    self.label, e,
                )
                return False
        else:
            # Sin plantilla: enviar correo básico
            return self._send_basic_transition_email(record, observation)

    def _get_email_values(self, record):
        """Construye los valores adicionales para el correo según destinatarios.

        Args:
            record: Registro del que obtener los destinatarios.

        Returns:
            dict: Valores para email_values del send_mail.
        """
        recipients = []

        if self.email_recipients == "applicant" and hasattr(record, 'user_id') and record.user_id.email:
            recipients.append(record.user_id.email)
        elif self.email_recipients == "responsible" and hasattr(record, 'user_on_charge') and record.user_on_charge.email:
            recipients.append(record.user_on_charge.email)
        elif self.email_recipients == "applicant_and_responsible":
            if hasattr(record, 'user_id') and record.user_id.email:
                recipients.append(record.user_id.email)
            if hasattr(record, 'user_on_charge') and record.user_on_charge.email:
                recipients.append(record.user_on_charge.email)

        values = {}
        if recipients:
            values['email_to'] = ','.join(recipients)

        # Adjuntar documentos si está configurado
        if self.attach_documents and hasattr(record, 'attachment_ids') and record.attachment_ids:
            values['attachment_ids'] = [(4, att.id) for att in record.attachment_ids]

        return values

    def _send_basic_transition_email(self, record, observation=None):
        """Envía un correo básico cuando no hay plantilla configurada.

        Genera un correo simple con la información del cambio de estado.

        Args:
            record: Registro origen.
            observation: Observación del cambio.

        Returns:
            bool: True si se envió correctamente.
        """
        from ..utils.email_helpers import get_default_email_from

        state_labels = dict(record._fields['state'].selection) if 'state' in record._fields else {}
        old_label = state_labels.get(self.from_code, self.from_code)
        new_label = state_labels.get(self.to_code, self.to_code)

        subject = f"{self.email_subject_prefix or ''} {record.name or ''} - {old_label} → {new_label}"
        body = f"""
        <p>El registro <strong>{record.display_name}</strong> ha cambiado de estado:</p>
        <ul>
            <li>Estado anterior: <strong>{old_label}</strong></li>
            <li>Estado nuevo: <strong>{new_label}</strong></li>
            <li>Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
        </ul>
        """
        if observation:
            body += f"<p><strong>Observación:</strong> {observation}</p>"

        email_values = self._get_email_values(record)
        email_values.update({
            'email_from': get_default_email_from(self.env),
            'subject': subject.strip(),
        })

        try:
            mail = self.env['mail.mail'].sudo().create({
                'subject': subject.strip(),
                'body_html': body,
                'email_from': email_values.get('email_from'),
                'email_to': email_values.get('email_to', ''),
                'model': record._name,
                'res_id': record.id,
            })
            if self.attach_documents and hasattr(record, 'attachment_ids') and record.attachment_ids:
                mail.write({
                    'attachment_ids': [(4, att.id) for att in record.attachment_ids],
                })
            mail.send()
            return True
        except Exception as e:
            _logger.error("Error enviando correo básico de transición: %s", e)
            return False

    # ─── Métodos de Consulta ───────────────────────────────────

    @api.model
    def get_transitions_for_model(self, model_name, from_state=None):
        """Retorna las transiciones disponibles para un modelo.

        Args:
            model_name: Nombre técnico del modelo.
            from_state: Si se especifica, filtra por estado origen.

        Returns:
            recordset: Transiciones encontradas.
        """
        domain = [("model_name", "=", model_name), ("active", "=", True)]
        if from_state:
            domain.append(("from_code", "=", from_state))
        return self.search(domain, order="from_code, to_code")
