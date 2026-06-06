odoo.define('nomenclators.dynamic_button', function (require) {
"use strict";

    var FormRenderer = require('web.FormRenderer');
    var rpc = require('web.rpc');

    FormRenderer.include({
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Seleccionar el campo procedure_type_id
                var procedureTypeField = self.$el.find('[name="procedure_type_id"]');

                // Función para actualizar el botón
                function updateButtonText() {
                    var procedureId = procedureTypeField.val();

                    if (procedureId) {
                        // Llamada RPC para obtener estado del trámite
                        rpc.query({
                            model: 'nomenclators.procedure_types',
                            method: 'search_read',
                            args: [[
                                ['id', '=', parseInt(procedureId)],
                                ['current_suspension_id', '!=', false]
                            ]],
                            fields: ['id']
                        }).then(function (result) {
                            var button = self.$el.find('button[name="action_confirm"]');
                            if (result.length > 0) {
                                button.text("Reanudar proceso");
                            } else {
                                button.text("Detener proceso");
                            }
                        });
                    }
                }

                // Actualizar al cambiar la selección
                procedureTypeField.on('change', updateButtonText);
                // Actualizar al cargar inicialmente
                updateButtonText();
            });
        }
    });

});