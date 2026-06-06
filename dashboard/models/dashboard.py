# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class Dashboard(models.Model):
    _name = 'dashboard'
    _description = 'Estadísticas'

    name = fields.Char('Estadísticas')

    # Métodos auxiliares
    def _get_base_domain(self):
        """Método auxiliar para obtener el dominio base según permisos de usuario"""
        user = self.env.user
        domain = [('company_id', 'in', user.company_ids.ids)]

        if user.has_group("security.group_professional_register_employee"):
            domain.append(('user_id', '=', user.id))

        return domain

    # Métodos para Solicitudes
    @api.model
    def get_count_professional_request(self, values=None):
        domain = self._get_base_domain()
        professional_request = self.env['professional_registers.professional_request'].search(domain)
        return len(professional_request)

    @api.model
    def get_solicitudes_por_estado(self):
        model = self.env['ir.model'].search([('model', '=', "professional_registers.professional_request")])
        state_model = self.env['security.state_configuration'].search([('model', '=', model.id)])
        result = []

        colores_por_estado = {
            "Borrador": "#FFFACD",  # Amarillo Suave
            "En Proceso": "#87CEEB",  # Azul Claro
            "En Validación": "#90EE90",  # Verde Claro
            "Detenida": "#FFA500",  # Naranja Oscuro
            "Subsanada": "#40E0D0",  # Celeste
            "Aprobada": "#228B22",  # Verde Oscuro
            "Cancelada": "#808080",  # Gris
            "Denegada": "#FF0000"  # Rojo
        }

        for state in state_model:
            count = self.env['professional_registers.professional_request'].search_count([
                ('states', '=', state.id)
            ])
            result.append({
                'state_id': state.id,
                'state_name': state.name,
                'color': colores_por_estado[f'{state.name}'],  # Usa color si lo tienes, o un valor por defecto
                'cantidad': count
            })

        return result

    @api.model
    def get_solicitudes_por_estado_mes(self, año=None, mes=None):
        if not año:
            año = fields.Date.today().year
        if not mes:
            mes = fields.Date.today().month

        primer_dia = fields.Date.to_string(datetime(año, mes, 1))
        ultimo_dia = fields.Date.to_string(datetime(año, mes, monthrange(año, mes)[1]))

        domain = self._get_base_domain()
        domain.extend([
            ('create_date', '>=', primer_dia),
            ('create_date', '<=', ultimo_dia)
        ])

        solicitudes = self.env['professional_registers.professional_request'].read_group(
            domain,
            ['states', 'create_date'],
            ['states']
        )

        return {
            'labels': [s['states'] for s in solicitudes],
            'data': [s['states_count'] for s in solicitudes]
        }

    @api.model
    def get_tiempo_promedio_procesamiento(self, ultimos_dias=365):
        fecha_inicio = fields.Date.to_string(datetime.now() - timedelta(days=ultimos_dias))
        domain = self._get_base_domain()
        domain.extend([
            ('create_date', '>=', fecha_inicio),
            ('states', 'in', [6, 4, 7, 8])
        ])

        solicitudes = self.env['professional_registers.professional_request'].search(domain)
        tiempos_proceso = []

        for solicitud in solicitudes:
            tiempo = fields.Datetime.from_string(solicitud.write_date) - \
                     fields.Datetime.from_string(solicitud.create_date)
            tiempos_proceso.append(tiempo.total_seconds() / 3600)

        return {
            'promedio_horas': sum(tiempos_proceso) / len(tiempos_proceso) if tiempos_proceso else 0,
            'total_solicitudes': len(tiempos_proceso)
        }

    @api.model
    def get_distribucion_profesiones(self):
        domain = self._get_base_domain()
        distribucion = self.env['professional_registers.professional_request'].read_group(
            domain,
            ['profession', 'profession_count:count(profession)'],
            ['profession'],
            orderby='profession desc',
            limit=10
        )

        return {
            'profesiones': [d['profession'][1] for d in distribucion if d['profession']],
            'cantidades': [d['profession_count'] for d in distribucion if d['profession']]
        }

    @api.model
    def get_tasa_aprobacion_rechazo(self, periodo='año'):
        if periodo == 'mes':
            fecha_inicio = fields.Date.to_string(datetime.now() - timedelta(days=30))
        elif periodo == 'año':
            fecha_inicio = fields.Date.to_string(datetime.now() - timedelta(days=365))
        else:
            fecha_inicio = fields.Date.to_string(datetime(2000, 1, 1))

        domain = self._get_base_domain()
        domain.append(('create_date', '>=', fecha_inicio))

        estados = self.env['professional_registers.professional_request'].read_group(
            domain,
            ['states', 'state_count:count(states)'],
            ['states']
        )

        total = sum(e['states_count'] for e in estados)
        return {
            'aprobadas': next((e['states_count'] for e in estados if e['states'] == 6), 0),
            'rechazadas': next((e['states_count'] for e in estados if e['states'] in [4, 7, 8]), 0),
            'total': total,
            'tasa_aprobacion': next((e['states_count'] / total * 100 for e in estados if e['states'] == 6),
                                    0) if total else 0,
            'tasa_rechazo': next((e['states_count'] / total * 100 for e in estados if e['states'] in [4, 7, 8]),
                                 0) if total else 0
        }

    # Métodos para Inscripciones
    @api.model
    def get_count_inscriptions(self, values=None):
        domain = self._get_base_domain()
        inscriptions = self.env['professional_registers.inscription'].search(domain)
        return len(inscriptions)

    @api.model
    def get_inscripciones_por_estado(self, estado=None):
        domain = self._get_base_domain()
        if estado:
            domain.append(('state', '=', estado))
        return self.env['professional_registers.inscription'].search_count(domain)

    # Métodos para Profesiones
    @api.model
    def get_professions(self):
        professions = self.env['nomenclators.professions'].search([])
        return [{'id': p.id, 'name': p.name} for p in professions]

    # Método para obtener todos los datos
    @api.model
    def get_full_data(self, values=None):
        return {
            'conteos': {
                'requests': self.get_count_professional_request(values) or 0,
                'inscriptions': self.get_count_inscriptions(values) or 0,
            },
            'solicitudes_estado': self.get_solicitudes_por_estado_mes() or {
                'labels': [],
                'data': []
            },
            'tiempo_promedio': self.get_tiempo_promedio_procesamiento() or {
                'promedio_horas': 0.0,
                'total_solicitudes': 0
            },
            'distribucion_profesiones': self.get_distribucion_profesiones() or {
                'profesiones': [],
                'cantidades': []
            },
            'tasas': self.get_tasa_aprobacion_rechazo() or {
                'tasa_aprobacion': 0,
                'tasa_rechazo': 0
            },
            'conteo_por_estado': self.get_solicitudes_por_estado() or {

                "Borrador": 0,  # Amarillo Suave
                "En Proceso": 0,  # Azul Claro
                "En Validación": 0,  # Verde Claro
                "Detenida": 0,  # Naranja Oscuro
                "Subsanada": 0,  # Celeste
                "Aprobada": 0,  # Verde Oscuro
                "Cancelada": 0,  # Gris
                "Denegada": 0  # Rojo

            },
        }


class DashboardClient(models.Model):
    _name = 'dashboard.client'
    _description = 'Términos y condiciones'

    @api.model
    def get_full_data(self, values=None):
        info = []
        terms = self.env['nomenclators.terms_conditions'].search([])
        for n in terms:
            info.append(n)
        return info


class DashboardClient(models.Model):
    _name = 'dashboard.client'
    _description = 'Términos y condiciones'

    name = fields.Char()
    content = fields.Html()

    @api.model
    def get_full_data(self, values=None):
        info = []
        terms = self.env['nomenclators.terms_conditions'].search([])
        result = [{'name': term.name, 'content': term.content} for term in terms]
        return result
