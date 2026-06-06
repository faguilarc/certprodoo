odoo.define('nomenclators.validate_file_size', function (require) {
    "use strict";

    document.addEventListener('DOMContentLoaded', function () {
        // Selecciona el campo de archivo dentro del widget many2many_binary
        const fileInputs = document.querySelectorAll('input[type="file"].o_input_file');


        fileInputs.forEach(function (fileInput) {
            fileInput.addEventListener('change', function (e) {
                const files = e.target.files;
                const tamañoMaximo = 5 * 1024 * 1024; // 5 MB en bytes

                for (let i = 0; i < files.length; i++) {
                    if (files[i].size > tamañoMaximo) {
                        alert("El archivo '" + files[i].name + "' no puede exceder los 5 MB.");
                        e.target.value = ''; // Limpia el campo de archivo
                        break; // Detiene la validación si encuentra un archivo demasiado grande
                    }
                }
            });
        });
    });
});