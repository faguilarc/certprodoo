from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date


# # Validacion en request minimal (Professional request)
# def validate_request_generation(self):
#     identification_number = self.identity if self.nationality_id.id == 1 else self.passport
#
#     # parche para dev
#     if not self.env['nomenclators.nationality'].search([('id', '=', self.nationality_id.id)]).validate_fuc:
#         identification_number = self.passport
#
#     # Buscar el usuario por la identificacion o pasaporte
#     profile = self.env['professional_registers.profile'].search([('identity', '=', identification_number)])
#     if profile:
#         pass
#         user = self.env['res.users'].search(
#             [('id', '=', profile.user_id.id)])
#         group_ids = user.groups_id
#         for group in self.env['res.groups'].browse(group_ids):
#
#             # En caso de ser cliente online redirigir al wizard sobre la existencia de su usuario online
#             if self.env["res.users"].has_group("security.group_professional_client_online"):
#                 title = 'Petición Denegada!!!'
#                 message = f'Ya existe un usuario registrado en línea para este número de identidad. Debe continuar sus proceso de manera en línea.'
#
#                 """Método para abrir el wizard con título, mensaje y función personalizados."""
#                 wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                     'title': title,
#                     'message': message,
#                 })
#
#                 return {
#                     'name': title,
#                     'type': 'ir.actions.act_window',
#                     'res_model': 'professional_registers.message_wizard',
#                     'view_mode': 'form',
#                     'res_id': wizard.id,
#                     'target': 'new',
#                     'context': {
#                         'target_model': 'professional_registers.profile',  # El modelo que contiene la función
#                         'target_function': 'none',  # La función que deseas ejecutar
#                         'profile': profile.id,
#                         'no_action': True
#                     },
#                 }
#             # En caso de ser cliente redirigir al wizard sobre la existencia de sus solicitudes hechas
#             if self.env["res.users"].has_group("security.group_professional_client"):
#
#                 count = self.env['professional_registers.professional_request'].search_count(
#                     [('identity', '=', identification_number)])
#
#                 if count >= 1:
#                     title = 'Existencia de solicitud!!!'
#                     message = f'Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud ?' if count > 1 else f'Ya existe {count} solicitud realizada con este número de identidad. Desea seguir generando otra solicitud ?'
#
#                     """Método para abrir el wizard con título, mensaje y función personalizados."""
#                     wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                         'title': title,
#                         'message': message,
#                     })
#
#                     return {
#                         'name': title,
#                         'type': 'ir.actions.act_window',
#                         'res_model': 'professional_registers.message_wizard',
#                         'view_mode': 'form',
#                         'res_id': wizard.id,
#                         'target': 'new',
#                         'context': {
#                             'target_model': 'professional_registers.profile',  # El modelo que contiene la función
#                             'target_function': 'generate_request',  # La función que deseas ejecutar
#                             'profile': profile.id,  # Pasar el nombre de la función como cadena
#                         },
#                     }
#     else:
#         self.search_data()
#
#
# def request_count_by_user(self):
#     count = self.env['professional_registers.professional_request'].search_count([('identity', '=', self.identity)])
#
#     if count >= 1:
#         title = 'Existencia de solicitud!!!'
#         message = f'<p>Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud?</p>'
#
#         # Buscar las solicitudes existentes
#         requests = self.env['professional_registers.professional_request'].search(
#             [('identity', '=', self.identity)])
#
#         # Agregar una lista de las solicitudes al mensaje
#         message += '<ul>'  # Lista no ordenada
#         for req in requests:
#             message += f'<li>Solicitud : {req.request_number} - Profesión: {req.profession.name}</li>'
#         message += '</ul>'
#
#         # Crear el wizard con el mensaje dinámico
#         wizard = self.env['professional_registers.message_wizard'].sudo().create({
#             'title': title,
#             'message': message,  # Aquí se pasa el mensaje HTML construido
#         })
#
#         return {
#             'name': title,
#             'type': 'ir.actions.act_window',
#             'res_model': 'professional_registers.message_wizard',
#             'view_mode': 'form',
#             'res_id': wizard.id,
#             'target': 'new',
#             'context': {
#                 'target_model': 'professional_registers.profile',  # El modelo que contiene la función
#                 'target_function': 'generate_request',  # La función que deseas ejecutar
#                 'profile': self.id,  # Pasar el ID del perfil
#             },
#         }
#     else:
#         self.generate_request()
#

