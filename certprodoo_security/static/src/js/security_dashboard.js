odoo.define('certprodoo_security.dashboard', function (require) {
    "use strict";

    /**
     * Dashboard de Seguridad - CertProdoo
     * 
     * Placeholder para el componente OWL del dashboard.
     * Muestra estadísticas básicas del módulo de seguridad.
     * 
     * TODO: Migrar completamente a OWL framework cuando
     * se implemente el dashboard completo con gráficos.
     */

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var SecurityDashboard = AbstractAction.extend({
        template: 'certprodoo_security.Dashboard',
        jsLibs: [],

        start: function () {
            var self = this;
            this._rpc({
                model: 'certprodoo.security.dashboard',
                method: 'get_full_data',
                args: [],
            }).then(function (data) {
                self.data = data;
                self.$('.total-users').text(data.total_users || 0);
                self.$('.active-users').text(data.active_users || 0);
                self.$('.companies').text(data.companies || 0);
                self.$('.roles').text(data.roles || 0);
                self.$('.options').text(data.options || 0);
            });
            return this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('certprodoo_security_dashboard', SecurityDashboard);

    return SecurityDashboard;
});
