odoo.define('dashboard.dashboard_client', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');
var _t = core._t;
var QWeb = core.qweb;
var web_client = require('web.web_client');

var DashboardClient = AbstractAction.extend({
    template: 'DashboardDetailsClient',
    cssLibs: [
        '/dashboard/static/src/css/Chart.min.css'
    ],
    jsLibs: [
        '/dashboard/static/src/js/chart.min.js',
        '/dashboard/static/src/js/ui_datepicker_es.js',
    ],
    events: {
//        'click .request':'request_function',
    },

    init: function(parent, context) {

        this._super(parent, context);
        this.date_range = 'week';  // possible values : 'week', 'month', year'
        this.date_from = moment().subtract(1, 'week');
        this.date_to = moment();
        this.dashboards_templates = ['DashboardDetailsClient'];
        this.users_info=[];
        // var self = this;
        // console.log("INIT FUNCTION 1")
        // if (context.tag == 'dashboard.dashboard'){
        //         self.render_dashboards();
        // }
    },

    willStart: function(){
        var self = this;
        this.login_employee = {};
        return this._super()
        .then(function() {
            var def1 =  rpc.query({
            model: 'dashboard.client',
            method: 'get_full_data',
            args: [{ }],
            }, []).then(function(result){
            console.log(result);
            self.users_info=result
            });
        return $.when( def1);
        });
    },

    start: function() {
        console.log("START FUNCTION")
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
        });
    },

    render_dashboards: function() {
        var self = this;
        _.each(this.dashboards_templates, function(template) {
            console.log('dad')
            self.$('.o_dashboard').append(QWeb.render(template, {widget: self,}));
        });
    },

    fetch_data: function() {
        var self = this;
        var def1 =  rpc.query({
            model: 'dashboard.client',
            method: 'get_full_data',
            args: [{ }],
            }, []).then(function(result){
            console.log(result);
            self.users_info=result
            });
        return $.when( def1);
    },

    on_reverse_breadcrumb: function() {console.log("ON_REVERSE_BREADCRUMB")
        var self = this;
        web_client.do_push_state({});
        this.update_cp();
        // self.render_dashboards();
        this.fetch_data().then(function() {
            self.$('.o_radius_dashboard').empty();
            self.render_dashboards();
        });
    },

    update_cp: function() {
        var self = this;
        console.log("UPDATE_CP")
    },

    get_emp_image_url: function(employee){
        return window.location.origin + '/web/image?model=hr.employee&field=image&id='+employee;
    },

//    request_function: function(ev){
//        var self = this;
//        ev.stopPropagation();
//        ev.preventDefault();
//        this.do_action({
//            name: _t(" Solicitudes"),
//            type: 'ir.actions.act_window',
//            res_model: 'professional_registers.professional_request',
//            view_mode: 'tree',
//            views: [[false, 'list'],[false, 'form']],
//            domain: [],
//            target: 'current' //self on some of them
//        }, {
//                on_reverse_breadcrumb: this.on_reverse_breadcrumb
//        });
//    },

});


core.action_registry.add('dashboard.dashboard_client', DashboardClient);

return Dashboard;

});