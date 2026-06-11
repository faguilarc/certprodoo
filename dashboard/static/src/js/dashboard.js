odoo.define('dashboard.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    var Dashboard = AbstractAction.extend({
        template: 'DashboardDetails',
        cssLibs: [
            '/dashboard/static/src/css/Chart.min.css',
        ],
        jsLibs: [
            '/dashboard/static/src/js/chart.min.js',
        ],
        events: {
            'click .status-card': 'openFilteredView',
            'click .kpi-card': 'onKpiClick',
            'change .period-selector': 'onPeriodChange',
            'click #btnCardView': 'showCardView',
            'click #btnChartView': 'showChartView',
        },

        init: function (parent, context) {
            this._super(parent, context);
            this.dashboard_data = {};
            this.charts = {};
            this.current_period = 'year';
            this.loading = false;
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._loadData();
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Enable scrolling on the Odoo content container
                self.$el.parents('.o_content').addClass('dashboard-scrollable');
                self._renderDashboard();
            });
        },

        // ================================================================
        // DATA LOADING
        // ================================================================

        _loadData: function () {
            var self = this;

            return rpc.query({
                model: 'dashboard',
                method: 'get_full_data',
                args: [{period: this.current_period}],
            }).then(function (result) {
                self.dashboard_data = result;
            }).guardedCatch(function (error) {
                console.error('Error cargando dashboard:', error);
            });
        },

        _updateLoadingState: function () {
            if (!this.$el) return;
            var $spinner = this.$('.loading-spinner');
            var $content = this.$('.dashboard-content');
            if ($spinner.length) {
                if (this.loading) {
                    $spinner.removeClass('d-none');
                    $content && $content.addClass('d-none');
                } else {
                    $spinner.addClass('d-none');
                    $content && $content.removeClass('d-none');
                }
            }
        },

        // ================================================================
        // RENDERING
        // ================================================================

        _renderDashboard: function () {
            var self = this;

            if (!this.dashboard_data || !this.dashboard_data.kpi_cards) {
                return;
            }

            // Render KPI cards
            this._renderKpiCards();

            // Render all charts
            _.defer(function () {
                self._renderAllCharts();
            });
        },

        _renderKpiCards: function () {
            var kpi = this.dashboard_data.kpi_cards;
            if (!kpi) return;

            this.$('#kpiTotalRequests .kpi-value').text(kpi.total_requests || 0);
            this.$('#kpiApprovedRequests .kpi-value').text(kpi.approved_requests || 0);
            this.$('#kpiPendingRequests .kpi-value').text(kpi.pending_requests || 0);
            this.$('#kpiInscriptions .kpi-value').text(kpi.active_inscriptions || 0);
            this.$('#kpiExpedients .kpi-value').text(kpi.open_expedients || 0);
            this.$('#kpiClaims .kpi-value').text(kpi.active_claims || 0);
            this.$('#kpiAvgTime .kpi-value').text(kpi.avg_processing_days || 0);
        },

        _renderAllCharts: function () {
            // Destruir graficos existentes
            Object.keys(this.charts).forEach(function (key) {
                if (this.charts[key]) {
                    this.charts[key].destroy();
                }
            }.bind(this));
            this.charts = {};

            this._renderSolicitudesEstado();
            this._renderTendenciaMensual();
            this._renderTopProfesiones();
            this._renderTipoTramite();
            this._renderReclamaciones();
            this._renderTasasAprobacion();
        },

        _renderSolicitudesEstado: function () {
            var data = this.dashboard_data.solicitudes_estado;
            if (!data || !data.length) return;

            var ctx = document.getElementById('chartSolicitudesEstado');
            if (!ctx) return;

            var labels = [];
            var values = [];
            var colors = [];

            data.forEach(function (item) {
                labels.push(item.state_name);
                values.push(item.cantidad);
                colors.push(item.color || '#6c757d');
            });

            this.charts.solicitudesEstado = new Chart(ctx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#ffffff',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                usePointStyle: true,
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                    var pct = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return context.label + ': ' + context.parsed + ' (' + pct + '%)';
                                }
                            }
                        }
                    }
                }
            });
        },

        _renderTendenciaMensual: function () {
            var data = this.dashboard_data.tendencia_mensual;
            if (!data || !data.labels || !data.labels.length) return;

            var ctx = document.getElementById('chartTendenciaMensual');
            if (!ctx) return;

            this.charts.tendenciaMensual = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Creadas',
                            data: data.created,
                            borderColor: '#4e73df',
                            backgroundColor: 'rgba(78, 115, 223, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                        },
                        {
                            label: 'Aprobadas',
                            data: data.approved,
                            borderColor: '#1cc88a',
                            backgroundColor: 'rgba(28, 200, 138, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        },
                        x: {
                            grid: { display: false },
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                    }
                }
            });
        },

        _renderTopProfesiones: function () {
            var data = this.dashboard_data.top_profesiones;
            if (!data || !data.profesiones || !data.profesiones.length) return;

            var ctx = document.getElementById('chartTopProfesiones');
            if (!ctx) return;

            var colors = [
                '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e',
                '#e74a3b', '#858796', '#5a5c69', '#2e8b57',
                '#ff6384', '#9966ff'
            ];

            this.charts.topProfesiones = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.profesiones,
                    datasets: [{
                        label: 'Solicitudes',
                        data: data.cantidades,
                        backgroundColor: colors.slice(0, data.profesiones.length),
                        borderWidth: 0,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        },
                        y: {
                            grid: { display: false },
                        }
                    },
                    plugins: {
                        legend: { display: false },
                    }
                }
            });
        },

        _renderTipoTramite: function () {
            var data = this.dashboard_data.por_tipo_tramite;
            if (!data || !data.length) return;

            var ctx = document.getElementById('chartTipoTramite');
            if (!ctx) return;

            var labels = [];
            var values = [];
            var colors = [];

            data.forEach(function (item) {
                labels.push(item.name);
                values.push(item.count);
                colors.push(item.color);
            });

            this.charts.tipoTramite = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Solicitudes',
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 0,
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        },
                        x: {
                            grid: { display: false },
                        }
                    },
                    plugins: {
                        legend: { display: false },
                    }
                }
            });
        },

        _renderReclamaciones: function () {
            var data = this.dashboard_data.reclamaciones_estado;
            if (!data || !data.length) return;

            var ctx = document.getElementById('chartReclamaciones');
            if (!ctx) return;

            var labels = [];
            var values = [];
            var colors = [];

            data.forEach(function (item) {
                labels.push(item.name);
                values.push(item.cantidad);
                colors.push(item.color);
            });

            this.charts.reclamaciones = new Chart(ctx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#ffffff',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                usePointStyle: true,
                            }
                        },
                    }
                }
            });
        },

        _renderTasasAprobacion: function () {
            var data = this.dashboard_data.tasas;
            if (!data || !data.labels || !data.labels.length) return;

            var ctx = document.getElementById('chartTasas');
            if (!ctx) return;

            this.charts.tasas = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Aprobadas',
                            data: data.aprobadas,
                            backgroundColor: '#1cc88a',
                        },
                        {
                            label: 'Rechazadas',
                            data: data.rechazadas,
                            backgroundColor: '#e74a3b',
                        },
                        {
                            label: 'Otras',
                            data: data.otras,
                            backgroundColor: '#858796',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            stacked: true,
                            grid: { display: false },
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                    }
                }
            });
        },

        // ================================================================
        // EVENT HANDLERS
        // ================================================================

        onPeriodChange: function (ev) {
            this.current_period = $(ev.currentTarget).val();
            var self = this;
            this._loadData().then(function () {
                self._renderDashboard();
            });
        },

        openFilteredView: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            var stateId = $(ev.currentTarget).data('estado');
            if (!stateId) return;

            this.do_action({
                name: 'Solicitudes',
                type: 'ir.actions.act_window',
                res_model: 'professional_registers.professional_request',
                view_mode: 'tree',
                views: [[false, 'list'], [false, 'form']],
                domain: [['states', '=', stateId]],
                target: 'current',
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb.bind(this),
            });
        },

        onKpiClick: function (ev) {
            var target = $(ev.currentTarget).data('target');
            if (!target) return;

            var domain = [];
            var model = 'professional_registers.professional_request';

            switch (target) {
                case 'total_requests':
                    break;
                case 'approved_requests':
                    domain = [['states.priority', '=', 6]];
                    break;
                case 'pending_requests':
                    domain = [['states.priority', 'in', [2, 3]]];
                    break;
                case 'inscriptions':
                    model = 'professional_registers.inscription';
                    domain = [['retired', '=', false]];
                    break;
                case 'expedients':
                    model = 'professional_registers.expedient';
                    domain = [['state', 'in', ['open', 'pending']]];
                    break;
                case 'claims':
                    model = 'professional_registers.claim_request';
                    domain = [['claim_status', 'in', ['in_process', 'evaluating']]];
                    break;
            }

            this.do_action({
                name: target === 'inscriptions' ? 'Inscripciones' :
                       target === 'expedients' ? 'Expedientes' :
                       target === 'claims' ? 'Reclamaciones' : 'Solicitudes',
                type: 'ir.actions.act_window',
                res_model: model,
                view_mode: 'tree',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb.bind(this),
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
        },

        on_reverse_breadcrumb: function () {
            var self = this;
            this._loadData().then(function () {
                self._renderDashboard();
            });
        },

        destroy: function () {
            // Remove scrolling class when leaving dashboard
            this.$el.parents('.o_content').removeClass('dashboard-scrollable');
            Object.keys(this.charts).forEach(function (key) {
                if (this.charts[key]) {
                    this.charts[key].destroy();
                }
            }.bind(this));
            this.charts = {};
            this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('dashboard.dashboard', Dashboard);

    return Dashboard;
});
