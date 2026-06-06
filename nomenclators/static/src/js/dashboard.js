odoo.define('security.MyCustomNomenclatorAction',  function (require) {
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t = core._t;
var  MyCustomNomenclatorAction = AbstractAction.extend({
        template: "DashboardNomenclatorDetails",
        cssLibs: [
        '/nomenclators/static/src/css/Chart.min.css'
        ],
        jsLibs: [
        '/nomenclators/static/src/js/chart.min.js',
        '/nomenclators/static/src/js/ui_datepicker_es.js',
        ],
        events: {
            'click .profession':'profesion_function',
            'click .specialties':'specialties_function',
            'click .study_center':'study_center_function',
            'click .teaching_categories':'teaching_categories_function',
            'click .documents_required':'documents_required_function',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.date_range = 'week';  // possible values : 'week', 'month', year'
            this.date_from = moment().subtract(1, 'week');
            this.date_to = moment();
            this.dashboards_templates = ['DashboardNomenclatorDetails'];
            this.users_info=[];
        },
        willStart: function(){
            var self = this;
            this.login_employee = {};
            return this._super().then(function() {
                var def1 =  rpc.query({
                    model: 'nomenclators.dashboard',
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
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_dashboard').append(QWeb.render(template, {widget: self,}));
            });
        },
        profesion_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Profesiones"),
                type: 'ir.actions.act_window',
                res_model: 'nomenclators.professions',
                view_mode: 'tree',
                views: [[false, 'list'],[false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
        specialties_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Especialidades"),
                type: 'ir.actions.act_window',
                res_model: 'nomenclators.specialties',
                view_mode: 'tree',
                views: [[false, 'list'],[false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
        study_center_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Centros de estudio"),
                type: 'ir.actions.act_window',
                res_model: 'nomenclators.study_centers',
                view_mode: 'tree',
                views: [[false, 'list'],[false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
        teaching_categories_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Categorías docentes"),
                type: 'ir.actions.act_window',
                res_model: 'nomenclators.teaching_categories',
                view_mode: 'tree',
                views: [[false, 'list'],[false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
        documents_required_function: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Documentos para trámites"),
                type: 'ir.actions.act_window',
                res_model: 'nomenclators.documents_required',
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
core.action_registry.add("nomenclators_dashboard", MyCustomNomenclatorAction);
});


//odoo.define('security.dashboard', function (require) {
//"use strict";
//
//var AbstractAction = require('web.AbstractAction');
//var core = require('web.core');
//var rpc = require('web.rpc');
//var _t = core._t;
//var QWeb = core.qweb;
//var web_client = require('web.web_client');
//
//var Dashboard = AbstractAction.extend({
//    template: 'DashboardSecurityDetails',
//    cssLibs: [
//        '/security/static/src/css/Chart.min.css'
//    ],
//    jsLibs: [
//        '/security/static/src/js/chart.min.js',
//        '/security/static/src/js/ui_datepicker_es.js',
//    ],
//    events: {
//        'click .client':'client_function',
//    },
//
//    init: function(parent, context) {
//
//        this._super(parent, context);
//        this.date_range = 'week';  // possible values : 'week', 'month', year'
//        this.date_from = moment().subtract(1, 'week');
//        this.date_to = moment();
//        this.dashboards_templates = ['DashboardSecurityDetails'];
//        this.users_info=[];
//    },
//
//    willStart: function(){
//        var self = this;
//        this.login_employee = {};
//        return this._super()
//        .then(function() {
//            var def1 =  rpc.query({
//            model: 'dashboard.security',
//            method: 'get_full_data',
//            args: [{ }],
//            }, []).then(function(result){
//            self.users_info=result[0]
//            });
//        return $.when( def1);
//        });
//    },
//
//    start: function() {
//        console.log("START FUNCTION")
//        var self = this;
//        this.set("title", 'Dashboard');
//        return this._super().then(function() {
//            self.render_dashboards();
//        });
//    },
//
//    render_dashboards: function() {
//        var self = this;
//        _.each(this.dashboards_templates, function(template) {
//            console.log('dad')
//            self.$('.o_dashboard').append(QWeb.render(template, {widget: self,}));
//        });
//    },
//
//    fetch_data: function() {
//        var self = this;
//        var def1 =  rpc.query({
//            model: 'dashboard.security',
//            method: 'get_full_data',
//            args: [{ }],
//            }, []).then(function(result){
//            console.log(result);
//            self.users_info=result[0]
//            });
//        return $.when( def1);
//    },
//
//    on_reverse_breadcrumb: function() {console.log("ON_REVERSE_BREADCRUMB")
//        var self = this;
//        web_client.do_push_state({});
//        this.update_cp();
//        this.fetch_data().then(function() {
//            self.$('.o_radius_dashboard').empty();
//            self.render_dashboards();
//        });
//    },
//
//    update_cp: function() {
//        var self = this;
//        console.log("UPDATE_CP")
//    },
//
//    get_emp_image_url: function(employee){
//        return window.location.origin + '/web/image?model=hr.employee&field=image&id='+employee;
//    },
//
//    client_function: function(ev){
//        var self = this;
//        ev.stopPropagation();
//        ev.preventDefault();
//        this.do_action({
//            name: _t(" Clientes"),
//            type: 'ir.actions.act_window',
//            res_model: 'res.partner',
//            view_mode: 'tree',
//            views: [[false, 'list'],[false, 'form']],
//            domain: [],
//            target: 'current' //self on some of them
//        }, {
//                on_reverse_breadcrumb: this.on_reverse_breadcrumb
//        });
//    },
//
//});
//
//
//core.action_registry.add('security.dashboard', Dashboard);
//
//return Dashboard;
//
//});