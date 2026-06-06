odoo.define('professional_registers.validate_file_size', function (require) {
    "use strict";

    var Many2ManyBinary = require('web.Many2ManyBinary');

    Many2ManyBinary.include({
        _onUpload: function (ev) {
            const files = ev.target.files;
            const tamañoMaximo = 5 * 1024 * 1024; // 5 MB en bytes

            for (let i = 0; i < files.length; i++) {
                if (files[i].size > tamañoMaximo) {
                    alert("El archivo '" + files[i].name + "' no puede exceder los 5 MB.");
                    ev.target.value = ''; // Limpia el campo de archivo
                    return; // Detiene la subida si encuentra un archivo demasiado grande
                }
            }

            return this._super.apply(this, arguments);
        },
    });
});