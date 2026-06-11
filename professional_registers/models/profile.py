# -*- coding: utf-8 -*-
import random
import re
from email.policy import default

from odoo import models, fields, api, exceptions, _
from datetime import datetime
import os
import base64
import time
import requests
from lxml import etree
import passlib.context
from unidecode import unidecode

from odoo.exceptions import UserError, except_orm, ValidationError
from odoo.http import request

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'plaintext'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['plaintext'],
)

model_profile = 'professional_registers.profile'
model_users = 'res.users'


class Profile(models.Model):
    _name = 'professional_registers.profile'
    _description = 'Perfil'
    _rec_name = 'full_name'

    PHONE_MIN_LENGTH = 8
    PHONE_MAX_LENGTH = 15
    INTERNATIONAL_MIN_LENGTH = 7
    INTERNATIONAL_MAX_LENGTH = 15

    name = fields.Char('Nombre')
    first_last_name = fields.Char('Primer apellido')
    second_last_name = fields.Char('Segundo apellido')

    full_name = fields.Char('Nombre y apellidos')

    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")

    identity = fields.Char('CI o pasaporte')
    sex = fields.Selection([('male', 'Masculino'),
                            ('female', 'Femenino')], string="Sexo")

    address = fields.Text('Dirección particular')
    country = fields.Many2one('res.country', string="País")
    country_states = fields.Many2one('res.country.state', string="Provincia")
    city = fields.Many2one('res.city', string="Municipio")
    phone = fields.Char('Teléfono')
    email = fields.Char('Correo')

    teaching_level = fields.Many2one('nomenclators.teaching_level', string="Nivel de enseñanza")
    study_center = fields.Many2one('nomenclators.study_centers', string="Centro de estudio")

    degree_date = fields.Date('Fecha de graduación')
    convalidation_degree_tittle = fields.Date('Fecha convalidación de título exp en el extranjero')

    volume = fields.Char('Tomo')
    folio = fields.Char('Folio')
    number = fields.Char('Número')

    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    specialties = fields.Many2one('nomenclators.specialties', string="Especialidad")
    teaching_category = fields.Many2one('nomenclators.teaching_categories', string="Categoría docente")
    teaching_category_date = fields.Date('Fecha de categ. docente')
    investigations = fields.Boolean('Investigaciones')
    investigations_year = fields.Char('Año de la investigación')

    degree_sciences = fields.Selection([('anything', 'Ninguno'),
                                        ('esp', 'Esp.'),
                                        ('msc', 'Msc.'),
                                        ('dr', 'Dr.')], string="Grado científico")

    degree_sciences_year = fields.Char('Año de grado científico')
    unaicc_date = fields.Date('Fecha ingreso UNAICC')
    user = fields.Char('Usuario')
    password = fields.Char('Contraseña')

    image = fields.Image("Foto", max_width=1920, max_height=1920)
    date = fields.Date('Fecha Jubilación')
    retired = fields.Boolean('Jubilado', default=False, tracking=True)

    @api.onchange('retired')
    def _onchange_retired(self):
        if not self.retired:
            self.date = False

    user_id = fields.Many2one(model_users, string="Registrador")
    id_user_register = fields.Many2one('res.users', string="Usuario asociado")
    year = fields.Char('Año')

    attachment_ids = fields.Many2many('ir.attachment', string="Subir")

    history_work = fields.One2many('professional_registers.work_history', 'profile', string="Trayectoria laboral")
    professional_language = fields.One2many('nomenclators.professional_language', 'profile', string="Idioma")

    documents_required = fields.One2many('professional_registers.pr_document', 'profile',
                                         string="Documentos requeridos")

    id_fuc = fields.Char('Id FUC')
    observation = fields.Text('Observación')

    others_professions = fields.One2many('professional_registers.others_professions', 'profile',
                                         string="Otras profesiones")

    correct_info = fields.Boolean(string='Mis datos son correctos ', )
    wrong_info = fields.Boolean(string='Mis datos no son correctos ', )

    # Campos computados para las solicitudes
    request_count = fields.Integer(
        string='Cantidad de Solicitudes',
        compute='_compute_request_data',
        store=False
    )

    request_ids = fields.One2many(
        'professional_registers.professional_request',
        'profile_id',
        string='Solicitudes',
        compute='_compute_request_data',
        store=False
    )

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente')

    sync_inscriptions_automatically = fields.Boolean(
        'Sincronizar Inscripciones Automáticamente',
        default=True,
        help="Si está marcado, los cambios en el perfil se sincronizarán automáticamente con las inscripciones asociadas"
    )

    last_sync_date = fields.Datetime('Última Sincronización', readonly=True)

    @api.depends('identity')
    def _compute_request_data(self):
        for record in self:
            if record.identity:
                # Buscar solicitudes con el mismo identity y states en [3,6]
                requests = self.env['professional_registers.professional_request'].search([
                    ('identity', '=', record.identity),
                    ('profile_id', '=', self.id),
                    ('states', 'in', [3, 6]),
                    ('priority', 'in', [3, 6])
                ])

                record.request_count = len(requests)
                record.request_ids = requests
            else:
                record.request_count = 0
                record.request_ids = False

    def action_view_requests(self):
        """Abre la vista de solicitudes asociadas al perfil"""
        self.ensure_one()

        action = {
            'name': f'Solicitudes de {self.full_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'view_mode': 'tree,form',
            'domain': [('identity', '=', self.identity)],
            'context': {
                'default_identity': self.identity,

            }
        }

        return action

    @api.constrains('phone')
    def _check_phone(self):
        for record in self:
            if record.phone:
                phone = record.phone.strip()

                # Verificar que no esté vacío
                if not phone:
                    raise ValidationError("El teléfono no puede estar vacío.")

                # Patrón que permite + al inicio y caracteres comunes de formato
                phone_pattern = r'^\+?[0-9\s\-\(\)]+$'

                if not re.match(phone_pattern, phone):
                    raise ValidationError(
                        "Formato de teléfono inválido. Use solo números, + al inicio (opcional), "
                        "y caracteres de separación como espacios, guiones o paréntesis."
                    )

                # Limpiar el número (eliminar +, espacios, guiones, paréntesis)
                clean_phone = re.sub(r'[^\+0-9]', '', phone)
                digits_only = clean_phone.replace('+', '')

                # Validar longitud
                if clean_phone.startswith('+'):
                    # Número internacional
                    if len(digits_only) < self.INTERNATIONAL_MIN_LENGTH or len(
                            digits_only) > self.INTERNATIONAL_MAX_LENGTH:
                        raise ValidationError(
                            f"Número internacional inválido. Debe tener entre "
                            f"{self.INTERNATIONAL_MIN_LENGTH} y {self.INTERNATIONAL_MAX_LENGTH} dígitos "
                            f"después del código de país."
                        )
                else:
                    # Número local
                    if len(digits_only) < self.PHONE_MIN_LENGTH or len(digits_only) > self.PHONE_MAX_LENGTH:
                        raise ValidationError(
                            f"Número local inválido. Debe tener entre {self.PHONE_MIN_LENGTH} "
                            f"y {self.PHONE_MAX_LENGTH} dígitos.")

    @api.constrains('email')
    def _validate_email(self):
        for record in self:
            if record.email:
                # 1. Validación básica de formato
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', record.email):
                    raise ValidationError(
                        _('Formato de correo electrónico inválido. Ejemplo válido: usuario@dominio.com'))

                # # 2. Validación de dominios no permitidos
                # invalid_domains = ['gmail.com', 'yahoo.com', 'hotmail.com']  # Lista personalizable
                # domain = record.email.split('@')[-1].lower()
                # if domain in invalid_domains:
                #     raise ValidationError(
                #         _('No se permiten correos de dominios gratuitos. Use su correo institucional.'))

                # # 3. Validación de unicidad (opcional)
                # if self.search_count([('email', '=', record.email), ('id', '!=', record.id)]):
                #     raise ValidationError(_('Este correo electrónico ya está registrado por otro profesional'))

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Profile, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'password', 'image', 'attachment_ids',
                   'history_work', 'documents_required', 'user_id', 'user']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Profile, self).fields_view_get(view_id=view_id,
                                                   view_type=view_type,
                                                   toolbar=toolbar,
                                                   submenu=submenu)

        user = self.env['res.users'].search([('id', '=', self.env.uid)])
        profile = self.env['professional_registers.profile'].search([('user', '=', str(user.login))])
        simulated = False
        if not profile and simulated:
            self.search_simulated_data(user)
        else:
            if not profile:
                self.search_data(user)
        doc = etree.XML(res['arch'])

        res['arch'] = etree.tostring(doc)
        return res

    def func_correct_data(self):
        # Obtener el perfil
        profile = self.env['professional_registers.profile'].search(
            [('id', '=', self.env.context.get('profile') if self.env.context.get('profile') else self.id)])

        # Si todos los datos son correctos, actualizar los campos booleanos
        profile.correct_info = True
        profile.wrong_info = False

        # Obtener el form_id para el modal
        ir_model_data = self.env['ir.model.data']
        try:
            form_id = (
                ir_model_data.get_object_reference('professional_registers',
                                                   'request_wizard_wizard_form_view')[1])

            # Enviar notificación de éxito
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '¡Datos Completos!',
                    'message': 'Todos sus datos están correctos. Ya puede comenzar el proceso de generar solicitudes.',
                    'type': 'success',
                    'sticky': False,

                }
            }

            return notification
        except ValueError:
            form_id = False

    def func_wrong_data(self):
        self.wrong_info = True
        self.correct_info = False
        ir_model_data = self.env['ir.model.data']
        try:
            form_id = (
                ir_model_data.get_object_reference('professional_registers',
                                                   'cancel_request_wizard_wizard_form_view')[1])
        except ValueError:
            form_id = False
        ctx = {
            'profile': self.id,

        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.request_wizard',
            'name': 'Atención!!!!',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target': 'new',
            'clear_breadcrumbs': True,
            'context': ctx,
        }

    # Auxiliar
    def generate_request(self, record):

        profile = self.env['professional_registers.profile'].search(
            [('id', '=', self.env.context.get('profile') if self.env.context.get('profile') else record.id)])

        ir_model_data = self.env['ir.model.data']
        register_user_id = self.env['res.users'].search([('login', '=', 'RegOnline')]).id
        incription = False
        if self.env.context.get('profile'):
            profile_id = self.env.context.get('profile')
            profile = self.env['professional_registers.profile'].browse(profile_id)
            if profile.nationality_id.validate_fuc:
                incription = True

        if not profile:
            record = self.env['professional_registers.profile'].browse(record)

        request_number = self.env['professional_registers.professional_request'].get_request_number()
        request = self.env['professional_registers.professional_request'].with_context(
            creation_origin='profile'  # o 'request_minimal'
        ).create({
            'request_number': request_number,
            'name': record.name if not profile else profile.name,
            'first_last_name': record.first_last_name if not profile else profile.first_last_name,
            'second_last_name': record.second_last_name if not profile else profile.second_last_name,
            'full_name': record.full_name if not profile else profile.full_name,
            'nationality_id': record.nationality_id.id if not profile else profile.nationality_id.id,
            'identity': record.identity if not profile else profile.identity,
            'id_fuc': record.id_fuc if not profile else profile.id_fuc,
            'sex': record.sex if not profile else profile.sex,
            'address': record.address if not profile else profile.address,
            'country': record.country.id if not profile else profile.country.id,
            'country_states': record.country_states.id if not profile else profile.country_states.id,
            'city': record.city.id if not profile else profile.city.id,
            'user': record.user if not profile else profile.user,
            'user_id': register_user_id,
            'password': record.password if not profile else profile.password,
            'observation': record.observation if not profile else profile.observation,
            'register_type': 'register',
            'states': 1,
            'priority': 1,
            'is_inscription_fuc': profile.nationality_id.validate_fuc if profile else record.nationality_id.validate_fuc,
            'date_request': datetime.utcnow().date().today(),
            'is_register_online': True,
            'email': record.email if not profile else profile.email,
            'id_user_register': self.env.uid,
            'phone': record.phone if not profile else profile.phone,
            'image': record.image if not profile else profile.image,
            'history_work': record.history_work if not profile else profile.history_work,
            'procedure_type': self.env['professional_registers.professional_request'].get_procedure_default(),
            'retired': record.retired if not profile else profile.retired,
            'professional_language': record.professional_language if not profile else profile.professional_language,
        })
        msg = "Se ha generado la solicitud No: " + str(request.request_number)
        self.env.user.notify_warning(
            message=msg)

        model = self.env['ir.model'].search([('model', '=', str(model_profile))])
        user = self.env[model_users].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': f'Creacion de la solicitud {str(request.request_number)} .'
        })
        # try:
        #     form_id = (
        #         ir_model_data.get_object_reference('professional_registers', 'professional_request_form_view2')[1])
        # except ValueError:
        #     form_id = False
        #
        ctx = {
            'profile': record.id if not self.env.context.get('profile') else self.env.context.get('profile'),
            'id_request': request.id
        }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'professional_registers.professional_request',
        #     'name': 'Generar Solicitud',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'views': [(form_id, 'form')],
        #     'target': 'new',
        #     'context': ctx,
        # }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'name': 'Solicitud del profesional',
            'view_mode': 'form',
            'res_id': request.id,
            'target': 'main',
            'clear_breadcrumbs': True,
            'context': ctx,
        }


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


    def get_token(self):
        try:
            return os.environ.get('TOKEN_FICHA_UNICA')
        except Exception:
            raise exceptions.ValidationError(
                'Configure el token de la ficha única en las variables de entorno del sitema.')


    def get_url_base(self):
        keys = self.env['security.configure_keys'].search([], limit=1, order='id desc')
        return keys.url_base


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
        try:
            response = requests.post(url=url_token, headers=headers)
            variable = response.json()
            variable = variable.get('access_token')
            self.update_token(variable)
        except Exception:
            raise exceptions.AccessError('No hay conexión a la ficha del ciudadano')


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


    def get_full_name_password(self, request_number):
        name = ''
        if self.name:
            name = self.name
        if self.first_last_name:
            if name != '':
                name = name + ' ' + self.first_last_name
            else:
                name = self.first_last_name
        if self.second_last_name:
            if name != '':
                name = name + ' ' + self.second_last_name
            else:
                name = self.second_last_name

        full_name = name
        user = ''
        password = ''
        if self.name and self.first_last_name:
            first_letter = self.name[:1]
            user = first_letter + self.first_last_name + str(request_number)
            str_accent = unidecode(user)
            str_lower = str(str_accent).lower()
            user = str_lower

            str_empty = str(self.name).split(' ')
            password = self.name + '*123'
            if len(str_empty) > 1:
                password = ''.join(str_empty) + '*123'

        return full_name, user, password


    def create_profile(self, data, user):
        id_fuc = data[0]['id']
        identity = data[0]['identidad_numero']
        first_name = data[0]['primer_nombre']
        second_name = data[0]['segundo_nombre']
        first_last_name = data[0]['primer_apellido']
        second_last_name = data[0]['segundo_apellido']
        sex = data[0]['sexo']
        address = data[0]['direccion']
        city_name = data[0]['municipio_residencia']
        state_name = data[0]['provincia_residencia']
        deceased = data[0]['fallecido']
        deceased_volume = data[0]['defuncion_tomo']
        deceased_folio = data[0]['defuncion_folio']
        immigration_status = data[0]['condicion_migratoria']
        email = data[0]['email']

        name = first_name
        if second_name != None:
            name = str(name) + ' ' + str(second_name)

        full_name = name + ' ' + first_last_name + ' ' + second_last_name

        sex_name = 'male'
        if sex == 'F':
            sex_name = 'female'

        country = self.env['res.country'].search([('code', '=', 'CU')], limit=1)

        if state_name == 'Ciudad de la Habana':
            state_name = 'La Habana'

        state = False
        if state_name:
            state = self.env['res.country.state'].search([('name', 'ilike', str(state_name))])

        city = False
        if city_name and country and state:
            city = self.env['res.city'].search([('name', 'ilike', str(city_name)),
                                                ('country_id', '=', int(country.id)),
                                                ('state_id', '=', int(state.id))])
            self.city = city.id

        if deceased:
            other_interested = "Fallecido\n" + "Tomo: " + str(deceased_volume) + "\n Folio: " + str(deceased_folio)
        else:
            other_interested = "Condición migratoria: " + str(immigration_status)

        user_id = self.env['res.users'].search([('login', '=', 'RegOnline')]).id

        obj = self.env['professional_registers.profile'].create({
            'name': name,
            'first_last_name': first_last_name,
            'second_last_name': second_last_name,
            'full_name': full_name,
            'nationality_id': user.nationality_id.id,
            'identity': identity,
            'sex': sex_name,
            'number': '',
            'email': email,
            'address': address,
            'country': country.id if country else False,
            'country_states': state.id if state else False,
            'city': city.id if city else False,
            'user_id': user.id,
            'id_user_register': user_id ,
            'user': user.login,
            'id_fuc': id_fuc,
            'year': str(datetime.utcnow().date().today().year),
            'observation': other_interested,
            'password': ''
        })

        self.env['security.permits_state'].create({
            "user": user.id,
            "company": None,
            "user_id": 2,
            "create_uid": 2,
            "create_date": datetime.utcnow().date().today(),
            "write_uid": 2,
            "write_date": datetime.utcnow().date().today(),
            "in_process": True,
            "validation": False,
            "stop": False,
            "approved": False,
            "init_process": False,
            "cancel": False,
            "reset": False,
            "send_email": False,
            "denied": False,
            "cancel_inscription": False,
            "reset_inscription": False
        })


    def search_data(self, user):
        if user.nationality_id.validate_fuc:
            # Add traces
            model = self.env['ir.model'].search([('model', '=', 'professional_registers.profile')])
            msg = 'Búsqueda por CI: ' + str(
                user.identification) + ' a la aplicación Registro del ciudadano para comprabación de datos.'
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': msg
            })

            # 71012229259
            identity = user.identification

            # aqui va tu url base y la del token
            url_base = self.get_url_base()

            # message = "yaBXFT57XirizpO0TivSDiuIMnka:vcGhbLOKH9Vcb4BSKeOdXPYkcrUa"
            variable = self.get_token()
            if variable == None:
                self.generate_token()
            reintentos = 0
            response_ok = False
            url = f"{url_base}identidad_numero={identity}"
            headers = {'Authorization': f"Bearer {variable}", 'Accept': 'application/json'}
            data = []

            while reintentos < 3 and not response_ok:
                response = requests.get(url=url, headers=headers)
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

                data = []
                data.append({
                    'id': id,
                    'identidad_numero': identity,
                    'primer_nombre': first_name,
                    'segundo_nombre': second_name,
                    'primer_apellido': first_last_name,
                    'segundo_apellido': second_last_name,
                    'sexo': sex,
                    'email': user.partner_id.email,
                    'direccion': address,
                    'municipio_residencia': city_name,
                    'provincia_residencia': state_name,
                    'fallecido': deceased,
                    'defuncion_tomo': deceased_volume,
                    'defuncion_folio': deceased_folio,
                    'condicion_migratoria': immigration_status,
                })

                if deceased:
                    raise exceptions.ValidationError('Carné de identidad registrado como fallecido en la FUC.'
                                                     'En caso de no ser correcto dicho dato diríjase a la entidad encargada de arreglar este error.')

                self.create_profile(data, user)

            if not data:
                raise exceptions.ValidationError(
                    'Sus datos no están validados por la FUC. Debe dirigirse a la oficina más cercana de trámites para verificar su información.\n Para el caso de los residentes extranjeros aqui en cuba utilizar el numero de identificacion cubana ')
        else:
            data = []
            data.append({
                'id': False,
                'identidad_numero': user.identification,
                'primer_nombre': user.name,
                'segundo_nombre': None,
                'primer_apellido': user.first_last_name,
                'segundo_apellido': user.second_last_name,
                'sexo': '',
                'email': user.partner_id.email,
                'direccion': '',
                'municipio_residencia': False,
                'provincia_residencia': False,
                'fallecido': '',
                'defuncion_tomo': '',
                'defuncion_folio': '',
                'condicion_migratoria': '',
            })
            self.create_profile(data, user)


    def search_simulated_data(self, user):
        if user.nationality_id.validate_fuc:
            # Registro de trazabilidad
            model = self.env['ir.model'].search([('model', '=', 'professional_registers.profile')])
            msg = f'Búsqueda por CI: {user.identification} - Simulación de datos'
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': msg
            })

            identity = user.identification

            # aqui va tu url base y la del token
            url_base = self.get_url_base()

            # message = "yaBXFT57XirizpO0TivSDiuIMnka:vcGhbLOKH9Vcb4BSKeOdXPYkcrUa"
            variable = self.get_token()
            if variable == None:
                variable = self.generate_token()
            reintentos = 0
            response_ok = False
            url = f"{url_base}?identidad_numero={identity}"
            headers = {'Authorization': f"Bearer {variable}", 'Accept': 'application/json'}
            data = []

            while reintentos < 3 and not response_ok:
                response = requests.get(url=url, headers=headers)
                if response.status_code == 200:
                    response = response.json()
                    data = [response]
                    response_ok = True
                else:
                    reintentos += 1
                    time.sleep(3)

            for r in data:
                self.create_profile([{
                    'id': r['id'],
                    'identidad_numero': r['identidad_numero'],
                    'primer_nombre': r['primer_nombre'],
                    'segundo_nombre': r['segundo_nombre'],
                    'primer_apellido': r['primer_apellido'],
                    'segundo_apellido': r['segundo_apellido'],
                    'sexo': r['sexo'],
                    'email': user.partner_id.email,
                    'direccion': r['direccion'],
                    'municipio_residencia': r['municipio_residencia'],
                    'provincia_residencia': r['provincia_residencia'],
                    'fallecido': r['fallecido'],
                    'defuncion_tomo': r['defuncion_tomo'],
                    'defuncion_folio': r['defuncion_folio'],
                    'condicion_migratoria': r['condicion_migratoria'],
                }], user)
        else:
            data = [{
                'id': False,
                'identidad_numero': user.identification,
                'primer_nombre': user.name,
                'segundo_nombre': None,
                'primer_apellido': user.first_last_name,
                'segundo_apellido': user.second_last_name,
                'sexo': '',
                'email': user.partner_id.email,
                'direccion': '',
                'municipio_residencia': False,
                'provincia_residencia': False,
                'fallecido': '',
                'defuncion_tomo': '',
                'defuncion_folio': '',
                'condicion_migratoria': '',
            }]
            self.create_profile(data, user)


    def _crypt_context(self):
        """ Passlib CryptContext instance used to encrypt and verify
        passwords. Can be overridden if technical, legal or political matters
        require different kdfs than the provided default.

        Requires a CryptContext as deprecation and upgrade notices are used
        internally
        """
        return DEFAULT_CRYPT_CONTEXT


    def _set_password(self, password):
        ctx = self._crypt_context()
        hash_password = ctx.hash if hasattr(ctx, 'hash') else ctx.encrypt

        return hash_password(password)


    @api.model
    def create(self, vals_list):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', str(model_profile))])
        user = self.env[model_users].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de perfil satisfactoria.'
        })
        res = super(Profile, self).create(vals_list)
        return res


    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', str(model_profile))])
        user = self.env[model_users].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de perfil satisfactoria.'
        })
        # register user
        if vals.get('password'):
            user = self.user
            password = self._set_password(vals.get('password'))
            user_id = self.env[model_users].search([('login', '=', str(user))])
            user_id._set_encrypted_password(user_id.id, password)

        # Campos que triggerizan la sincronización
        sync_fields = [
            'name', 'first_last_name', 'second_last_name', 'full_name',
            'nationality_id', 'identity', 'sex', 'address', 'country',
            'country_states', 'city', 'phone', 'email', 'image',
            'retired', 'date', 'teaching_level', 'study_center',
            'profession', 'specialties', 'teaching_category',
            'degree_sciences', 'investigations'
        ]

        # Verificar si hay cambios en campos relevantes
        sync_needed = any(field in vals for field in sync_fields)

        res = super(Profile, self).write(vals)

        # Si hay cambios relevantes y la sincronización automática está activada
        if sync_needed and self.sync_inscriptions_automatically:
            if not self.env.context.get('skip_profile_sync'):
                for record in self:
                    record.with_context(from_profile_sync=True).sync_profile_to_inscriptions('profile')

        return res


    # def request_count_by_user(self):
    #
    #     suspended_procedures = self.env['nomenclators.procedure_types']._check_suspended_procedures()
    #
    #     is_professional_request = next(
    #         (obj for obj in suspended_procedures if obj.procedure_type_id.name == "Solicitud de inscripción"), None)
    #
    #     if self.correct_info:
    #
    #         if suspended_procedures and is_professional_request:
    #
    #             # reasons = "\n".join(
    #             #     reason.name  # Elemento individual de stop_reasons (debe ser string)
    #             #     for r in procedure_type.current_suspension_id  # Iterar sobre cada suspensión
    #             #     for reason in r.stop_reasons  # Iterar sobre cada razón en stop_reasons
    #             # )
    #             # # reasons = "\n".join([r.stop_reasons for r in procedure_type.current_suspension_id])
    #             #
    #             # raise exceptions.ValidationError(
    #             #     f"El proceso para el trámite {procedure_type.name} está actualmente detenido.\n"
    #             #     f"Motivos:\n{reasons}\n"
    #             #     f"Detenido el: {procedure_type.current_suspension_id.stop_date}\n"
    #             #     f"Por: {procedure_type.current_suspension_id.stopped_by.partner_id.name}"
    #             # )
    #
    #             message_parts = []
    #             is_admin = self.env.user.has_group('base.group_system')
    #
    #             header = "🚨 ALERTA DEL SISTEMA 🚨\n" + ("-" * 50) + "\n\n"
    #
    #             if is_admin:
    #                 header += "Como Administrador, se requiere su atención inmediata:\n\n"
    #             else:
    #                 header += "Información importante sobre procesos detenidos:\n\n"
    #
    #             for proc in suspended_procedures:
    #                 reasons = ', '.join(proc.stop_reasons.mapped('name'))
    #                 if is_admin:
    #                     message_parts.append(
    #                         f"📋 Trámite: {proc.procedure_type_id.name}\n"
    #                         f"📊 Estado: {'Detenido' if proc.state == 'stopped' else proc.state}\n"
    #                         f"❌ Motivos: {reasons}\n"
    #                         f"🕒 Fecha de Detención: {proc.stop_date.strftime('%d/%m/%Y %H:%M')}\n"
    #                         f"👤 Detenido por: {proc.stopped_by.name}\n"
    #
    #                         # f"🔍 ID del Proceso: {proc.id}\n"
    #                         f"{'-' * 30}\n"
    #                     )
    #                 else:
    #                     message_parts.append(
    #                         f"📋 Trámite: {proc.procedure_type_id.name}\n"
    #                         f"❌ Motivos: {reasons}\n"
    #                         f"🕒 Detenido desde: {proc.stop_date.strftime('%d/%m/%Y')}\n"
    #                         f"{'-' * 30}\n"
    #                     )
    #
    #             footer = "\n"
    #             if is_admin:
    #                 footer += "⚠️ Se requiere revisión y acción inmediata de estos procesos."
    #             else:
    #                 footer += "⚠️ Por favor, tenga en cuenta estas detenciones al realizar sus operaciones."
    #
    #             complete_message = header + ''.join(message_parts) + footer
    #             raise ValidationError(_(complete_message))
    #         else:
    #             return self.env['professional_registers.validator'].validate_generate_request(record=self,
    #                                                                                           view="profile")
    #     elif suspended_procedures:
    #         raise exceptions.ValidationError(
    #             f"Para continuar con el proceso para el trámite {suspended_procedures[0].procedure_type_id.name} debe confirmar que sus datos estan correctos!!!.\n"
    #
    #         )
    #     else:
    #         raise exceptions.ValidationError(
    #             f"Para continuar con el proceso debe confirmar que sus datos estan correctos!!!.\n"
    #
    #         )

    def _check_incomplete_profile(self, profile):
        """
        Verifica si el perfil tiene campos incompletos.
        Retorna True si hay campos incompletos (incorrecto), False si está completo (correcto).
        """
        # Verificar campos que pueden ser None o vacíos
        incomplete_fields = [
            profile.image,
            profile.name,
            profile.first_last_name,
            profile.second_last_name,
            profile.nationality_id,
            profile.identity,
            profile.sex,
            profile.address,
            profile.country,
            profile.country_states,
            profile.city,
            profile.email
        ]

        # Verificar si alguno es None o vacío
        for field in incomplete_fields:
            if not field:  # Esto cubre None, False, 0, "", [], {}, etc.
                return True  # Hay campos incompletos

        return False  # Todos los campos están completos


    def _check_changes_in_profile(self):
        """
        Verifica si el perfil tiene campos incompletos.
        Retorna True si hay campos incompletos (incorrecto), False si está completo (correcto).
        """
        # Verificar campos que pueden ser None o vacíos
        incomplete_fields = [
            self.image,
            self.name,
            self.first_last_name,
            self.second_last_name,
            self.nationality_id,
            self.identity,
            self.sex,
            self.address,
            self.country,
            self.country_states,
            self.city,
            self.phone,
            self.email
        ]

        # Verificar si alguno es None o vacío
        for field in incomplete_fields:
            if not field:  # Esto cubre None, False, 0, "", [], {}, etc.
                return True  # Hay campos incompletos

        return False  # Todos los campos están completos


    def create_update_request(self):
        self.ensure_one()

        # Buscar la solicitud de inscripción asociada
        request = self.env['professional_registers.professional_request'].search([
            '&',  # AND
            '|',  # OR
            ('identity', '=', self.identity),
            ('profile_id', '=', self.id),
            ('states', 'in', [3, 6])
        ], limit=1)

        if not request:
            raise exceptions.ValidationError('No existe una solicitud de inscripción aprobada para este perfil.')

            # Abrir un wizard para seleccionar el tipo de actualización
        return {
            'name': 'Crear Solicitud de Actualización',
            'type': 'ir.actions.act_window',
            'res_model': 'professional.update.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_profile_id': self.id,

            }
        }


    def sync_profile_to_inscriptions(self, source_type='manual', source_model=None, source_id=None):
        """Sincroniza el perfil con inscripciones y solicitudes asociadas"""
        self.ensure_one()

        # Sincronizar inscripciones (código existente)
        inscription_count = self._sync_inscriptions(source_type, source_model, source_id)

        # Sincronizar solicitudes
        request_count = self._sync_requests(source_type, source_model, source_id)

        # Actualizar fecha de última sincronización
        self.write({'last_sync_date': fields.Datetime.now()})

        # Registrar evento combinado
        details = []
        if inscription_count > 0:
            details.append(f"Inscripciones actualizadas: {inscription_count}")
        if request_count > 0:
            details.append(f"Solicitudes actualizadas: {request_count}")

        log_vals = {
            'profile_id': self.id,
            'source_model': source_model or 'professional_registers.profile',
            'source_id': source_id or self.id,
            'inscriptions_updated': inscription_count + request_count,
            'details': "\n".join(details) if details else "No se detectaron cambios",
            'sync_type': source_type,
        }

        self.env['professional_registers.profile_sync_log'].create(log_vals)

        return inscription_count + request_count


    def _sync_inscriptions(self, source_type, source_model, source_id):
        """Sincroniza el perfil con las inscripciones asociadas"""
        # Campos que se sincronizarán
        sync_fields = {
            'name': self.name,
            'first_last_name': self.first_last_name,
            'second_last_name': self.second_last_name,
            'full_name': self.full_name,
            'nationality_id': self.nationality_id.id if self.nationality_id else False,
            'identity': self.identity,

            'email': self.email,
            'image': self.image,

        }

        # Obtener todas las inscripciones asociadas a este perfil
        inscriptions = self.env['professional_registers.inscription'].search([
            ('identity', '=', self.identity)
        ])

        updated_count = 0
        details = []

        for inscription in inscriptions:
            # Preparamos los valores a actualizar, solo si han cambiado
            vals_to_update = {}
            changes = []

            for field, value in sync_fields.items():
                current_value = getattr(inscription, field)
                # Para campos Many2one, comparamos los IDs
                if isinstance(inscription._fields[field], fields.Many2one):
                    current_id = current_value.id if current_value else False
                    if current_id != value:
                        vals_to_update[field] = value
                        changes.append(f"{field}: {current_value} -> {value}")
                else:
                    if current_value != value:
                        vals_to_update[field] = value
                        changes.append(f"{field}: {current_value} -> {value}")

            # Si hay cambios, actualizamos la inscripción
            if vals_to_update:
                inscription.write(vals_to_update)
                updated_count += 1
                details.append(f"Inscripción {inscription.inscription_number}: {', '.join(changes)}")

        return updated_count


    def _sync_requests(self, source_type, source_model, source_id):
        """Sincroniza el perfil con las solicitudes asociadas que no estén en estado 3 o 6"""
        # Campos que se sincronizarán
        sync_fields = {
            'name': self.name,
            'first_last_name': self.first_last_name,
            'second_last_name': self.second_last_name,
            'full_name': self.full_name,
            'nationality_id': self.nationality_id.id if self.nationality_id else False,
            'identity': self.identity,
            'id_fuc': self.id_fuc,
            'sex': self.sex,
            'address': self.address,
            'country': self.country.id if self.country else False,
            'country_states': self.country_states.id if self.country_states else False,
            'city': self.city.id if self.city else False,
            'phone': self.phone,
            'email': self.email,
            'image': self.image,
            'retired': self.retired,
            'date': self.date,

        }

        # Obtener solicitudes asociadas que no estén en estado 3 (validación) ni 6 (aprobada)
        requests = self.env['professional_registers.professional_request'].search([
            ('identity', '=', self.identity),
            ('priority', 'not in', [3, 6])  # Excluir estados 3 y 6
        ])

        updated_count = 0
        details = []

        for request in requests:
            # Preparamos los valores a actualizar, solo si han cambiado
            vals_to_update = {}
            changes = []

            for field, value in sync_fields.items():
                current_value = getattr(request, field)
                # Para campos Many2one, comparamos los IDs
                if isinstance(request._fields[field], fields.Many2one):
                    current_id = current_value.id if current_value else False
                    if current_id != value:
                        vals_to_update[field] = value
                        changes.append(f"{field}: {current_value} -> {value}")
                else:
                    if current_value != value:
                        vals_to_update[field] = value
                        changes.append(f"{field}: {current_value} -> {value}")

            # Si hay cambios, actualizamos la solicitud
            if vals_to_update:
                request.write(vals_to_update)
                updated_count += 1
                details.append(f"Solicitud {request.request_number}: {', '.join(changes)}")

        return updated_count


    def action_manual_sync(self):
        """Acción para sincronizar manualmente"""
        updated_count = self.sync_profile_to_inscriptions('manual')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': f'Se han sincronizado {updated_count} inscripciones.',
                'type': 'success',
                'sticky': False,
            }
        }


    def abrir_wizard_prueba(self):
        # Validación de campos requeridos

        ir_model_data = self.env['ir.model.data']
        try:
            form_id = ir_model_data.get_object_reference(
                'professional_registers',
                'request_wizard_wizard_form_view'
            )[1]
        except ValueError:
            form_id = False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.request_wizard',
            'name': 'Atención!!!!',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target': 'new',
            'clear_breadcrumbs': True,
        }


    def _validate_profile_for_request(self, profile):
        """
        Valida si el perfil puede generar una solicitud.
        Returns:
            dict: {
                'valid': bool,
                'error_type': str ('incomplete', 'suspended', 'unconfirmed'),
                'message': str (opcional),
                'can_proceed_with_wizard': bool
            }
        """
        # 1. ¿Datos incompletos?
        if self._check_incomplete_profile(profile):
            return {
                'valid': False,
                'error_type': 'incomplete',
                'can_proceed_with_wizard': True,  # ✅ Sí, abre wizard para completar
            }

        # 2. ¿Datos no confirmados?
        if not profile.correct_info:
            return {
                'valid': False,
                'error_type': 'unconfirmed',
                'message': _("Debe confirmar que sus datos son correctos."),
                'can_proceed_with_wizard': False,
            }

        # 3. ¿Procesos detenidos?
        suspended = self.env['nomenclators.procedure_types']._check_suspended_procedures()
        is_inscription_suspended = any(
            p.procedure_type_id.name == "Solicitud de inscripción" for p in suspended
        )
        if suspended and is_inscription_suspended:
            # Generar mensaje como en tu código
            is_admin = self.env.user.has_group('base.group_system')
            header = _("🚨 ALERTA: Procesos detenidos.\n")
            if is_admin:
                header += _("Requiere su atención inmediata.\n")
            else:
                header += _("No puede continuar hasta resolver las detenciones.\n")

            return {
                'valid': False,
                'error_type': 'suspended',
                'message': header,
                'can_proceed_with_wizard': False,
            }

        # ✅ Todo OK
        return {'valid': True}


    def action_generate_request(self):
        """Método llamado directamente desde el botón."""
        # Obtener perfil (ajusta según tu lógica)
        profile = self  # si self es un record de profile
        # O si viene de contexto:
        # profile_id = self.env.context.get('profile')
        # profile = self.env['professional_registers.profile'].browse(profile_id) if profile_id else self

        validation = self._validate_profile_for_request(profile)

        if validation['valid']:
            # ✅ Crear solicitud
            return self.env['professional_registers.validator'].validate_generate_request(record=self,
                                                                                          view="profile")

        elif validation['can_proceed_with_wizard']:
            # ✅ Abrir wizard para completar datos
            return self._open_incomplete_profile_wizard(profile)

        else:
            # ❌ Mostrar error bloqueante
            raise ValidationError(validation.get('message', _("No se puede continuar.")))


    def _open_incomplete_profile_wizard(self, profile):
        try:
            form_view = self.env.ref('professional_registers.request_wizard_wizard_form_view')
        except ValueError:
            form_view = None

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.request_wizard',
            'name': _('Atención!!!!'),
            'view_mode': 'form',
            'view_id': form_view.id if form_view else False,
            'target': 'new',
            'context': {'default_profile_id': profile.id},
            'clear_breadcrumbs': True,
        }
