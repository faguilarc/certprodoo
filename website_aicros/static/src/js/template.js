console.log("Here")
odoo.define('website_aicros.s_website_aicros_form', function (require) {
    "use strict";

//    document.getElementById("structure").onclick = function() {myFunction()};

    function myFunction() {
//        var ajax = require('web.ajax');
//        ajax.jsonRpc("/get_data", 'call').then(function(data) {
        console.log(data);
        console.log("Here")
//        if (data) {
//            // Code
//        } else {
//           // Code
//            location.href ='http://localhost:8069/structure';
//        });
    }

});
//
// odoo.define('website_aicros.s_website_aicros_form', function (require) {
//     "use strict";
//     console.log('entre al dinamic selector')
//     var FormController = require('web.FormController');
//     var session = require('web.session');
//
//     FormController.include({
//         render_buttons: function ($node) {
//             this._super.apply(this, arguments);
//
//             // Escuchar cambios en el campo de profesiones
//             $('#professions').change(function () {
//                 var selectedProfessionId = $(this).val();
//                 var specialtySelect = $('#specialties');
//                 var specialtyOptions = [];
//
//                 // Limpiar las opciones actuales
//                 specialtySelect.empty();
//
//                 // Obtener las especialidades para la profesión seleccionada
//                 if (selectedProfessionId) {
//                     $.ajax({
//                         url: '/my_module/get_specialties',
//                         type: 'GET',
//                         data: {profession_id: selectedProfessionId},
//                         success: function (data) {
//                             // Procesar las especialidades recibidas
//                             data.forEach(function (specialty) {
//                                 specialtyOptions.push('<option value="' + specialty.id + '">' + specialty.name + '</option>');
//                             });
//
//                             // Actualizar las opciones en el select de especialidades
//                             specialtySelect.html(specialtyOptions.join(''));
//                         }
//                     });
//                 } else {
//                     // Opciones vacías si no hay profesión seleccionada
//                     specialtySelect.html('<option value="">Especialidad</option>');
//                 }
//             });
//         },
//     });
// });
//
$(document).ready(function () {
    $('#professions').on('change', function () {
        var profession_id = $(this).val();
        console.log(profession_id)
        if (profession_id) {
            $.ajax({
                url: '/web/get_specialties?profession_id=' + profession_id,
                type: 'POST',
                dataType: 'json',  // Esperas una respuesta JSON

                success: function (data) {
                    var $specialty_select = $('#specialties');
                    $specialty_select.empty();
                    $specialty_select.append('<option value="">Especialidad</option>');
                    $.each(data, function (index, specialty) {
                        console.log(specialty);
                        $specialty_select.append('<option value="' + specialty.id + '">' + specialty.name + '</option>');
                    });
                },
                error: function (error) {
                    console.log("Error en la petición: ", error);
                }
            });
        } else {
            $('#specialties').empty();
            $('#specialties').append('<option value="">Especialidad</option>');
        }
    });
});

// $(document).ready(function () {
//     $('#register_form_out').on('submit', function (e) {
//         e.preventDefault(); // Evitar el envío normal del formulario
//
//         // Recoger los datos del formulario
//         var formData = {
//             name: $('#name').val(),
//             user: $('#user').val(),
//             password: $('#password').val(),
//             confirm_password: $('#confirm_password').val(),
//             email: $('#email').val(),
//             first_lastname: $('#first_lastname').val(),
//             second_lastname: $('#second_lastname').val(),
//             identification: $('#identification').val(),
//             nationalities: $('#nationalities').val(),
//         };
//
//         // Enviar la solicitud AJAX
//         $.ajax({
//             url: '/web/register_user', // Ruta del controlador
//             type: 'POST',
//             contentType: 'application/json',
//             data: JSON.stringify(formData), // Convertir los datos a JSON
//             success: function (response) {
//                 if (response.error) {
//                     // Mostrar el error en el modal
//                     $('#messageModal').text(response.error);
//                 } else if (response.success) {
//                     // Mostrar el éxito en el modal
//                     $('#messageModal').text(response.success);
//                 }
//
//                 // Abrir el modal para mostrar el mensaje
//                 $('#messageModal').modal('show');
//             },
//             error: function (error) {
//                 $('#messageModal').modal('show');
//                 $('#messageModal').text('Ocurrió un error inesperado');
//
//             }
//         });
//     });
// });