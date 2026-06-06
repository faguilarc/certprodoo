# -*- coding: utf-8 -*-
import random

from odoo import models, fields, api, exceptions, _
from datetime import datetime
import base64
import requests
from unidecode import unidecode
import os
import time

from odoo.exceptions import ValidationError


class ProfessionalRequestMinimal(models.Model):
    _name = 'professional_registers.professional_request_minimal'
    _description = 'Solicitud del profesional simplificada'
    _rec_name = 'request_number'

    request_number = fields.Char('Nro. solicitud')

    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")

    name = fields.Char('Nombre')
    first_last_name = fields.Char('Primer apellido')
    second_last_name = fields.Char('Segundo apellido')
    identity = fields.Char('Carné de identidad', size=11)
    passport = fields.Char('Pasaporte', size=11)
    id_fuc = fields.Char('Id')
    address = fields.Text('Dirección particular')
    country = fields.Many2one('res.country', string="País")
    country_states = fields.Many2one('res.country.state', string="Provincia")
    city = fields.Many2one('res.city', string="Municipio")
    sex = fields.Selection([('male', 'Masculino'),
                            ('female', 'Femenino')], string="Sexo")

    other_interested = fields.Text('Otros datos de interés')

    show_button = fields.Boolean('mostrar', default=False)
    flag_button = fields.Boolean('Buscar', default=False)

    @api.constrains('identity')
    def _check_identity_length(self):
        for record in self:
            if record.identity:
                if len(record.identity) < 11:
                    raise ValidationError("El número de identidad  no puede tener menos de 11 caracteres.")

                if len(record.identity) > 11:
                    raise ValidationError("El número de identidad  no puede tener más de 11 caracteres.")

    @api.constrains('passport')
    def _check_passport_length(self):
        for record in self:
            if record.passport:
                if len(record.passport) < 6:
                    raise ValidationError("El número de pasaporte debe tener al menos 6 caracteres.")
                if len(record.passport) > 11:
                    raise ValidationError("El número de pasaporte no puede tener más de 11 caracteres.")

    @api.onchange('nationality_id')
    def onchange_nationality(self):
        if self.nationality_id:
            if self.nationality_id.validate_fuc:
                self.show_button = True
                self.flag_button = False
            else:
                self.show_button = False
                self.flag_button = True

            self.identity = ''
            self.passport = ''
            self.clear_fields()

    @api.onchange('identity', 'passport')
    def onchange_identities(self):
        if self.show_button:
            self.flag_button = False
        else:
            self.flag_button = True

    # Buttons
    def generate_request(self, record=None):

        if not record.flag_button:

            raise exceptions.ValidationError(
                f"No se puede generar la solicitud.\n\n"

            )


        request_number = self.env['professional_registers.professional_request'].get_request_number()
        full_name, user, password = self.get_full_name_password(record, request_number)
        request = self.env['professional_registers.professional_request'].with_context(
            creation_origin='request_minimal'  # o 'profile'
        ).create({
            'request_number': request_number,
            'name': record.name,
            'first_last_name': record.first_last_name,
            'second_last_name': record.second_last_name,
            'full_name': full_name,
            'nationality_id': record.nationality_id.id,
            'identity': record.identity if record.show_button else record.passport,
            'id_fuc': record.id_fuc,
            'sex': record.sex,
            'address': record.address,
            'country': record.country.id,
            'country_states': record.country_states.id,
            'procedure_type': self.env['professional_registers.professional_request'].get_procedure_default(),

            'city': record.city.id,
            'user': user,
            'user_id': self.env.uid,
            'password': password,
            'observation': record.other_interested,
            'register_type': 'register',
            'states': self.get_default_state(),
            'priority': 1,
            'is_inscription_fuc': True if record.nationality_id.validate_fuc else False,
            'date_request': datetime.utcnow().date().today()
        })

        # view = self.env.ref('professional_registers.professional_request_form_view')
        msg = "Se ha generado la solicitud No: " + str(request.request_number)
        self.env.user.notify_warning(
            message=msg)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'name': 'Solicitud del profesional',
            'view_mode': 'form',
            'res_id': request.id,
            'target': 'main',
            'clear_breadcrumbs': True,
        }

    def generate_token(self):
        message = self.get_keys()
        url_token = self.get_token_url()
        grant = '?grant_type=client_credentials'
        scope = '&scope=nivel10'
        url_token = f"{url_token}{grant}{scope}"
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        variableencode = base64_bytes.decode('ascii')
        headers = {'Authorization': f"Basic {variableencode}"}
        response = requests.post(url=url_token, headers=headers)
        variable = response.json()
        variable = variable.get('access_token')
        self.update_token(variable)
        return variable

    def search_data(self, record):

        if record:
            record = self.env['professional_registers.professional_request_minimal'].browse(record)
        else:
            raise exceptions.ValidationError('No se puede buscar los datos .')

        if record.nationality_id.validate_fuc:

            # Add traces
            model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request_minimal')])
            user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
            msg = 'Búsqueda por CI: ' + str(
                record.identity) + ' a la aplicación Registro del ciudadano para generación de solicitud.'
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': msg
            })

            # 71012229259
            identity = record.identity
            self.clear_fields()

            # aqui va tu url base y la del token
            # url_base = 'https://apis-fuc.xutil.cu/pn-api-consulta/2.0.210111/api/v1/nivel10?'
            url_base = self.get_url_base()
            # url_token = 'https://apis-fuc.xutil.cu/token'
            # url_token = self.get_token_url()

            # message = "yaBXFT57XirizpO0TivSDiuIMnka:vcGhbLOKH9Vcb4BSKeOdXPYkcrUa"
            variable = self.generate_token()
          
                

            reintentos = 0
            response_ok = False
            url = f"{url_base}identidad_numero={identity}"
            headers = {'Authorization': f"Bearer {variable}", 'Accept': 'application/json'}
            data = []
            while reintentos < 3 and not response_ok:

                response = requests.get(url=url, headers=headers)
                print(response)
                if response.status_code == 200 and self.validate_fuc(response.json()):
                    response = response.json()
                    data = response
                    response_ok = True
                else:
                    reintentos += 1
                    time.sleep(3)

            # random_data = self.generate_random_data()
            # data = [random_data]

            for r in data:
                print(f'esto es dentro de la data en uno de sus elementos: {r}')
                record.flag_button = True
                id = r['id']
                identity = r['identidad_numero']
                first_name = r['primer_nombre']
                second_name = r['segundo_nombre']
                first_last_name = r['primer_apellido']
                second_last_name = r['segundo_apellido']
                sex = r['sexo']
                address = r['direccion']
                city_name = r['municipio_residencia']
                state_name = r['provincia_residencia']
                deceased = r['fallecido']
                deceased_volume = r['defuncion_tomo']
                deceased_folio = r['defuncion_folio']
                immigration_status = r['condicion_migratoria']

                record.id_fuc = id
                record.identity = identity
                name = first_name
                if second_name != None:
                    name = str(name) + ' ' + str(second_name)
                record.name = name
                record.first_last_name = first_last_name
                record.second_last_name = second_last_name
                if sex == 'F':
                    record.sex = 'female'
                else:
                    record.sex = 'male'

                record.address = address

                other_interested = ""

                if deceased:
                    other_interested = "Fallecido\n" + "Tomo: " + str(deceased_volume) + "\n Folio: " + str(
                        deceased_folio)
                else:
                    other_interested = "Condición migratoria: " + str(immigration_status)

                record.other_interested = other_interested

                country = self.env['res.country'].search([('code', '=', 'CU')], limit=1)
                record.country = country.id

                if state_name == 'Ciudad de la Habana':
                    state_name = 'La Habana'

                state = self.env['res.country.state'].search([('name', 'ilike', str(state_name))])
                record.country_states = state.id

                city = self.env['res.city'].search([('name', 'ilike', str(city_name)),
                                                    ('country_id', '=', int(country.id)),
                                                    ('state_id', '=', int(state.id))])
                record.city = city.id



                message = f"""
                                    <b>Consulta exitosa para CI: {self.identity}</b><br/>
                                    <b>Nombre:</b> {first_name} {second_name} {first_last_name} {second_last_name}<br/>
                                    <b>Sexo:</b> {sex}<br/>
                                    
                                    <b>Dirección:</b> {address}<br/>
                                    <b>Municipio:</b> {city_name}<br/>
                                    <b>Provincia:</b> {state_name}<br/>
                                    """

                if deceased:
                    print('el carnet sale fallecido!!!!!!!!!!!!!!')
                    raise exceptions.ValidationError('Carné de identidad registrado como fallecido en la FUC.'
                                                     'En caso de no ser correcto dicho dato diríjase a la entidad encargada de arreglar este error.')


                # return {
                #     'type': 'ir.actions.act_window',
                #     'name': 'Resultado de la Prueba',
                #     'res_model': 'fuc.result.wizard',
                #     'view_mode': 'form',
                #     'target': 'new',
                #     'context': {
                #         'default_message': message,
                #     }
                # }

            if not data:
                raise exceptions.ValidationError('Carné de identidad no registrado.')


        self.generate_request(record)

    def search_simulated_data(self, record):
        """Busca datos en el API simulado."""
        if record:
            record = self.env['professional_registers.professional_request_minimal'].browse(record)
        else:
            raise exceptions.ValidationError('No se puede buscar los datos .')

        if record.nationality_id.validate_fuc:
            # Registrar trazas
            model = self.env['ir.model'].search(
                [('model', '=', 'professional_registers.professional_request_minimal')])
            user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
            msg = 'Búsqueda por CI: ' + str(
                record.identity) + ' a la aplicación Registro del ciudadano para generación de solicitud.'
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': msg
            })

            # Limpiar campos
            self.clear_fields()
            variable = self.get_token()
            if variable == None:
                self.generate_token()

            # URL del API simulado en Flask
            url_base = 'http://127.0.0.1:5000/api/v1/nivel10?'
            identity = record.identity
            url = f"{url_base}identidad_numero={identity}"
            print(url)

            # # Configuración del proxy (modificar según corresponda)
            # proxy = "http://f.aguilar:Ing__00***@proxy.aicros.cu:3128"
            # proxies = {
            #     "http": proxy,
            #     "https": proxy,
            # }

            # Realizar la solicitud al API a través del proxy
            reintentos = 0
            response_ok = False
            headers = {'Authorization': f"Bearer {variable}", 'Accept': 'application/json'}
            data = []
            while reintentos < 3 and not response_ok:
                response = requests.get(url=url, headers=headers)
                if response.status_code == 200:
                    response = response.json()
                    data = [response]  # Simulamos una lista para mantener la estructura
                    response_ok = True
                else:
                    reintentos += 1
                    time.sleep(3)

            # Procesar los datos recibidos
            for r in data:
                record.flag_button = True
                record.id_fuc = r['id']
                record.identity = r['identidad_numero']
                name = r['primer_nombre']
                if r['segundo_nombre']:
                    name += ' ' + r['segundo_nombre']
                record.name = name
                record.first_last_name = r['primer_apellido']
                record.second_last_name = r['segundo_apellido']
                record.sex = 'female' if r['sexo'] == 'F' else 'male'
                record.address = r['direccion']

                other_interested = ""
                if r['fallecido']:
                    other_interested = "Fallecido\nTomo: " + str(r['defuncion_tomo']) + "\nFolio: " + str(
                        r['defuncion_folio'])
                else:
                    other_interested = "Condición migratoria: " + r['condicion_migratoria']
                record.other_interested = other_interested

                country = self.env['res.country'].search([('code', '=', 'CU')], limit=1)
                record.country = country.id

                state_name = 'La Habana' if r['provincia_residencia'] == 'Ciudad de la Habana' else r[
                    'provincia_residencia']
                state = self.env['res.country.state'].search([('name', 'ilike', state_name)])
                record.country_states = state.id

                city = self.env['res.city'].search([
                    ('name', 'ilike', r['municipio_residencia']),
                    ('country_id', '=', country.id),
                    ('state_id', '=', state.id)
                ])
                record.city = city.id

            if not data:
                raise exceptions.ValidationError(
                    'Carné de identidad no registrado. Para el caso de los residentes extranjeros aqui en cuba utilizar el numero de identificacion cubana')

        self.generate_request(record)

        # identification_number = self.identity if self.env['nomenclators.nationality'].search([('id', '=', self.nationality_id.id)]).validate_fuc else self.passport
        #
        # # Buscar el usuario por la identificacion o pasaporte
        # profile = self.env['professional_registers.profile'].search([('identity', '=', identification_number)])
        # if profile:
        #
        #     user = self.env['res.users'].search(
        #             [('id', '=', profile.user_id.id)])
        #     group_ids = user.groups_id
        #     for group in self.env['res.groups'].browse(group_ids):
        #
        #         # En caso de ser cliente online redirigir al wizard sobre la existencia de su usuario online
        #         if self.env["res.users"].has_group("security.group_professional_client_online"):
        #
        #             title = 'Petición Denegada!!!'
        #             message = f'Ya existe un usuario registrado en línea para este número de identidad. Debe continuar sus proceso de manera en línea.'
        #
        #             """Método para abrir el wizard con título, mensaje y función personalizados."""
        #             wizard = self.env['professional_registers.message_wizard'].sudo().create({
        #                 'title': title,
        #                 'message': message,
        #             })
        #
        #             return {
        #                 'name': title,
        #                 'type': 'ir.actions.act_window',
        #                 'res_model': 'professional_registers.message_wizard',
        #                 'view_mode': 'form',
        #                 'res_id': wizard.id,
        #                 'target': 'new',
        #                 'context': {
        #                     'target_model': 'professional_registers.profile',  # El modelo que contiene la función
        #                     'target_function': 'none',  # La función que deseas ejecutar
        #                     'profile': profile.id,
        #                     'no_action': True
        #                 },
        #             }
        #         # En caso de ser cliente redirigir al wizard sobre la existencia de sus solicitudes hechas
        #         if self.env["res.users"].has_group("security.group_professional_client"):
        #
        #             count = self.env['professional_registers.professional_request'].search_count(
        #                 [('identity', '=', identification_number)])
        #
        #             if count >= 1:
        #                 title = 'Existencia de solicitud!!!'
        #                 message = f'Ya existen {count} solicitudes realizadas para este número de identidad. Desea seguir generando otra solicitud ?' if count > 1 else f'Ya existe {count} solicitud realizada con este número de identidad. Desea seguir generando otra solicitud ?'
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
        #                         'target_function': 'generate_request',  # La función que deseas ejecutar
        #                         'profile': profile.id,  # Pasar el nombre de la función como cadena
        #                     },
        #                 }
        #
        # else:
        #     self.search_data()

    # Auxiliar
    def get_keys(self):
        keys = self.env['security.configure_keys'].search([], limit=1, order='id desc')
        if not keys:
            return False
        else:
            message = keys.key_1 + ':' + keys.key_2
            return message

    def get_token_url(self):
        keys = self.env['security.configure_keys'].search([], limit=1, order='id desc')
        return keys.url

    def get_url_base(self):
        keys = self.env['security.configure_keys'].search([], limit=1, order='id desc')
        return keys.url_base

    def update_token(self, token):
        os.environ['TOKEN_FICHA_UNICA'] = str(token)

    def validate_fuc(self, json_):
        keys = ['id', 'identidad_numero', 'primer_nombre', 'primer_apellido', 'sexo', 'edad', 'direccion',
                'municipio_residencia_cod_dpa', 'provincia_residencia_cod_dpa', 'nacimiento_fecha']
        for item in json_:
            for key in keys:
                if item.get(key) is None or item[key] == '':
                    return False
        return True

    def get_token(self):
        try:
            return os.environ.get('TOKEN_FICHA_UNICA')
        except Exception:
            raise exceptions.ValidationError(
                'Configure el token de la ficha única en las variables de entorno del sitema.')

    def get_full_name_password(self, record, request_number):
        name = ''
        if record.name:
            name = record.name
        if record.first_last_name:
            if name != '':
                name = name + ' ' + record.first_last_name
            else:
                name = record.first_last_name
        if record.second_last_name:
            if name != '':
                name = name + ' ' + record.second_last_name
            else:
                name = record.second_last_name

        full_name = name
        user = ''
        password = ''
        if record.name and record.first_last_name:
            first_letter = record.name[:1]
            user = first_letter + record.first_last_name + str(request_number)
            str_accent = unidecode(user)
            str_lower = str(str_accent).lower()
            user = str_lower

            str_empty = str(record.name).split(' ')
            password = record.name + '*123'
            if len(str_empty) > 1:
                password = ''.join(str_empty) + '*123'

        return full_name, user, password

    def get_default_state(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([('model', '=', int(model.id))], order="priority asc")
        if states:
            return states[0].id
        return 0

    def clear_fields(self):
        self.name = ''
        self.first_last_name = ''
        self.second_last_name = ''
        # self.identity = ''
        # self.passport = ''
        self.id_fuc = ''
        self.address = ''
        self.country = False
        self.country_states = False
        self.city = False
        self.sex = ''
        self.other_interested = ''

    @api.model
    def create(self, vals_list):

        requests = self.env['professional_registers.professional_request_minimal'].search([])
        request_number = 0
        if requests:
            older = 0
            for r in requests:
                value = int(r.request_number)
                if value > older:
                    older = value
            request_number = older + 1
        else:
            request_number = 1
        vals_list['request_number'] = request_number

        return super(ProfessionalRequestMinimal, self).create(vals_list)

    def validate_request_generation(self):

        suspended_procedures = self.env['nomenclators.procedure_types']._check_suspended_procedures()

        is_professional_request = None  # Valor por defecto si no se encuentra

        is_professional_request = next(
            (obj for obj in suspended_procedures if obj.procedure_type_id.name == "Solicitud de inscripción"), None)

        if suspended_procedures and is_professional_request:

            # reasons = "\n".join(
            #     reason.name  # Elemento individual de stop_reasons (debe ser string)
            #     for r in procedure_type.current_suspension_id  # Iterar sobre cada suspensión
            #     for reason in r.stop_reasons  # Iterar sobre cada razón en stop_reasons
            # )
            # # reasons = "\n".join([r.stop_reasons for r in procedure_type.current_suspension_id])
            #
            # raise exceptions.ValidationError(
            #     f"El proceso para el trámite {procedure_type.name} está actualmente detenido.\n"
            #     f"Motivos:\n{reasons}\n"
            #     f"Detenido el: {procedure_type.current_suspension_id.stop_date}\n"
            #     f"Por: {procedure_type.current_suspension_id.stopped_by.partner_id.name}"
            # )

            message_parts = []
            is_admin = self.env.user.has_group('base.group_system')

            header = "🚨 ALERTA DEL SISTEMA 🚨\n" + ("-" * 50) + "\n\n"

            if is_admin:
                header += "Como Administrador, se requiere su atención inmediata:\n\n"
            else:
                header += "Información importante sobre procesos detenidos:\n\n"

            for proc in suspended_procedures:
                reasons = ', '.join(proc.stop_reasons.mapped('name'))
                if is_admin:
                    message_parts.append(
                        f"📋 Trámite: {proc.procedure_type_id.name}\n"
                        f"📊 Estado: {'Detenido' if proc.state == 'stopped' else proc.state}\n"
                        f"❌ Motivos: {reasons}\n"
                        f"🕒 Fecha de Detención: {proc.stop_date.strftime('%d/%m/%Y %H:%M')}\n"
                        f"👤 Detenido por: {proc.stopped_by.name}\n"

                        # f"🔍 ID del Proceso: {proc.id}\n"
                        f"{'-' * 30}\n"
                    )
                else:
                    message_parts.append(
                        f"📋 Trámite: {proc.procedure_type_id.name}\n"
                        f"❌ Motivos: {reasons}\n"
                        f"🕒 Detenido desde: {proc.stop_date.strftime('%d/%m/%Y')}\n"
                        f"{'-' * 30}\n"
                    )

            footer = "\n"
            if is_admin:
                footer += "⚠️ Se requiere revisión y acción inmediata de estos procesos."
            else:
                footer += "⚠️ Por favor, tenga en cuenta estas detenciones al realizar sus operaciones."

            complete_message = header + ''.join(message_parts) + footer
            raise ValidationError(_(complete_message))
        else:
            return self.env['professional_registers.validator'].validate_generate_request(record=self,
                                                                                          view="generate_request_minimal")

# import json
#
# import base64
# from datetime import datetime
#
# import requests
# from django.utils.dateparse import parse_datetime
#
# from app import settings
# from rest_framework import status
#
# class FichaUnica:
#     # aqui va tu url base y la del token
#     url_base = '/api/v1/nivel10?'
#     url_token = 'https://apis-fuc.minjus.gob.cu/token'

#     @staticmethod
#     # esto es para refrescar el token


#     # este es el metodo para llamar
#     @classmethod
#     def request_to_level_10(cls, carnet=None, id_ficha=None):
#         data = list()
#         reintentos = 0
#         # message son tus dos llaves (variables) de la manera llave1:llave2
#         message = "llave1:llave2"
#         message_bytes = message.encode('ascii')
#         base64_bytes = base64.b64encode(message_bytes)
#         variableencode = base64_bytes.decode('ascii')
#         response_ok = False
#         grant = '?grant_type=client_credentials'
#         scope = '&scope=nivel0 nivel1 nivel2 nivel3 nivel4 nivel10'
#         url_token = f"{cls.url_token}{grant}{scope}"
#
#         headers = {'Authorization': f"Basic {variableencode}"}
#         response = requests.post(url=url_token, headers=headers)
#         variable = response.json()
#         variable = variable.get('access_token')
#
#         if id_ficha:
#             url = f"{cls.url_base}id={id_ficha}"
#         else:
#             url = f"{cls.url_base}identidad_numero={carnet}"
#         url = f"{cls.url_base}identidad_numero={carnet}"
#         headers = {'Authorization': f"Bearer {variable}", 'Accept': 'application/json'}
#         # print(headers)
#         while reintentos < 3 and not response_ok:
#             response = requests.get(url=url, headers=headers)
#
#             if response.status_code == status.HTTP_200_OK and cls.validar_ficha(response.json()):
#                 response = response.json()
#                 data = response
#                 response_ok = True
#             else:
#                 reintentos += 1
#                 time.sleep(3)
#
#         return data[0] if len(data) > 0 else {}
#
#     @staticmethod
#     def validar_ficha(json_):
#         keys = ['id', 'identidad_numero', 'primer_nombre', 'primer_apellido', 'sexo', 'edad', 'direccion',
#                 'municipio_residencia_cod_dpa', 'provincia_residencia_cod_dpa', 'nacimiento_fecha']
#         for item in json_:
#             for key in keys:
#                 if item.get(key) is None or item[key] == '':
#                     return False
#
#         return True

