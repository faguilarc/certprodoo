# models/profile.py
from odoo import models, fields, api


class Profile(models.Model):
    _inherit = 'professional_registers.profile'

    # Campos de dirección estructurados
    street = fields.Char('Calle')
    street2 = fields.Char('Calle 2')
    city = fields.Char('Ciudad')
    state_id = fields.Many2one('res.country.state', string='Provincia')
    country_id = fields.Many2one('res.country', string='País')
    zip = fields.Char('Código Postal')

    # Coordenadas geográficas - campos separados
    latitude = fields.Float(
        string='Latitud',
        digits=(16, 5),
        help="Latitud de la ubicación del profesional"
    )
    longitude = fields.Float(
        string='Longitud',
        digits=(16, 5),
        help="Longitud de la ubicación del profesional"
    )

    # Campo para mostrar si tiene coordenadas
    has_coordinates = fields.Boolean(
        string='Tiene Coordenadas',
        compute='_compute_has_coordinates',
        store=True
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
                'default_profile_id': self.id,
                'default_latitude': self.latitude,
                'default_longitude': self.longitude,
            }
        }