odoo.define('nomenclators.suspended_procedures', function (require) {
    "use strict";

    var session = require('web.session');
    var core = require('web.core');
    var Notification = require('web.Notification');

    function checkSuspendedProcedures() {
        session.rpc('/web/session/get_suspended_procedures', {}).then(function(result) {
            if (result) {
                var notification = new Notification(this, {
                    title: result.title,
                    message: result.message,
                    type: 'warning',
                    sticky: true,
                });
                notification.appendTo($('.o_notification_manager'));
            }
        });
    }

    console.log('wentro a la funcion /....')

    // Check when web client is ready
    core.bus.on('web_client_ready', null, function () {
        checkSuspendedProcedures();
    });
});