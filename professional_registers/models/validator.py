from odoo import models, fields, api
from datetime import datetime
import requests
import time


class ProfessionalRegistersValidator(models.TransientModel):
    _name = 'professional_registers.validator'
    _description = 'Validador para Professional Registers (Transient)'

    def validate_generate_request(self, record=None, view=None, env='prod'):
        '''
        Función para validar la creación de las solicitudes para los casos siguientes:
        - Cliente Online -Cliente presencial
        Validaciones que se realizan:
        -Estado de las socilitudes
        -Cantidad de solicitudes por profesional
        -Unicidad de profesiones por solicitud

        Parámetros:
        -self: se recibe los datos del self de odoo en ese momento para luego obtener datos del env. como el registro en cuestión
        -view: se recibe el lugar donde se ejecuta la accion puede ser desde el perfil, o de la generacion de solicitud por parte del profesional
        ---- Las vistas pueden ser:
            -profile
            -generate_request_minimal
        -env(experimental): se recibe si es en entorno de produccón o desarrollo
        ---- Las opciones de entorno son:
            -prod
            -dev


        '''
        if env:
            if env == 'prod' and view == "profile":

                # Buscar solicitudes en estado = borrador
                count = self.env['professional_registers.professional_request'].search_count(
                    [('identity', '=', record.identity), ('priority', '=', 1)])
                if count >= 1:
                    title = 'Existencia de solicitud!!!'
                    message = f'Ya existen {count} solicitudes realizadas en estado borrador para este número de identidad. Debe terminar las solicitudes pendientes para crear una nueva !!!!' if count > 1 else f'Ya existe {count} solicitud realizada en estado borrador con este número de identidad. Debe terminar la solicitud pendiente para crear una nueva !!'

                    # Captura del wizard
                    wizard = self.env['professional_registers.message_wizard'].sudo().create({
                        'title': title,
                        'message': message,  # Aquí se pasa el mensaje HTML construido
                    })

                    # parametros para la funcion a ejecutar en el wizard
                    target_function_args = {
                        'ref': 'professional_registers.professional_request_act_window',

                    }
                    return {
                        'name': title,
                        'type': 'ir.actions.act_window',
                        'res_model': 'professional_registers.message_wizard',
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'target': 'new',
                        'context': {
                            'target_model': 'professional_registers.message_wizard',
                            # El modelo que contiene la función
                            'target_function': 'move_to_act',  # La función que deseas ejecutar
                            'target_function_args': target_function_args,  # Parámetros para la función
                            'profile': record.id,  # Pasar el ID del perfil

                        },
                        # 'clear_breadcrumbs': True,
                    }

                # Buscar solicitudes en estado > borrador
                else:

                    count = self.env['professional_registers.professional_request'].search_count(
                        [('identity', '=', record.identity), ('priority', '!=', 1)])
                    if count >= 1:
                        title = 'Existencia de solicitud!!!'
                        message = f'Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud?' if count > 1 else f'Ya existen {count} solicitud realizada para este número de identidad. Desea seguir generando otra solicitud?'

                        requests = self.env['professional_registers.professional_request'].search(
                            [('identity', '=', record.identity), ('priority', '!=', 1)])

                        # Agregar una lista de las solicitudes al mensaje
                        message += '<ul>'  # Lista no ordenada
                        for req in requests:
                            message += f'<li>Solicitud : {req.request_number} - Profesión: {req.profession.name} - Estado:{req.states.name}</li>'

                        message += '</ul>'

                        wizard = self.env['professional_registers.message_wizard'].sudo().create({
                            'title': title,
                            'message': message,  # Aquí se pasa el mensaje HTML construido
                        })

                        # target_function_args = {
                        #     'res_model': 'professional_registers.professional_request',
                        #     'name': 'Solicitud del profesional',
                        #     'target': 'main',
                        #     'view_mode': 'form',
                        #     'context': {
                        #         'target_model': 'professional_registers.profile',  # El modelo que contiene la función
                        #         'target_function': 'generate_request',  # La función que deseas ejecutar
                        #         'target_function_args': record,  # Parámetros para la función
                        #         'profile': record.id,  # Pasar el ID del perfil
                        #     }
                        # }

                        target_function_args = {
                            'record': record,

                        }

                        return {
                            'name': title,
                            'type': 'ir.actions.act_window',
                            'res_model': 'professional_registers.message_wizard',
                            'view_mode': 'form',
                            'res_id': wizard.id,
                            'target': 'new',
                            'context': {
                                'target_model': 'professional_registers.profile',
                                # El modelo que contiene la función
                                'target_function': 'generate_request',  # La función que deseas ejecutar
                                'target_function_args': target_function_args,  # Parámetros para la función
                                'profile': record.id,  # Pasar el ID del perfil
                            },
                        }
                    else:
                        self.env.context = {
                            'profile': record.id,
                        }
                        self.env['professional_registers.profile'].generate_request(record)

            if env == 'prod' and view == "generate_request_minimal":
                simulated_fuc = False

                identification_number = record.identity if self.env['nomenclators.nationality'].search(
                    [('id', '=', record.nationality_id.id)]).validate_fuc else record.passport

                # Buscar el usuario por la identificacion o pasaporte
                profile = self.env['professional_registers.profile'].search([('identity', '=', identification_number)], limit=1)

                if profile:

                    user = self.env['res.users'].search([('id', '=', profile.id_user_register.id)])

                    # En caso de ser cliente online redirigir al wizard sobre la existencia de su usuario online
                    if user.has_group("security.group_professional_client_online"):
                        title = 'Petición Denegada!!!'
                        message = f'Ya existe un usuario registrado en línea para este número de identidad. Debe continuar sus proceso de manera en línea.'

                        """Método para abrir el wizard con título, mensaje y función personalizados."""
                        wizard = self.env['professional_registers.message_wizard'].sudo().create({
                            'title': title,
                            'message': message,
                        })

                        return {
                            'name': title,
                            'type': 'ir.actions.act_window',
                            'res_model': 'professional_registers.message_wizard',
                            'view_mode': 'form',
                            'res_id': wizard.id,
                            'target': 'new',
                            'context': {
                                'target_model': 'professional_registers.profile',  # El modelo que contiene la función
                                'target_function': 'none',  # La función que deseas ejecutar
                                'profile': profile.id,
                                'no_action': True
                            },
                        }

                    # En caso de ser cliente redirigir al wizard sobre la existencia de sus solicitudes hechas
                    if user.has_group("security.group_professional_client"):

                        record.flag_button = True
                        # Buscar solicitudes en borrador
                        count = self.env['professional_registers.professional_request'].search_count(
                                [('identity', '=', identification_number), ('priority', '=', 1)])

                        if count == 1:
                            title = 'Existencia de solicitud!!!'
                            message = f'Ya existen {count} solicitudes realizadas en estado borrador para este número de identidad. Debe terminar las solicitudes pendientes para crear una nueva !!!!' if count > 1 else f'Ya existe {count} solicitud realizada en estado borrador con este número de identidad. Debe terminar la solicitud pendiente para crear una nueva !!'

                            # Captura del wizard
                            wizard = self.env['professional_registers.message_wizard'].sudo().create({
                                'title': title,
                                'message': message,  # Aquí se pasa el mensaje HTML construido
                            })

                            # parametros para la funcion a ejecutar en el wizard
                            target_function_args = {
                                'ref': 'professional_registers.professional_request_act_window',

                            }
                            return {
                                'name': title,
                                'type': 'ir.actions.act_window',
                                'res_model': 'professional_registers.message_wizard',
                                'view_mode': 'form',
                                'res_id': wizard.id,
                                'target': 'new',
                                'context': {
                                    'target_model': 'professional_registers.message_wizard',
                                    # El modelo que contiene la función
                                    'target_function': 'move_to_act',  # La función que deseas ejecutar
                                    'target_function_args': target_function_args,  # Parámetros para la función
                                    'profile': record.id,  # Pasar el ID del perfil

                                },
                                # 'clear_breadcrumbs': True,
                            }

                        else:
                            count = self.env['professional_registers.professional_request'].search_count(
                                [('identity', '=', record.identity), ('states', '!=', 1)])
                            if count >= 1:
                                title = 'Existencia de solicitud!!!'
                                message = f'Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud?' if count > 1 else f'Ya existen {count} solicitud realizada para este número de identidad. Desea seguir generando otra solicitud?'

                                requests = self.env['professional_registers.professional_request'].search(
                                    [('identity', '=', record.identity), ('states', '!=', 1)])

                                # Agregar una lista de las solicitudes al mensaje
                                message += '<ul>'  # Lista no ordenada
                                for req in requests:
                                    message += f'<li>Solicitud : {req.request_number} - Profesión: {req.profession.name} - Estado:{req.states.name}</li>'
                                message += '</ul>'

                                wizard = self.env['professional_registers.message_wizard'].sudo().create({
                                    'title': title,
                                    'message': message,  # Aquí se pasa el mensaje HTML construido
                                })

                                # target_function_args = {
                                #     'res_model': 'professional_registers.professional_request',
                                #     'name': 'Solicitud del profesional',
                                #     'target': 'main',
                                #     'view_mode': 'form',
                                #     'context': {
                                #         'target_model': 'professional_registers.profile',  # El modelo que contiene la función
                                #         'target_function': 'generate_request',  # La función que deseas ejecutar
                                #         'target_function_args': record,  # Parámetros para la función
                                #         'profile': record.id,  # Pasar el ID del perfil
                                #     }
                                # }

                                target_function_args = {
                                    'record': record.id,

                                }

                                return {
                                    'name': title,
                                    'type': 'ir.actions.act_window',
                                    'res_model': 'professional_registers.message_wizard',
                                    'view_mode': 'form',
                                    'res_id': wizard.id,
                                    'target': 'new',
                                    'context': {
                                        'target_model': 'professional_registers.profile',
                                        # El modelo que contiene la función
                                        'target_function': 'generate_request',
                                        # La función que deseas ejecutar
                                        'target_function_args': target_function_args,  # Parámetros para la función
                                        'profile': profile.id,  # Pasar el ID del perfil
                                    },
                                }

                            else:
                                self.env.context = {
                                    'profile': record.id,
                                }
                                self.env['professional_registers.professional_request_minimal'].search_simulated_data(
                                    record.id)


                else:

                    if simulated_fuc:
                        return self.env['professional_registers.professional_request_minimal'].search_simulated_data(
                            record.id)
                    else:
                        return self.env['professional_registers.professional_request_minimal'].search_data(record.id)
