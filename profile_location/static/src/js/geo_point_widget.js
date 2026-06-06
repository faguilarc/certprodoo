// static/src/js/geo_point_widget.js

// Al principio del archivo
var QWeb = require('web.QWeb');

odoo.define('professional_registers.geo_point_widget', function (require) {
    "use strict";

    var fieldRegistry = require('web.field_registry');
    var FieldText = require('web.basic_fields').FieldText;

    var GeoPointWidget = FieldText.extend({
        template: 'GeoPointWidget',

        events: {
            'click .geo_point_button': '_onButtonClick',
        },

        _onButtonClick: function (ev) {
            ev.preventDefault();
            this._showMapDialog();
        },

        _showMapDialog: function () {
            var self = this;
            var value = this.value || '';

            // Parsear el valor actual
            var lat = 0, lng = 0;
            if (value) {
                var parts = value.split(',');
                if (parts.length === 2) {
                    lat = parseFloat(parts[0].trim()) || 0;
                    lng = parseFloat(parts[1].trim()) || 0;
                }
            }

            // Crear el diálogo
            var $dialog = $(QWeb.render('GeoPointDialog', {
                lat: lat,
                lng: lng
            }));

            // Agregar el diálogo al cuerpo
            $('body').append($dialog);

            // Inicializar el mapa después de un pequeño retraso
            setTimeout(function () {
                self._initializeMap($dialog, lat, lng);
            }, 100);

            // Manejar el cierre del diálogo
            $dialog.on('hidden.bs.modal', function () {
                $dialog.remove();
            });

            // Manejar el guardado
            $dialog.find('.save_coordinates').click(function () {
                var newLat = parseFloat($dialog.find('#map_lat').val()) || 0;
                var newLng = parseFloat($dialog.find('#map_lng').val()) || 0;

                self._setValue(newLat + ', ' + newLng);
                $dialog.modal('hide');
            });
        },

        _initializeMap: function ($dialog, lat, lng) {
            // Cargar Leaflet dinámicamente
            if (typeof L === 'undefined') {
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css';
                document.head.appendChild(link);

                var script = document.createElement('script');
                script.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
                script.onload = function () {
                    self._createMap($dialog, lat, lng);
                };
                document.head.appendChild(script);
            } else {
                self._createMap($dialog, lat, lng);
            }
        },

        _createMap: function ($dialog, lat, lng) {
            // Inicializar el mapa
            var map = L.map($dialog.find('#map')[0]).setView([lat, lng], 13);

            // Añadir capa de OpenStreetMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            // Añadir marcador
            var marker = L.marker([lat, lng]).addTo(map);

            // Actualizar campos al mover el marcador
            marker.on('dragend', function (e) {
                var position = e.target.getLatLng();
                $dialog.find('#map_lat').val(position.lat.toFixed(6));
                $dialog.find('#map_lng').val(position.lng.toFixed(6));
            });

            // Hacer el marcador arrastrable
            marker.dragging.enable();
        }
    });

    fieldRegistry.add('geo_point', GeoPointWidget);

    return {
        GeoPointWidget: GeoPointWidget,
    };
});