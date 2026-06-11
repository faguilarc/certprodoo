# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree

from odoo.exceptions import ValidationError


class Workhistory(models.Model):
    _name = 'professional_registers.work_history'
    _description = 'Trayectoria laboral'

    PHONE_MIN_LENGTH = 8
    PHONE_MAX_LENGTH = 15
    INTERNATIONAL_MIN_LENGTH = 7
    INTERNATIONAL_MAX_LENGTH = 15

    profesional_request = fields.Many2one('professional_registers.professional_request', string="Solicitud")
    profile = fields.Many2one('professional_registers.profile', string="Perfil")
    # Añadir el campo relacionado con la solicitud de actualización
    update_request = fields.Many2one('professional_registers.professional_request_update',
                                     string="Solicitud de Actualización")

    work_center = fields.Char('Centro de trabajo')
    organism = fields.Many2one('res.organism', string="Organismo")
    labour_sector = fields.Many2one('nomenclators.labour_sector', string="Tipo de entidad")
    activity = fields.Char('Actividad')
    phone = fields.Char('Teléfono')
    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')

    @api.constrains('phone')
    def _check_phone(self):
        for record in self:
            if record.phone:
                phone = record.phone.strip()

                # Verificar que no esté vacío
                if not phone:
                    raise ValidationError("El teléfono no puede estar vacío.")

                # Patrón que permite + al inicio y caracteres comunes de formato
                phone_pattern = r'^\+?[0-9\s\-\(\)]+$'

                if not re.match(phone_pattern, phone):
                    raise ValidationError(
                        "Formato de teléfono inválido. Use solo números, + al inicio (opcional), "
                        "y caracteres de separación como espacios, guiones o paréntesis."
                    )

                # Limpiar el número (eliminar +, espacios, guiones, paréntesis)
                clean_phone = re.sub(r'[^\+0-9]', '', phone)
                digits_only = clean_phone.replace('+', '')

                # Validar longitud
                if clean_phone.startswith('+'):
                    # Número internacional
                    if len(digits_only) < self.INTERNATIONAL_MIN_LENGTH or len(
                            digits_only) > self.INTERNATIONAL_MAX_LENGTH:
                        raise ValidationError(
                            f"Número internacional inválido. Debe tener entre "
                            f"{self.INTERNATIONAL_MIN_LENGTH} y {self.INTERNATIONAL_MAX_LENGTH} dígitos "
                            f"después del código de país."
                        )
                else:
                    # Número local
                    if len(digits_only) < self.PHONE_MIN_LENGTH or len(digits_only) > self.PHONE_MAX_LENGTH:
                        raise ValidationError(
                            f"Número local inválido. Debe tener entre {self.PHONE_MIN_LENGTH} "
                            f"y {self.PHONE_MAX_LENGTH} dígitos.")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("La fecha 'Hasta' no puede ser menor que la fecha 'Desde'")