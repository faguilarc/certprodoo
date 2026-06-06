# wizards/find_professionals_by_location.py
from odoo import models, fields, api
import math


class FindProfessionalsByLocation(models.TransientModel):
    _name = 'find.professionals.by.location'
    _description = 'Buscar Profesionales por Ubicación'

    project_id = fields.Many2one(
        'professional_registers.project',
        string='Proyecto',
        required=True
    )

    max_distance = fields.Float(
        string='Distancia Máxima (km)',
        default=50.0,
        help="Distancia máxima en kilómetros para buscar profesionales"
    )

    profession_id = fields.Many2one(
        'nomenclators.professions',
        string='Profesión',
        help="Filtrar por profesión específica"
    )

    specialty_id = fields.Many2one(
        'nomenclators.specialties',
        string='Especialidad',
        help="Filtrar por especialidad específica"
    )

    state_id = fields.Many2one(
        'res.country.state',
        string='Provincia',
        help="Filtrar por provincia"
    )

    available_professionals = fields.Many2many(
        'professional_registers.profile',
        string='Profesionales Disponibles',
        compute='_compute_available_professionals'
    )

    @api.depends('project_id', 'max_distance', 'profession_id', 'specialty_id', 'state_id')
    def _compute_available_professionals(self):
        if not self.project_id or not self.project_id.location_point:
            self.available_professionals = [(5, 0, 0)]  # Limpiar la lista
            return

        # Dominio base para buscar profesionales
        domain = [('location_point', '!=', False)]

        # Aplicar filtros adicionales
        if self.profession_id:
            domain.append(('profession', '=', self.profession_id.id))

        if self.specialty_id:
            domain.append(('specialties', '=', self.specialty_id.id))

        if self.state_id:
            domain.append(('state_id', '=', self.state_id.id))

        # Buscar todos los profesionales que cumplen con los filtros
        all_professionals = self.env['professional_registers.profile'].search(domain)

        # Filtrar por distancia
        available_professionals = []

        for professional in all_professionals:
            distance = self.project_id.calculate_distance_to_professional(professional)

            if distance is not None and distance <= self.max_distance:
                # Agregar el profesional a la lista con su distancia
                professional.distance = distance
                available_professionals.append(professional.id)

        # Ordenar por distancia
        available_professionals.sort(key=lambda p: p.distance)

        # Asignar la lista ordenada
        self.available_professionals = [(6, 0, available_professionals)]

    def action_assign_professionals(self):
        """
        Asigna los profesionales seleccionados al proyecto
        """
        selected_professionals = self.available_professionals.filtered('selected')

        if not selected_professionals:
            return {'type': 'ir.actions.act_window_close'}

        # Asignar los profesionales al proyecto
        self.project_id.write({
            'professional_ids': [(4, p.id) for p in selected_professionals]
        })

        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Asignación Completada',
                'message': f'Se han asignado {len(selected_professionals)} profesionales al proyecto.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def render_map(self):
        """
        Renderiza el mapa con la ubicación del proyecto y los profesionales
        """
        # Obtener las coordenadas del proyecto
        project_data = {
            'project_latitude': self.project_id.project_latitude,
            'project_longitude': self.project_id.project_longitude,
            'name': self.project_id.name
        }

        # Obtener los datos de los profesionales
        professionals_data = []
        for professional in self.available_professionals:
            professionals_data.append({
                'name': professional.name,
                'partner_latitude': professional.partner_latitude,
                'partner_longitude': professional.partner_longitude,
                'distance': professional.distance,
                'profession': professional.profession.name if professional.profession else ''
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'geo_location_map',
            'project': project_data,
            'professionals': professionals_data,
        }