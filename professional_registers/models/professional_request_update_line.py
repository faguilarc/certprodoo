from odoo import models, fields, api
from odoo.tools import html_sanitize


class ProfessionalRequestUpdateLine(models.Model):
    _name = 'professional_registers.professional_request_update_line'
    _description = 'Línea de Actualización de Profesional'


    field_name = fields.Char(string='Campo', required=True)
    field_label = fields.Char(string='Etiqueta', )
    field_type = fields.Char(string='Tipo de Campo', required=True)
    old_value = fields.Char(string='Valor Actual', readonly=True)
    new_value = fields.Char(string='Nuevo Valor', required=True)

    # NUEVO: Campo para categorizar los campos
    category = fields.Selection([
        ('personal', 'Datos Personales'),
        ('contact', 'Datos de Contacto'),
        ('academic', 'Datos Académicos'),
        ('professional', 'Datos Profesionales'),
        ('work', 'Experiencia Laboral'),
        ('language', 'Idiomas'),
    ], string='Categoría', required=True)

    def _convert_value(self, value, field_type):
        """Convierte una cadena de texto al tipo de dato adecuado"""
        if not value:
            return False

        if field_type == 'char':
            return value
        elif field_type == 'text':
            return value
        elif field_type == 'integer':
            try:
                return int(value)
            except ValueError:
                return 0
        elif field_type == 'float':
            try:
                return float(value)
            except ValueError:
                return 0.0
        elif field_type == 'boolean':
            return value.lower() in ('true', '1', 'sí', 'si', 'yes')
        elif field_type == 'date':
            try:
                return fields.Date.to_string(fields.Date.from_string(value))
            except:
                return False
        elif field_type == 'many2one':
            # Para many2one, asumimos que el valor es el nombre del registro
            model_name = self.update_id._get_related_model()._name
            related_record = self.env[model_name].search([('name', '=', value)], limit=1)
            return related_record.id if related_record else False
        elif field_type == 'selection':
            return value  # Devolver el valor tal cual (debe ser un valor válido de la selección)
        else:
            return value