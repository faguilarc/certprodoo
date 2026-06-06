# models/project.py
from odoo import models, fields, api
import math


class Project(models.Model):
    _name = 'professional_registers.project'
    _description = 'Proyectos con Ubicación Geográfica'

    name = fields.Char('Nombre del Proyecto', required=True)
    description = fields.Text('Descripción')

    # Campos de dirección del proyecto
    street = fields.Char('Calle')
    street2 = fields.Char('Calle 2')
    city = fields.Char('Ciudad')
    state_id = fields.Many2one('res.country.state', string='Provincia')
    country_id = fields.Many2one('res.country', string='País')
    zip = fields.Char('Código Postal')

    # Coordenadas del proyecto - campos separados
    latitude = fields.Float(
        string='Latitud',
        digits=(16, 5),
        help="Latitud de la ubicación del proyecto"
    )
    longitude = fields.Float(
        string='Longitud',
        digits=(16, 5),
        help="Longitud de la ubicación del proyecto"
    )

    # Campo para mostrar si tiene coordenadas
    has_coordinates = fields.Boolean(
        string='Tiene Coordenadas',
        compute='_compute_has_coordinates',
        store=True
    )

    # Relación con profesionales asignados
    professional_ids = fields.Many2many(
        'professional_registers.profile',
        'project_professional_rel',
        'project_id',
        'professional_id',
        string='Profesionales Asignados'
    )

    @api.depends('latitude', 'longitude')
    def _compute_has_coordinates(self):
        for record in self:
            record.has_coordinates = bool(record.latitude and record.longitude)

    def action_set_location_from_map(self):
        """
        Abre un wizard para seleccionar la ubicación en un mapa
        """
        return {
            'name': 'Establecer Ubicación en Mapa',
            'type': 'ir.actions.act_window',
            'res_model': 'set.location.map.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_latitude': self.latitude,
                'default_longitude': self.longitude,
            }
        }

    def calculate_distance_to_professional(self, professional):
        """
        Calcula la distancia en kilómetros entre el proyecto y un profesional
        """
        if not (self.latitude and self.longitude and professional.latitude and professional.longitude):
            return None

        # Convertir a radianes
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(professional.latitude)
        lon2 = math.radians(professional.longitude)

        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Radio de la Tierra en kilómetros
        r = 6371.0

        return c * r