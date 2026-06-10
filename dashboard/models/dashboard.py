# -*- coding: utf-8 -*-
"""
Cuadro de Mando para el Sistema de Registro Profesional (certprodoo).
Odoo 14 - Modulo dashboard.

Proporciona KPIs y graficos para la gestion del registro profesional:
- Solicitudes por estado, tendencia mensual, top profesiones
- Tasas de aprobacion/rechazo por tipo de tramite
- Reclamaciones, expedientes, inscripciones
- Tiempo promedio de procesamiento
- Filtrado por rol y empresa
"""
from calendar import monthrange
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class Dashboard(models.Model):
    _name = 'dashboard'
    _description = 'Cuadro de Mando - Registro Profesional'
    _rec_name = 'name'

    name = fields.Char('Cuadro de Mando', default='Cuadro de Mando')

    # ================================================================
    # METODOS AUXILIARES
    # ================================================================

    def _get_base_domain(self, model_name=None):
        """Dominio base segun permisos del usuario y empresa.

        - Superadmin / Editor+Gestor / Consultor: ven datos de su empresa
        - Registrador: solo sus propios registros (user_id = self)
        - Cliente / Cliente Online: solo sus registros (id_user_register = self)
        """
        user = self.env.user
        domain = [('company_id', 'in', user.company_ids.ids)]

        if user.has_group("security.group_professional_register_employee"):
            if not user.has_group("security.group_professional_managment") and \
               not user.has_group("security.group_professional_editor") and \
               not user.has_group("security.group_professional_superadmin"):
                domain.append(('user_id', '=', user.id))

        return domain

    def _get_period_domain(self, period='year'):
        """Dominio de filtro por periodo de tiempo."""
        today = fields.Date.today()
        if period == 'month':
            start = today - relativedelta(days=30)
        elif period == 'quarter':
            start = today - relativedelta(months=3)
        elif period == 'year':
            start = today - relativedelta(years=1)
        else:
            # 'all' - sin filtro de fecha
            return []
        return [('create_date', '>=', fields.Date.to_string(start))]

    def _get_state_colors(self):
        """Mapa de colores por nombre de estado con fallback."""
        return {
            "Borrador": "#FFFACD",
            "En Proceso": "#87CEEB",
            "En Validacion": "#90EE90",
            "En Validaci\u00f3n": "#90EE90",
            "Detenida": "#FFA500",
            "Subsanada": "#40E0D0",
            "Aprobada": "#228B22",
            "Cancelada": "#808080",
            "Denegada": "#DC3545",
        }

    def _get_model_states(self, model_technical_name):
        """Obtiene los estados configurados para un modelo dado."""
        ir_model = self.env['ir.model'].search([
            ('model', '=', model_technical_name)
        ], limit=1)
        if not ir_model:
            return self.env['security.state_configuration']
        return self.env['security.state_configuration'].search([
            ('model', '=', ir_model.id)
        ], order='priority')

    def _compute_avg_processing_time(self, domain):
        """Calcula el tiempo promedio de procesamiento en dias usando SQL."""
        company_ids = self.env.user.company_ids.ids
        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (write_date - create_date)) / 86400.0) as avg_days
            FROM professional_registers_professional_request
            WHERE company_id IN %s
        """
        params = [tuple(company_ids)]

        # Filtro de periodo si existe
        date_domain = self._get_period_domain(
            domain and next((d[2] for d in domain if d[0] == 'period'), 'year')
            if domain else 'year'
        )

        # Filtro de estados finales (aprobada, detenida, cancelada, denegada)
        final_states = self.env['security.state_configuration'].search([
            ('model.model', '=', 'professional_registers.professional_request'),
            ('priority', 'in', [4, 6, 7, 8])
        ])
        if final_states:
            query += " AND states IN %s"
            params.append(tuple(final_states.ids))

        self.env.cr.execute(query, params)
        result = self.env.cr.fetchone()
        return result[0] if result and result[0] else 0.0

    # ================================================================
    # KPI CARDS
    # ================================================================

    @api.model
    def get_kpi_cards(self, period='year'):
        """Retorna datos para las tarjetas KPI principales."""
        request_model = self.env['professional_registers.professional_request']
        base_domain = self._get_base_domain()
        period_domain = self._get_period_domain(period)
        request_domain = base_domain + period_domain

        # Total solicitudes en periodo
        total_requests = request_model.search_count(request_domain)

        # Solicitudes aprobadas
        approved_states = self._get_model_states(
            'professional_registers.professional_request'
        ).filtered(lambda s: s.priority == 6)
        approved_domain = list(request_domain)
        if approved_states:
            approved_domain.append(('states', '=', approved_states[0].id))
        approved_count = request_model.search_count(approved_domain)

        # Inscripciones activas
        active_inscriptions = self.env['professional_registers.inscription'].search_count([
            ('company_id', 'in', self.env.user.company_ids.ids),
            ('retired', '=', False),
        ])

        # Expedientes abiertos
        open_expedients = self.env['professional_registers.expedient'].search_count([
            ('company_id', 'in', self.env.user.company_ids.ids),
            ('state', 'in', ['open', 'pending']),
        ])

        # Reclamaciones activas
        active_claims = self.env['professional_registers.claim_request'].search_count([
            ('company_id', 'in', self.env.user.company_ids.ids),
            ('claim_status', 'in', ['in_process', 'evaluating']),
        ])

        # Tiempo promedio de procesamiento (dias)
        avg_days = self._get_avg_processing_days(request_domain)

        # Solicitudes pendientes (en proceso + en validacion)
        pending_states = self._get_model_states(
            'professional_registers.professional_request'
        ).filtered(lambda s: s.priority in [2, 3])
        pending_domain = list(request_domain)
        if pending_states:
            pending_domain.append(('states', 'in', pending_states.ids))
        pending_count = request_model.search_count(pending_domain)

        return {
            'total_requests': total_requests,
            'approved_requests': approved_count,
            'pending_requests': pending_count,
            'active_inscriptions': active_inscriptions,
            'open_expedients': open_expedients,
            'active_claims': active_claims,
            'avg_processing_days': round(avg_days, 1),
        }

    def _get_avg_processing_days(self, domain):
        """Calcula el tiempo promedio de procesamiento en dias via SQL."""
        company_ids = self.env.user.company_ids.ids
        if not company_ids:
            return 0.0

        # Obtener IDs de estados finales
        final_states = self._get_model_states(
            'professional_registers.professional_request'
        ).filtered(lambda s: s.priority in [4, 6, 7, 8])

        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (write_date - create_date)) / 86400.0)
            FROM professional_registers_professional_request
            WHERE company_id IN %s
        """
        params = [tuple(company_ids)]

        if final_states:
            query += " AND states IN %s"
            params.append(tuple(final_states.ids))

        # Aplicar filtro de periodo del domain
        for d in domain:
            if d[0] == 'create_date' and d[1] == '>=':
                query += " AND create_date >= %s"
                params.append(d[2])

        self.env.cr.execute(query, params)
        result = self.env.cr.fetchone()
        return result[0] if result and result[0] else 0.0

    # ================================================================
    # GRAFICOS
    # ================================================================

    @api.model
    def get_solicitudes_por_estado(self, period='year'):
        """Distribucion de solicitudes por estado."""
        base_domain = self._get_base_domain()
        period_domain = self._get_period_domain(period)
        domain = base_domain + period_domain

        states = self._get_model_states('professional_registers.professional_request')
        colors = self._get_state_colors()
        result = []

        for state in states:
            state_domain = list(domain)
            state_domain.append(('states', '=', state.id))
            count = self.env['professional_registers.professional_request'].search_count(state_domain)
            result.append({
                'state_id': state.id,
                'state_name': state.name,
                'priority': state.priority,
                'color': colors.get(state.name, '#6c757d'),
                'cantidad': count,
            })

        return result

    @api.model
    def get_tendencia_mensual(self, months=12):
        """Tendencia mensual de solicitudes creadas y aprobadas."""
        base_domain = self._get_base_domain()
        result = {
            'labels': [],
            'created': [],
            'approved': [],
        }

        # Obtener estado "Aprobada"
        approved_states = self._get_model_states(
            'professional_registers.professional_request'
        ).filtered(lambda s: s.priority == 6)

        today = fields.Date.today()
        for i in range(months - 1, -1, -1):
            target = today - relativedelta(months=i)
            year = target.year
            month = target.month
            primer_dia = datetime(year, month, 1)
            ultimo_dia = datetime(year, month, monthrange(year, month)[1])

            # Formatear etiqueta del mes
            meses = [
                '', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
            ]
            label = "%s %s" % (meses[month], str(year)[2:])
            result['labels'].append(label)

            # Solicitudes creadas en el mes
            created_domain = list(base_domain) + [
                ('create_date', '>=', fields.Date.to_string(primer_dia)),
                ('create_date', '<=', fields.Date.to_string(ultimo_dia)),
            ]
            created_count = self.env['professional_registers.professional_request'].search_count(
                created_domain
            )
            result['created'].append(created_count)

            # Solicitudes aprobadas en el mes
            approved_domain = list(base_domain) + [
                ('write_date', '>=', fields.Date.to_string(primer_dia)),
                ('write_date', '<=', fields.Date.to_string(ultimo_dia)),
            ]
            if approved_states:
                approved_domain.append(('states', '=', approved_states[0].id))
            approved_count = self.env['professional_registers.professional_request'].search_count(
                approved_domain
            )
            result['approved'].append(approved_count)

        return result

    @api.model
    def get_top_profesiones(self, period='year', limit=10):
        """Top de profesiones por cantidad de solicitudes."""
        base_domain = self._get_base_domain()
        period_domain = self._get_period_domain(period)
        domain = base_domain + period_domain

        distribucion = self.env['professional_registers.professional_request'].read_group(
            domain,
            ['profession'],
            ['profession'],
            orderby='profession_count desc',
            limit=limit,
        )

        profesiones = []
        cantidades = []
        for d in distribucion:
            if d['profession']:
                profesiones.append(d['profession'][1] if isinstance(d['profession'], (list, tuple)) else str(d['profession']))
                cantidades.append(d['profession_count'])

        return {
            'profesiones': profesiones,
            'cantidades': cantidades,
        }

    @api.model
    def get_por_tipo_tramite(self, period='year'):
        """Distribucion de solicitudes por tipo de tramite."""
        base_domain = self._get_base_domain()
        period_domain = self._get_period_domain(period)
        domain = base_domain + period_domain

        result = []
        procedure_types = self.env['nomenclators.procedure_types'].search([
            ('active', '=', True),
        ])
        colores = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']

        for idx, pt in enumerate(procedure_types):
            pt_domain = list(domain)
            pt_domain.append(('procedure_type', '=', pt.id))
            count = self.env['professional_registers.professional_request'].search_count(pt_domain)
            result.append({
                'name': pt.name,
                'count': count,
                'color': colores[idx % len(colores)],
            })

        return result

    @api.model
    def get_reclamaciones_estado(self):
        """Distribucion de reclamaciones por estado."""
        base_domain = self._get_base_domain()
        claim_model = self.env['professional_registers.claim_request']

        claim_status_labels = {
            'draft': 'Borrador',
            'in_process': 'En Proceso',
            'evaluating': 'En Evaluacion',
            'approved': 'Con Lugar',
            'cancelled': 'Con Lugar en Parte',
            'rejected': 'Sin Lugar',
        }
        claim_status_colors = {
            'draft': '#FFFACD',
            'in_process': '#87CEEB',
            'evaluating': '#90EE90',
            'approved': '#228B22',
            'cancelled': '#FFA500',
            'rejected': '#DC3545',
        }

        result = []
        for status_key, status_label in claim_status_labels.items():
            domain = list(base_domain)
            domain.append(('claim_status', '=', status_key))
            count = claim_model.search_count(domain)
            result.append({
                'key': status_key,
                'name': status_label,
                'color': claim_status_colors.get(status_key, '#6c757d'),
                'cantidad': count,
            })

        return result

    @api.model
    def get_tasa_aprobacion_rechazo(self, period='year'):
        """Tasa de aprobacion y rechazo por tipo de tramite."""
        base_domain = self._get_base_domain()
        period_domain = self._get_period_domain(period)

        # Obtener estados
        all_states = self._get_model_states('professional_registers.professional_request')
        approved_state = all_states.filtered(lambda s: s.priority == 6)
        denied_state = all_states.filtered(lambda s: s.priority == 8)
        cancelled_state = all_states.filtered(lambda s: s.priority == 7)
        stopped_state = all_states.filtered(lambda s: s.priority == 4)

        procedure_types = self.env['nomenclators.procedure_types'].search([
            ('active', '=', True),
        ])

        result = {
            'labels': [],
            'aprobadas': [],
            'rechazadas': [],
            'otras': [],
            'total': 0,
            'tasa_aprobacion_global': 0.0,
            'tasa_rechazo_global': 0.0,
        }

        total_all = 0
        total_approved = 0
        total_denied = 0

        for pt in procedure_types:
            domain = base_domain + period_domain + [('procedure_type', '=', pt.id)]
            total = self.env['professional_registers.professional_request'].search_count(domain)

            approved_count = 0
            denied_count = 0
            if approved_state:
                approved_count = self.env['professional_registers.professional_request'].search_count(
                    domain + [('states', '=', approved_state[0].id)]
                )
            other_count = total - approved_count
            if denied_state:
                denied_count = self.env['professional_registers.professional_request'].search_count(
                    domain + [('states', '=', denied_state[0].id)]
                )
                other_count -= denied_count
            if cancelled_state:
                cancelled_count = self.env['professional_registers.professional_request'].search_count(
                    domain + [('states', '=', cancelled_state[0].id)]
                )
                other_count -= cancelled_count

            result['labels'].append(pt.name)
            result['aprobadas'].append(approved_count)
            result['rechazadas'].append(denied_count)
            result['otras'].append(max(0, other_count))

            total_all += total
            total_approved += approved_count
            total_denied += denied_count

        result['total'] = total_all
        result['tasa_aprobacion_global'] = round(
            (total_approved / total_all * 100) if total_all else 0, 1
        )
        result['tasa_rechazo_global'] = round(
            (total_denied / total_all * 100) if total_all else 0, 1
        )

        return result

    @api.model
    def get_expedientes_stats(self):
        """Estadisticas de expedientes por estado."""
        base_domain = [('company_id', 'in', self.env.user.company_ids.ids)]
        expedient_model = self.env['professional_registers.expedient']

        state_labels = {
            'draft': 'Borrador',
            'open': 'Abierto',
            'pending': 'Pendiente',
            'closed': 'Cerrado',
            'archived': 'Archivado',
        }
        state_colors = {
            'draft': '#FFFACD',
            'open': '#87CEEB',
            'pending': '#FFA500',
            'closed': '#228B22',
            'archived': '#808080',
        }

        result = []
        for state_key, state_label in state_labels.items():
            domain = list(base_domain) + [('state', '=', state_key)]
            count = expedient_model.search_count(domain)
            result.append({
                'key': state_key,
                'name': state_label,
                'color': state_colors.get(state_key, '#6c757d'),
                'cantidad': count,
            })

        return result

    # ================================================================
    # AGREGACION PRINCIPAL
    # ================================================================

    @api.model
    def get_full_data(self, values=None):
        """Retorna todos los datos del dashboard en una sola llamada."""
        period = 'year'
        if values and isinstance(values, dict):
            period = values.get('period', 'year')

        return {
            'kpi_cards': self.get_kpi_cards(period),
            'solicitudes_estado': self.get_solicitudes_por_estado(period),
            'tendencia_mensual': self.get_tendencia_mensual(),
            'top_profesiones': self.get_top_profesiones(period),
            'por_tipo_tramite': self.get_por_tipo_tramite(period),
            'reclamaciones_estado': self.get_reclamaciones_estado(),
            'tasas': self.get_tasa_aprobacion_rechazo(period),
            'expedientes_stats': self.get_expedientes_stats(),
            'period': period,
        }


class DashboardClient(models.Model):
    """Dashboard para clientes - Terminos y condiciones."""
    _name = 'dashboard.client'
    _description = 'Terminos y Condiciones - Portal Cliente'
    _rec_name = 'name'

    name = fields.Char()
    content = fields.Html()

    @api.model
    def get_full_data(self, values=None):
        """Retorna terminos y condiciones para el portal del cliente."""
        terms = self.env['nomenclators.terms_conditions'].search([
            ('active', '=', True),
        ])
        return [{'name': term.name, 'content': term.content} for term in terms]
