odoo.define('dashboard.dashboard_client', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    var DashboardClient = AbstractAction.extend({
        template: 'DashboardDetailsClient',

        init: function (parent, context) {
            this._super(parent, context);
            this.terms_data = [];
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return rpc.query({
                    model: 'dashboard.client',
                    method: 'get_full_data',
                    args: [{}],
                }).then(function (result) {
                    self.terms_data = result || [];
                });
            });
        },

        start: function () {
            var self = this;
            this.set("title", 'Terminos y Condiciones');
            return this._super.apply(this, arguments).then(function () {
                self._renderContent();
            });
        },

        _renderContent: function () {
            var $container = this.$('.terms-container');
            if (!$container.length) return;

            $container.empty();
            this.terms_data.forEach(function (term) {
                var $section = $('<div class="terms-section mb-4"/>');
                $section.append($('<h5/>').text(term.name));
                $section.append($('<div/>').html(term.content));
                $container.append($section);
            });
        },
    });

    core.action_registry.add('dashboard.dashboard_client', DashboardClient);

    return DashboardClient;
});
