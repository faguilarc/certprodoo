odoo.define('dashboard.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
// var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var web_client = require('web.web_client');

    var Dashboard = AbstractAction.extend({
        template: 'DashboardDetails',
        cssLibs: [
            '/dashboard/static/src/css/Chart.min.css'
        ],
        jsLibs: [
            '/dashboard/static/src/js/chart.min.js',
            '/dashboard/static/src/js/ui_datepicker_es.js',
        ],
        events: {
            'click .request': 'request_function',
            'click .inscriptions': 'inscription_function',
            'click .status-card': 'openFilteredView',
            'change .report-toggles input[type="checkbox"]': 'toggleReport',
            'click .btn-group button': 'handlePeriodChange',
            'click #btnCardView': 'showCardView',
            'click #btnChartView': 'showChartView'
        },

        init: function (parent, context) {
            this._super(parent, context);
            this.date_range = 'month';
            this.loading_state = false;
            this.error_state = false;
            this.dashboards_templates = ['DashboardDetails'];
            this.visible_reports = {
                solicitudes_estado: true,
                distribucion_profesiones: false,
                tiempo_promedio: false,
                tasas: false
            };
        },

        openFilteredView: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            var estado = $(ev.currentTarget).data('estado');
            console.log($(ev.currentTarget).data)
            console.log(estado)
            this.do_action({
                name: _t("Solicitudes"),
                type: 'ir.actions.act_window',
                res_model: 'professional_registers.professional_request',
                view_mode: 'tree',
                views: [[false, 'list'], [false, 'form']],
                domain: [['states', '=', estado]],
                target: 'current'
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },

        toggleReport: function (ev) {
            var $checkbox = $(ev.currentTarget);
            var reportId = $checkbox.attr('id').replace('show', '');
            var $report = this.$('#report' + reportId);

            if ($checkbox.is(':checked')) {
                $report.slideDown();
                // Refresh chart if exists
                var chartId = 'chart' + reportId.replace('report', '');
                var chart = this.charts && this.charts[chartId];
                if (chart) {
                    chart.update();
                }
            } else {
                $report.slideUp();
            }
        },

        // Add this to store chart instances
        charts: {},

        updateReportsVisibility: function () {
            var self = this;
            Object.keys(this.visible_reports).forEach(function (reportType) {
                var $report = self.$('#report' + reportType.charAt(0).toUpperCase() + reportType.slice(1));
                if (self.visible_reports[reportType]) {
                    $report.show();
                } else {
                    $report.hide();
                }
            });
        },

        showCardView: function () {
            this.$('#cardView').show();
            this.$('#chartView').hide();
            this.$('#btnCardView').addClass('active');
            this.$('#btnChartView').removeClass('active');
        },

        showChartView: function () {
            this.$('#cardView').hide();
            this.$('#chartView').show();
            this.$('#btnChartView').addClass('active');
            this.$('#btnCardView').removeClass('active');
            if (!this.chartSolicitudesEstado) {
                this._renderSolicitudesEstado();
            }
        },

        handlePeriodChange: function (ev) {
            ev.preventDefault();
            var self = this;
            var period = $(ev.currentTarget).data('period');

            // Update UI state
            this.$('.btn-group button').removeClass('active');
            $(ev.currentTarget).addClass('active');

            this._loadDashboardData(period);
        },

        _loadDashboardData: function (period) {
            var self = this;
            this.loading_state = true;
            this._updateLoadingState();

            return rpc.query({
                model: 'dashboard',
                method: 'get_full_data',
                args: [{
                    period: period
                }],
            }).then(function (result) {
                self.dashboard_data = result;
                self.loading_state = false;
                self.error_state = false;
                self._updateLoadingState();
                self._refreshDashboard();
            }).guardedCatch(function (error) {
                self.loading_state = false;
                self.error_state = true;
                self._updateLoadingState();
                self._handleError(error);
            });
        },

        _updateLoadingState: function () {
            if (this.loading_state) {
                this.$('.dashboard-content').addClass('loading');
                this.$('.loading-spinner').removeClass('d-none');
            } else {
                this.$('.dashboard-content').removeClass('loading');
                this.$('.loading-spinner').addClass('d-none');
            }

            if (this.error_state) {
                this.$('.error-message').removeClass('d-none');
            } else {
                this.$('.error-message').addClass('d-none');
            }
        },

        _refreshDashboard: function () {
            this.$('.o_dashboard').empty();
            this.render_dashboards();
        },

        _handleError: function (error) {
            this.$('.error-message')
                .text(error.message || 'Ha ocurrido un error al cargar los datos')
                .removeClass('d-none');
        },

        willStart: function () {
            var self = this;
            this.login_employee = {};
            return this._super()
                .then(function () {
                    var def1 = rpc.query({
                        model: 'dashboard',
                        method: 'get_full_data',
                        args: [{}],
                    }, []).then(function (result) {
                        console.log(result);
                        self.users_info = result
                        // Inicializar dashboard_data con los datos necesarios
                        self.dashboard_data = {
                            solicitudes_estado: result.solicitudes_estado || {},
                            distribucion_profesiones: result.distribucion_profesiones || {},
                            tasas: result.tasas || {},
                            tiempo_promedio: result.tiempo_promedio || {
                                promedio_horas: 0,
                                total_solicitudes: 0
                            },
                            conteo_por_estado: result.conteo_por_estado || []
                        };
                    });
                    return $.when(def1);
                });
        },


        start: function () {
            console.log("START FUNCTION")
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.updateReportsVisibility();
            });
        },

        render_dashboards: function () {
            var self = this;
            _.each(this.dashboards_templates, function (template) {
                console.log('dad')
                self.$('.o_dashboard').append(QWeb.render(template, {widget: self,}));
            });
            _.defer(function () {
                self._renderCharts();  // Espera a que el DOM esté listo
            });
        },

        _renderCharts: function () {
            // // this.charts.chartSolicitudesEstado = this._renderSolicitudesEstado();
            // this.charts.chartProfesiones = this._renderDistribucionProfesiones();
            // this.charts.chartTasas = this._renderTasas();
        },

        _renderSolicitudesEstado: function () {
            var estados = this.dashboard_data.conteo_por_estado;
            var ctx = document.getElementById('chartSolicitudesEstado').getContext('2d');

            var labels = [];
            var data = [];
            var backgroundColors = [];

            estados.forEach(function (estado) {
                labels.push(estado.state_name);
                data.push(estado.cantidad);
                backgroundColors.push(estado.color || '#777');
            });

            if (this.chartSolicitudesEstado) {
                this.chartSolicitudesEstado.destroy();
            }

            this.chartSolicitudesEstado = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Solicitudes por Estado',
                        data: data,
                        backgroundColor: backgroundColors
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,  // Allow custom height
                    layout: {
                        padding: {
                            top: 20,
                            bottom: 20,
                            left: 10,
                            right: 10
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                                stepSize: 1  // Force step size to 1 for better granularity
                            },
                            max: Math.max(...data) + 2  // Add some padding on top
                        },
                        x: {
                            ticks: {
                                maxRotation: 45,
                                minRotation: 30,
                                autoSkip: false
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    return context.parsed.y + ' solicitudes';
                                }
                            }
                        }
                    }
                }
            });

            // Optionally, set canvas height explicitly for better visibility
            document.getElementById('chartSolicitudesEstado').style.height = '400px';
        },

        _renderDistribucionProfesiones: function () {
            var data = this.dashboard_data.distribucion_profesiones;
            var ctx = document.getElementById('chartProfesiones').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.profesiones,
                    datasets: [{
                        data: data.cantidades,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        },

        _renderTasas: function () {
            var data = this.dashboard_data.tasas;
            var ctx = document.getElementById('chartTasas').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Aprobadas', 'Rechazadas', 'En Proceso'],
                    datasets: [{
                        data: [
                            data.tasa_aprobacion,
                            data.tasa_rechazo,
                            100 - data.tasa_aprobacion - data.tasa_rechazo
                        ],
                        backgroundColor: ['#4BC0C0', '#FF6384', '#FFCE56']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        fetch_data: function () {
            var self = this;
            var def1 = rpc.query({
                model: 'dashboard',
                method: 'get_full_data',
                args: [{}],
            }, []).then(function (result) {
                console.log(result);
                self.users_info = result
            });
            return $.when(def1);
        },

        on_reverse_breadcrumb: function () {
            console.log("ON_REVERSE_BREADCRUMB")
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            // self.render_dashboards();
            this.fetch_data().then(function () {
                self.$('.o_radius_dashboard').empty();
                self.render_dashboards();
            });
        },

        update_cp: function () {
            var self = this;
            console.log("UPDATE_CP")
        },

        get_emp_image_url: function (employee) {
            return window.location.origin + '/web/image?model=hr.employee&field=image&id=' + employee;
        },

        request_function: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Solicitudes"),
                type: 'ir.actions.act_window',
                res_model: 'professional_registers.professional_request',
                view_mode: 'tree',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },
        inscription_function: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t(" Inscripciones"),
                type: 'ir.actions.act_window',
                res_model: 'professional_registers.inscription',
                view_mode: 'tree',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
                target: 'current' //self on some of them
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb
            });
        },


    });


    core.action_registry.add('dashboard.dashboard', Dashboard);

    return Dashboard;

});








