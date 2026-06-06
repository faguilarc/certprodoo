odoo.define('security.MyCustomInscriptionsAction',  function (require) {
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t = core._t;
var  MyCustomInscriptionsAction = AbstractAction.extend({
        template: "DashboardInscriptionsDetails",
        cssLibs: [
        '/professional_registers/static/src/css/Chart.min.css'
        ],
        jsLibs: [
        '/professional_registers/static/src/js/chart.min.js',
        '/professional_registers/static/src/js/ui_datepicker_es.js',
        ],
        events: {
        'click .inscriptions':'inscription_function',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.date_range = 'week';  // possible values : 'week', 'month', year'
            this.date_from = moment().subtract(1, 'week');
            this.date_to = moment();
            this.dashboards_templates = ['DashboardInscriptionsDetails'];
            this.users_info=[];
        },
        willStart: function(){
            var self = this;
            this.login_employee = {};
            return this._super().then(function() {
                var def1 =  rpc.query({
                    model: 'professional_register.dashboard_inscriptions',
                    method: 'get_full_data',
                    args: [{ }],
                }, []).then(function(result){
                    self.users_info=result[0]
                });
                return $.when( def1);
            });
        },
        start: function () {
            // Actions to do
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
            });
        },
        render_dashboards: function() {
            var self = this;
//            $('#investigations_year').on('click', (e) => {
//                console.log("Invalid Delta:");
//            });
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_dashboard').append(QWeb.render(template, {widget: self,}));
            });
        },
        inscription_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Inscripciones"),
                type: 'ir.actions.act_window',
                res_model: 'professional_registers.inscription',
                view_mode: 'tree',
                views: [[false, 'list'],[false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
  // Functions according to the working of the widget.
});
  // Following code will attach the above widget to the defined client action
core.action_registry.add("professional_register_dashboard_inscriptions", MyCustomInscriptionsAction);
});