# def validate_generate_request(self, view=None, env='prod'):
#     '''
#     Función para validar la creación de las solicitudes para los casos siguientes:
#     - Cliente Online -Cliente presencial
#     Validaciones que se realizan:
#     -Estado de las socilitudes
#     -Cantidad de solicitudes por profesional
#     -Unicidad de profesiones por solicitud
#
#     Parámetros:
#     -self: se recibe los datos del self de odoo en ese momento para luego obtener datos del env. como el registro en cuestión
#     -view: se recibe el lugar donde se ejecuta la accion puede ser desde el perfil, o de la generacion de solicitud por parte del profesional
#     ---- Las vistas pueden ser:
#         -profile
#         -generate_request_minimal
#     -env(experimental): se recibe si es en entorno de produccón o desarrollo
#     ---- Las opciones de entorno son:
#         -prod
#         -dev
#
#
#     '''
#     if env:
#         if env == 'prod' and view == "profile":
#
#             # Buscar solicitudes en borrador
#             count = self.env['professional_registers.professional_request'].search_count(
#                 [('identity', '=', self.identity), ('states', '=', 1)])
#             if count >= 1:
#                 title = 'Existencia de solicitud!!!'
#                 message = f'Ya existen {count} solicitudes realizadas en estado Borrador para este número de identidad. Debe terminar las solicitudes pendientes para crear una nueva ?' if count > 1 else f'Ya existe {count} solicitud realizada en estado Borrador . con este número de identidad. Debe terminar la solicitude pendiente para crear una nueva ? ?'
#
#                 # Captura del wizard
#                 wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                     'title': title,
#                     'message': message,  # Aquí se pasa el mensaje HTML construido
#                 })
#
#                 # parametros para la funcion a ejecutar en el wizard
#                 target_function_args = {
#                     'res_model': 'professional_registers.professional_request',
#                     'name': 'Solicitud del profesional',
#                     'target': 'main',
#                     'view_mode': 'tree',
#
#                 }
#
#                 return {
#                     'name': title,
#                     'type': 'ir.actions.act_window',
#                     'res_model': 'professional_registers.message_wizard',
#                     'view_mode': 'form',
#                     'res_id': wizard.id,
#                     'target': 'new',
#                     'context': {
#                         'target_model': 'professional_registers.message_wizard',  # El modelo que contiene la función
#                         'target_function': 'move_to_tree',  # La función que deseas ejecutar
#                         'target_function_args': target_function_args,  # Parámetros para la función
#                         'profile': self.id,  # Pasar el ID del perfil
#                     },
#                 }
#
#
#             else:
#
#                 count = self.env['professional_registers.professional_request'].search_count(
#                     [('identity', '=', self.identity), ('states', '!=', 1)])
#                 if count >= 1:
#                     title = 'Existencia de solicitud!!!'
#                     message = f'Ya existen {count} solicitudes realizadas en para este número de identidad. Debe terminar las solicitudes pendientes para crear una nueva ?' if count > 1 else f'Ya existe {count} solicitud realizada en estado Borrador . con este número de identidad. Debe terminar la solicitude pendiente para crear una nueva ? ?'
#
#                     requests = self.env['professional_registers.professional_request'].search(
#                         [('identity', '=', self.identity), ('states', '!=', 1)])
#
#                     # Agregar una lista de las solicitudes al mensaje
#                     message += '<ul>'  # Lista no ordenada
#                     for req in requests:
#                         message += f'<li>Solicitud : {req.request_number} - Profesión: {req.profession.name}</li>'
#                     message += '</ul>'
#
#                     wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                         'title': title,
#                         'message': message,  # Aquí se pasa el mensaje HTML construido
#                     })
#
#                     target_function_args = {
#                         'res_model': 'professional_registers.professional_request',
#                         'name': 'Solicitud del profesional',
#                         'target': 'main',
#                         'view_mode': 'form',
#                         'context': {
#                             'target_model': 'professional_registers.profile',  # El modelo que contiene la función
#                             'target_function': 'generate_request',  # La función que deseas ejecutar
#                             'profile': self.id,  # Pasar el ID del perfil
#                         }
#                     }
#
#                     return {
#                         'name': title,
#                         'type': 'ir.actions.act_window',
#                         'res_model': 'professional_registers.message_wizard',
#                         'view_mode': 'form',
#                         'res_id': wizard.id,
#                         'target': 'new',
#                         'context': {
#                             'target_model': 'professional_registers.message_wizard',
#                             # El modelo que contiene la función
#                             'target_function': 'move_to_tree',  # La función que deseas ejecutar
#                             'target_function_args': target_function_args,  # Parámetros para la función
#                             'profile': self.id,  # Pasar el ID del perfil
#                         },
#                     }
#                 else:
#                     self.env['professional_registers.profile'].generate_request()
#
#         if env == 'prod' and view == "generate_request_minimal":
#
#             identification_number = self.identity if self.env['nomenclators.nationality'].search(
#                 [('id', '=', self.nationality_id.id)]).validate_fuc else self.passport
#
#             # Buscar el usuario por la identificacion o pasaporte
#             profile = self.env['professional_registers.profile'].search([('identity', '=', identification_number)])
#
#             if profile:
#
#                 user = self.env['res.users'].search([('id', '=', profile.user_id.id)])
#
#                 # En caso de ser cliente online redirigir al wizard sobre la existencia de su usuario online
#                 if user.has_group("security.group_professional_client_online"):
#                     title = 'Petición Denegada!!!'
#                     message = f'Ya existe un usuario registrado en línea para este número de identidad. Debe continuar sus proceso de manera en línea.'
#
#                     """Método para abrir el wizard con título, mensaje y función personalizados."""
#                     wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                         'title': title,
#                         'message': message,
#                     })
#
#                     return {
#                         'name': title,
#                         'type': 'ir.actions.act_window',
#                         'res_model': 'professional_registers.message_wizard',
#                         'view_mode': 'form',
#                         'res_id': wizard.id,
#                         'target': 'new',
#                         'context': {
#                             'target_model': 'professional_registers.profile',  # El modelo que contiene la función
#                             'target_function': 'none',  # La función que deseas ejecutar
#                             'profile': profile.id,
#                             'no_action': True
#                         },
#                     }
#                 # En caso de ser cliente redirigir al wizard sobre la existencia de sus solicitudes hechas
#                 if user.has_group("security.group_professional_client"):
#
#                     count = self.env['professional_registers.professional_request'].search_count(
#                         [('identity', '=', identification_number)])
#
#                     if count >= 1:
#                         title = 'Existencia de solicitud!!!'
#                         message = f'Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud ?' if count > 1 else f'Ya existe {count} solicitud realizada con este número de identidad. Desea seguir generando otra solicitud ?'
#
#                         """Método para abrir el wizard con título, mensaje y función personalizados."""
#                         wizard = self.env['professional_registers.message_wizard'].sudo().create({
#                             'title': title,
#                             'message': message,
#                         })
#
#                         return {
#                             'name': title,
#                             'type': 'ir.actions.act_window',
#                             'res_model': 'professional_registers.message_wizard',
#                             'view_mode': 'form',
#                             'res_id': wizard.id,
#                             'target': 'new',
#                             'context': {
#                                 'target_model': 'professional_registers.profile',
#                                 # El modelo que contiene la función
#                                 'target_function': 'generate_request',  # La función que deseas ejecutar
#                                 'profile': profile.id,  # Pasar el nombre de la función como cadena
#                             },
#                         }
#             else:
#
#                 self.env['professional_registers.professional_request_minimal'].search_simulated_data(self)


def action_confirm(self):
    # Recupera el nombre del modelo, la función y los argumentos del contexto
    target_model = self.env.context.get('target_model')
    target_function = self.env.context.get('target_function')
    target_function_args = self.env.context.get('target_function_args', {})  # Parámetros opcionales
    no_action = self.env.context.get('no_action')

    if target_model and target_function and not no_action:
        # Obtiene la instancia del modelo deseado
        model_instance = self.env[target_model]

        # Verifica que el modelo tenga la función y que sea ejecutable
        if hasattr(model_instance, target_function):
            func = getattr(model_instance, target_function)
            if callable(func):
                # Llama a la función del modelo objetivo y pasa los argumentos
                return func(**target_function_args)  # Pasar los parámetros como kwargs
            else:
                raise ValueError(f"{target_function} no es una función ejecutable.")
        else:
            raise ValueError(f"El modelo {target_model} no tiene una función llamada {target_function}.")
    else:
        if no_action:
            pass
        else:
            raise ValueError("El nombre del modelo o de la función no fueron especificados.")
