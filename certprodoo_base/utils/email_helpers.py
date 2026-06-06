# -*- coding: utf-8 -*-
"""
Helpers de correo electrónico reutilizables.

Centraliza la lógica de envío de correos que antes estaba
distribuida entre professional_registers.send_email,
digital_signature (métodos _send_*_email) y notifications.
"""

import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def send_template_email(env, template_xml_id, record_id,
                        email_to=None, email_from=None,
                        force_send=True, raise_on_error=False):
    """Envía un correo usando una plantilla QWeb de Odoo.

    Unifica el patrón de envío de correo que se repite en
    digital_signature (3 métodos _send_*_email) y en otros módulos.

    Args:
        env: Odoo environment.
        template_xml_id: ID externo de la plantilla mail.template
            (ej. 'certprodoo_base.email_template_default').
        record_id: ID del registro que sirve de contexto a la plantilla.
        email_to: Dirección destino (sobrescribe la de la plantilla).
        email_from: Dirección remitente (sobrescribe la de la plantilla).
        force_send: Si True, envía inmediatamente en lugar de encolar.
        raise_on_error: Si True, lanza excepción si falla el envío.

    Returns:
        bool: True si el envío fue exitoso.
    """
    template = env.ref(template_xml_id, raise_if_not_found=False)
    if not template:
        msg = f"Plantilla de correo '{template_xml_id}' no encontrada."
        if raise_on_error:
            raise UserError(msg)
        _logger.warning(msg)
        return False

    email_values = {}
    if email_to:
        email_values["email_to"] = email_to
    if email_from:
        email_values["email_from"] = email_from

    try:
        template.send_mail(
            record_id,
            force_send=force_send,
            email_values=email_values if email_values else None,
        )
        return True
    except Exception as e:
        msg = f"Error enviando correo con plantilla '{template_xml_id}': {e}"
        _logger.error(msg)
        if raise_on_error:
            raise UserError(msg) from e
        return False


def get_default_email_from(env):
    """Obtiene la dirección de correo remitente por defecto del sistema.

    Prioriza el email del usuario actual, luego el de la compañía,
    y finalmente el parámetro del sistema.

    Args:
        env: Odoo environment.

    Returns:
        str: Dirección de correo remitente.
    """
    if env.user.email:
        return env.user.email
    if env.company.email:
        return env.company.email
    # Último recurso: parámetro del sistema
    config_email = env["ir.config_parameter"].sudo().get_param(
        "mail.catchall.email_from", ""
    )
    return config_email or "noreply@certprodoo.cu"
