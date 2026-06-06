odoo.define('professional_registers.stopped_requests_notification', function (require) {
    "use strict";

    var session = require('web.session');
    var core = require('web.core');
    var Notification = require('web.Notification');
    var _t = core._t;

    function checkStoppedRequests() {
        // Verificar solicitudes detenidas
        session.rpc('/web/session/check_stopped_requests', {}).then(function(alerts) {
            if (alerts && alerts.length > 0) {
                // Agrupar alertas por nivel
                var criticals = alerts.filter(a => a.alert_level === 'critical');
                var warnings = alerts.filter(a => a.alert_level === 'warning');

                // Mostrar notificación para críticas
                if (criticals.length > 0) {
                    showNotification(
                        _t("⚠️ ALERTAS CRÍTICAS DE SOLICITUDES"),
                        formatAlerts(criticals),
                        'danger'
                    );
                }

                // Mostrar notificación para advertencias
                if (warnings.length > 0) {
                    showNotification(
                        _t("⚠️ ADVERTENCIAS DE SOLICITUDES"),
                        formatAlerts(warnings),
                        'warning'
                    );
                }
            }
        });
    }

    function formatAlerts(alerts) {
        var message = '';
        alerts.forEach(function(alert, index) {
            message += `<div style="margin-bottom: 15px; border-left: 3px solid ${alert.alert_level === 'critical' ? '#dc3545' : '#ffc107'}; padding-left: 10px;">
                <strong>${alert.request_name}</strong><br>
                ${alert.message}<br>
                <small>Fecha de detención: ${alert.stop_date}</small>
            </div>`;

            if (index < alerts.length - 1) {
                message += '<hr style="margin: 10px 0;">';
            }
        });

        message += `<div style="margin-top: 15px; font-size: 0.9em; font-style: italic;">
            ${_t("Actualiza los requisitos pendientes para evitar la denegación")}
        </div>`;

        return message;
    }

    function showNotification(title, message, type) {
        var notification = new Notification(null, {
            title: title,
            message: message,
            type: type,
            sticky: true,
            buttons: [
                {text: _t("Ver Solicitudes"), onClick: function() {
                    // Aquí puedes añadir lógica para redirigir a las solicitudes
                    this.destroy();
                }.bind(notification)},
                {text: _t("Cerrar"), onClick: function() {
                    this.destroy();
                }.bind(notification)}
            ]
        });

        notification.appendTo($('.o_notification_manager'));
    }

    // Ejecutar cuando el cliente web esté listo
    core.bus.on('web_client_ready', null, function() {
        // Esperar 5 segundos después del login para mostrar las alertas
        checkStoppedRequests()
    });
});