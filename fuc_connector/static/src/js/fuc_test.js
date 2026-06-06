odoo.define('fuc_connector.test', function (require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');

    var FUCTestFormController = FormController.extend({
        /**
         * Override to add custom functionality for FUC test form
         */
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                // Add event listeners for buttons
                this.$buttons.on('click', '#test_connection_btn', this._onTestConnection.bind(this));
                this.$buttons.on('click', '#generate_token_btn', this._onGenerateToken.bind(this));
            }
        },

        _onTestConnection: function () {
            var identity_number = $('#identity_number').val();
            var use_simulation = $('#use_simulation').is(':checked');

            if (!identity_number) {
                this.do_warn("Advertencia", "Por favor, ingrese un número de identidad.");
                return;
            }

            rpc.query({
                model: 'fuc.config',
                method: 'test_connection',
                args: [identity_number],
                kwargs: {
                    use_simulation: use_simulation
                }
            }).then(function (result) {
                if (result.status === 'success') {
                    var data = result.data;
                    var resultHtml = `
                        <div class="alert alert-success">
                            <h4>Consulta exitosa para CI: ${identity_number}</h4>
                            <p><strong>Nombre:</strong> ${data.primer_nombre} ${data.segundo_nombre || ''} ${data.primer_apellido} ${data.segundo_apellido || ''}</p>
                            <p><strong>Sexo:</strong> ${data.sexo}</p>
                            <p><strong>Edad:</strong> ${data.edad}</p>
                            <p><strong>Dirección:</strong> ${data.direccion}</p>
                            <p><strong>Municipio:</strong> ${data.municipio_residencia}</p>
                            <p><strong>Provincia:</strong> ${data.provincia_residencia}</p>
                            <p><strong>Fecha de Nacimiento:</strong> ${data.nacimiento_fecha}</p>
                        </div>
                    `;
                    $('#test_results').html(resultHtml);
                } else {
                    $('#test_results').html(`
                        <div class="alert alert-danger">
                            <h4>Error</h4>
                            <p>${result.message}</p>
                        </div>
                    `);
                }
            }).catch(function (error) {
                $('#test_results').html(`
                    <div class="alert alert-danger">
                        <h4>Error</h4>
                        <p>Ocurrió un error al probar la conexión: ${error.message}</p>
                    </div>
                `);
            });
        },

        _onGenerateToken: function () {
            rpc.query({
                model: 'fuc.config',
                method: 'generate_token',
                args: []
            }).then(function (result) {
                if (result.status === 'success') {
                    $('#test_results').html(`
                        <div class="alert alert-success">
                            <h4>Éxito</h4>
                            <p>${result.message}</p>
                        </div>
                    `);
                } else {
                    $('#test_results').html(`
                        <div class="alert alert-danger">
                            <h4>Error</h4>
                            <p>${result.message}</p>
                        </div>
                    `);
                }
            }).catch(function (error) {
                $('#test_results').html(`
                    <div class="alert alert-danger">
                        <h4>Error</h4>
                        <p>Ocurrió un error al generar el token: ${error.message}</p>
                    </div>
                `);
            });
        },
    });

    var FUCTestFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: FUCTestFormController,
        }),
    });

    viewRegistry.add('fuc_test_form', FUCTestFormView);

    return {
        FUCTestFormController: FUCTestFormController,
        FUCTestFormView: FUCTestFormView,
    };
});