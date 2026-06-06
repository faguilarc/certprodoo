// static/src/js/selection_checkboxes_widget.js
odoo.define('your_module.SelectionCheckboxes', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var fieldRegistry = require('web.field_registry');
var core = require('web.core');

var SelectionCheckboxesWidget = AbstractField.extend({
    className: 'o_field_selection_checkboxes',
    supportedFieldTypes: ['selection', 'char', 'text'],
    
    init: function () {
        this._super.apply(this, arguments);
        this.selectedValues = [];
        this._parseValue();
    },

    _parseValue: function () {
        // Parsear el valor actual (puede ser string separado por comas)
        if (this.value) {
            if (typeof this.value === 'string') {
                this.selectedValues = this.value.split(',').map(v => v.trim()).filter(v => v);
            } else {
                this.selectedValues = [this.value];
            }
        } else {
            this.selectedValues = [];
        }
    },

    _renderReadonly: function () {
        var self = this;
        this.$el.empty();
        
        if (!this.value || this.selectedValues.length === 0) {
            return;
        }

        // Obtener las opciones del campo
        this._getSelectionOptions().then(function(options) {
            var selectedLabels = [];
            self.selectedValues.forEach(function(value) {
                var option = options.find(opt => opt[0] === value);
                if (option) {
                    selectedLabels.push(option[1]);
                }
            });
            
            self.$el.html('<span class="badge badge-pill badge-info mr-1">' + 
                         selectedLabels.join('</span><span class="badge badge-pill badge-info mr-1">') + 
                         '</span>');
        });
    },

    _renderEdit: function () {
        var self = this;
        this.$el.empty();
        
        this._getSelectionOptions().then(function(options) {
            if (!options || options.length === 0) {
                self.$el.html('<div class="text-muted">No hay opciones disponibles</div>');
                return;
            }

            var $container = $('<div class="o_selection_checkboxes_container"></div>');
            
            options.forEach(function(option) {
                var value = option[0];
                var label = option[1];
                var isChecked = self.selectedValues.includes(value);
                
                var $checkbox = $('<div class="form-check">' +
                    '<input class="form-check-input" type="checkbox" ' +
                    'value="' + value + '" id="checkbox_' + value + '"' +
                    (isChecked ? ' checked' : '') + '>' +
                    '<label class="form-check-label" for="checkbox_' + value + '">' +
                    label + '</label>' +
                    '</div>');
                
                $container.append($checkbox);
            });
            
            self.$el.append($container);
            
            // Bind eventos
            self.$el.find('input[type="checkbox"]').on('change', function() {
                self._onCheckboxChange();
            });
        });
    },

    _getSelectionOptions: function () {
        var self = this;
        
        if (this.field.type === 'selection' && this.field.selection) {
            // Si es un campo selection con opciones estáticas
            return Promise.resolve(this.field.selection);
        } else {
            // Si es un campo con selection dinámica
            return this._rpc({
                model: this.model,
                method: 'fields_get',
                args: [[this.name]],
                context: this.record.getContext(),
            }).then(function(result) {
                var fieldInfo = result[self.name];
                if (fieldInfo && fieldInfo.selection) {
                    return fieldInfo.selection;
                }
                return [];
            });
        }
    },

    _onCheckboxChange: function () {
        var selectedValues = [];
        this.$el.find('input[type="checkbox"]:checked').each(function() {
            selectedValues.push($(this).val());
        });
        
        this.selectedValues = selectedValues;
        var newValue = selectedValues.length > 0 ? selectedValues.join(',') : false;
        this._setValue(newValue);
    },

    _setValue: function (value, options) {
        this._super(value, options);
        this._parseValue();
    },

    _onFieldChanged: function () {
        this._parseValue();
        if (this.mode === 'edit') {
            this._renderEdit();
        } else {
            this._renderReadonly();
        }
    }
});

// Registrar el widget
fieldRegistry.add('selection_checkboxes', SelectionCheckboxesWidget);

return SelectionCheckboxesWidget;

});