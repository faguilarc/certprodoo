# -*- coding: utf-8 -*-
from datetime import date, datetime

from odoo import http, exceptions, _, fields
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


# class Nomenclators(http.Controller):
#     @http.route('/nomenclators/nomenclators/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nomenclators/nomenclators/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nomenclators.listing', {
#             'root': '/nomenclators/nomenclators',
#             'objects': http.request.env['nomenclators.nomenclators'].search([]),
#         })

#     @http.route('/nomenclators/nomenclators/objects/<model("nomenclators.nomenclators"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nomenclators.object', {
#             'object': obj
#         })


class ProcedureController(http.Controller):

    @http.route('/web/session/get_suspended_procedures', type='json', auth="user")
    def get_suspended_procedures(self):
        procedures = request.env['nomenclators.procedure_types']._check_suspended_procedures()
        if procedures:
            message_parts = []
            is_admin = request.env.user.has_group('base.group_system')

            header = "🚨 ALERTA DEL SISTEMA 🚨\n" + ("-" * 50) + "\n\n"

            if is_admin:
                header += "Como Administrador, se requiere su atención inmediata:\n\n"
            else:
                header += "Información importante sobre procesos detenidos:\n\n"

            for proc in procedures:
                reasons = ', '.join(proc.stop_reasons.mapped('name'))
                if is_admin:
                    message_parts.append(
                        f"📋 Trámite: {proc.procedure_type_id.name}\n"
                        f"📊 Estado: {'Detenido' if proc.state == 'stopped' else proc.state}\n"
                        f"❌ Motivos: {reasons}\n"
                        f"🕒 Fecha de Detención: {proc.stop_date.strftime('%d/%m/%Y %H:%M')}\n"
                        f"👤 Detenido por: {proc.stopped_by.name}\n"

                        # f"🔍 ID del Proceso: {proc.id}\n"
                        f"{'-' * 30}\n"
                    )
                else:
                    message_parts.append(
                        f"📋 Trámite: {proc.procedure_type_id.name}\n"
                        f"❌ Motivos: {reasons}\n"
                        f"🕒 Detenido desde: {proc.stop_date.strftime('%d/%m/%Y')}\n"
                        f"{'-' * 30}\n"
                    )

            footer = "\n"
            if is_admin:
                footer += "⚠️ Se requiere revisión y acción inmediata de estos procesos."
            else:
                footer += "⚠️ Por favor, tenga en cuenta estas detenciones al realizar sus operaciones."

            complete_message = header + ''.join(message_parts) + footer
            raise ValidationError(_(complete_message))

        return False

    @http.route('/web/session/check_stopped_requests', type='json', auth="user")
    def check_stopped_requests(self):
        # 1. Buscar estado "detenido"
        stopped_state = request.env['security.state_configuration'].search(
            [('name', 'ilike', 'Detenida')],
            limit=1
        )

        if not stopped_state:
            return {"error": "Estado 'detenido' no encontrado"}

        # 2. Obtener el usuario actual
        current_user = request.env.user
        Request = request.env['professional_registers.professional_request']
        RequestHElp = request.env['professional_registers.request_help']
        Requesthist = request.env['professional_registers.professional_request_history']
        alerts = []

        # 3. Buscar solicitudes del usuario actual con último estado detenido
        user_requests = Request.search([('id_user_register', '=', current_user.id), ('states', '=', stopped_state.id)])

        for req in user_requests:
            # Obtener el último historial de estado
            last_history = RequestHElp.search([
                ('request_id', '=', req.id), ('state', '=', 'Detenida')
            ], )

            if not last_history or last_history.state != stopped_state.name:
                continue

            # Calcular días hábiles transcurridos
            stop_date = last_history.date
            today = fields.Datetime.now()
            if isinstance(stop_date, str):
                stop_date = fields.Datetime.from_string(stop_date)
            elif isinstance(stop_date, date) and not isinstance(stop_date, datetime):
                # Si es date pero no datetime, convertirlo
                stop_date = fields.Datetime.to_datetime(stop_date)
            elif stop_date is None:
                stop_date = today

            elapsed_days = self.calculate_working_days(stop_date, today)

            # Umbrales de alerta
            warning_threshold = 50  # 50% del plazo
            critical_threshold = 75  # 75% del plazo
            max_days = last_history.counter  # Total de días hábiles permitidos
            remaining_days = max(0, max_days - elapsed_days)

            # 4. Generar alertas según rangos
            if elapsed_days >= critical_threshold or elapsed_days >= warning_threshold:
                alert_level = "critical" if elapsed_days >= critical_threshold else "warning"

                alerts.append({
                    'request_id': req.id,
                    'request_name': req.request_number or f"Solicitud #{req.id}",
                    'elapsed_days': elapsed_days,
                    'remaining_days': remaining_days,
                    'stop_date': stop_date.strftime('%d/%m/%Y'),
                    'alert_level': alert_level,
                    'message': self.generate_alert_message(
                        alert_level,
                        elapsed_days,
                        remaining_days,
                        req.request_number or f"Solicitud #{req.id}",
                        stop_date.strftime('%d/%m/%Y')
                    ),
                })

            # Si hay alertas, mostrarlas como notificación
        if alerts:
            # Construir mensaje de notificación
            message_parts = []
            message_parts.append("🚨 ALERTA DE SOLICITUDES DETENIDAS 🚨")
            message_parts.append("=" * 50)

            for alert in alerts:
                message_parts.append(f"\n{alert['message']}")
                message_parts.append("-" * 30)

            complete_message = "\n".join(message_parts)
            raise ValidationError(_(complete_message))

        return False

    def generate_alert_message(self, level, elapsed_days, remaining_days, request_name, stop_date_str):
        if level == "critical":
            return (f"🚨 ¡ALERTA CRÍTICA!\n"
                    f"Solicitud: {request_name}\n"
                    f"📅 Detenida desde: {stop_date_str}\n"
                    f"⏰ Días detenida: {elapsed_days} días\n"
                    f"⚠️ Quedan solo {remaining_days} días hábiles para regularizar\n"
                    f"🛑 Si no actúa, será DENEGADA automáticamente")
        else:
            return (f"⚠️ ¡Advertencia!\n"
                    f"Solicitud: {request_name}\n"
                    f"📅 Detenida desde: {stop_date_str}\n"
                    f"⏰ Lleva {elapsed_days} días detenido\n"
                    f"✅ Quedan {remaining_days} días hábiles para completar requisitos")

    def calculate_working_days(self, start_date, end_date):
        """Calcula días hábiles entre dos fechas (excluye fines de semana)"""
        if isinstance(start_date, str):
            start_date = fields.Datetime.from_string(start_date)
        if isinstance(end_date, str):
            end_date = fields.Datetime.from_string(end_date)

        days_diff = (end_date - start_date).days
        if days_diff <= 0:
            return 0

        # Calcular días no laborables (sábados y domingos)
        full_weeks = days_diff // 7
        extra_days = days_diff % 7

        # Ajustar por días de fin de semana
        weekend_days = full_weeks * 2
        if extra_days:
            start_weekday = start_date.weekday()
            weekend_days += sum(
                1 for day in range(1, extra_days + 1)
                if (start_weekday + day) % 7 in (5, 6)  # 5=Sábado, 6=Domingo
            )

        return days_diff - weekend_days

    def send_alert_email(self, user, alerts):
        """Envía un correo electrónico de alerta al usuario"""
        if not alerts:
            return

        # Crear cuerpo del correo
        email_body = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
                <h2 style="color: #d9534f;">⚠️ Alertas de Solicitudes Detenidas</h2>
                <p>Estimado(a) {user_name},</p>
                <p>Tienes solicitudes detenidas que requieren tu atención inmediata:</p>
            """.format(user_name=user.name)

        for alert in alerts:
            email_body += """
                <div style="border: 1px solid #f0ad4e; border-radius: 5px; padding: 15px; margin-bottom: 20px; 
                             background-color: #fcf8e3;">
                    <h3 style="color: #d9534f; margin-top: 0;">Solicitud: {request_name}</h3>
                    <p><strong>Días transcurridos:</strong> {elapsed_days} días hábiles</p>
                    <p><strong>Días restantes:</strong> {remaining_days} días hábiles</p>
                    <p><strong>Fecha de detención:</strong> {stop_date}</p>
                    <p><strong>Observaciones:</strong><br>{observation}</p>
                    <p style="color: #d9534f; font-weight: bold;">
                        ¡Actualiza los requisitos pendientes para evitar la denegación!
                    </p>
                </div>
                """.format(**alert)

        email_body += """
                <p style="margin-top: 30px;">
                    Atentamente,<br>
                    El equipo de Sistema
                </p>
            </div>
            """

        # Enviar correo
        mail_template = request.env.ref('your_module.email_template_stopped_request_alert', False)

        if mail_template:
            # Usar plantilla existente si está configurada
            mail_template.send_mail(user.id, force_send=True)
        else:
            # Envío directo si no hay plantilla
            request.env['mail.mail'].create({
                'subject': f"Alerta de solicitudes detenidas - {fields.Date.today()}",
                'body_html': email_body,
                'email_to': user.email,
                'email_from': request.env.user.company_id.email,
            }).send()
