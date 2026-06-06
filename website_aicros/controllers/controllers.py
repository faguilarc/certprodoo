# -*- coding: utf-8 -*-
import base64
import json
import time

import requests
from werkzeug.exceptions import NotFound

from odoo import http, exceptions, _
from odoo.exceptions import AccessError, MissingError, _logger
from odoo.http import request, content_disposition, serialize_exception
from datetime import datetime
import werkzeug

model_user = 'res.users'


class WebsiteAicros(http.Controller):

    @http.route('/web/register_user', type='http', auth='public', methods=['POST', 'GET'], csrf=False, website=True)
    def register_user(self, **kw):
        error_message = None
        if request.httprequest.method == 'POST':
            try:
                is_create_user = self.create_user(**kw)
                if is_create_user:
                    # Éxito - redirigir a login con mensaje
                    return werkzeug.utils.redirect('/web/login?success=Usuario registrado satisfactoriamente')

            except exceptions.ValidationError as e:
                error_message = str(e)
                _logger.warning("Error de validación en registro de usuario: %s", error_message)
                # Renderizar template de error modal
                return request.render("website_aicros.registration_error_modal", {
                    'error_message': error_message
                })

            except Exception as e:
                error_message = "Ha ocurrido un error inesperado. Por favor, intente nuevamente."
                _logger.error("Error inesperado en registro de usuario: %s", str(e))
                return request.render("website_aicros.registration_error_modal", {
                    'error_message': error_message
                })

        # GET request - mostrar formulario normal
        nationalities = http.request.env['website_model'].get_nationalities()
        values = {
            'nationalities': nationalities,
            'name': kw.get('name', ''),
            'first_lastname': kw.get('first_lastname', ''),
            'second_lastname': kw.get('second_lastname', ''),
            'identification': kw.get('identification', ''),
            'selected_nationality': kw.get('nationalities', ''),
            'email': kw.get('email', ''),
            'user': kw.get('user', ''),
        }
        return http.request.render("website_aicros.register_user_form", values)

    @http.route('/web/cancel', type='http', auth='public', methods=['GET'], csrf=False, website=True)
    def cancel(self, **kw):
        return http.request.render("web.login")

    @http.route(['/home'], type='http', auth="public", website=True, csrf=False, cors='*')
    def service_request(self, **kw):
        show = False
        register_list = []
        if kw:
            show = True
            register_list = http.request.env['website_model'].get_register_inscription(kw)

        professions = http.request.env['website_model'].get_professions()
        nationalities = http.request.env['website_model'].get_nationalities()
        specialties = http.request.env['website_model'].get_specialties()
        structures = http.request.env['website_model'].get_str_structure()
        enrrolls = http.request.env['website_model'].get_str_inscription()
        normative = http.request.env['website_model'].get_str_normative()
        documents = http.request.env['website_model'].get_str_relations_documents()

        total_registers = len(register_list)

        values = {
            'professions': professions,
            'nationalities': nationalities,
            'specialties': specialties,
            'structures': structures,
            'enrrolls': enrrolls,
            'normative_str': normative,
            'documents_str': documents,
            'attachment': normative.attachment_ids,
            'show': show,
            'structure': show,
            'inscription': show,
            'normative': show,
            'documents': show,
            'register_list': register_list,
            'total_registers': total_registers
        }
        return http.request.render("website_aicros.request_form", values)

    @http.route(['/structure'], type='http', auth="public", website=True, csrf=False)
    def service_structure(self, **kw):
        values = {
            'show': True,
            'structure': False,
            'inscription': True,
            'normative': True,
            'documents': True,
        }
        return http.request.render("website_aicros.structure_form", values)

    @http.route(['/inscription'], type='http', auth="public", website=True, csrf=False)
    def service_insription(self, **kw):
        values = {
            'show': True,
            'structure': True,
            'inscription': False,
            'normative': True,
            'documents': True,
        }
        return http.request.render("website_aicros.who_form", values)

    @http.route(['/documents'], type='http', auth="public", website=True, csrf=False)
    def service_documents(self, **kw):
        values = {
            'show': True,
            'structure': True,
            'inscription': True,
            'normative': True,
            'documents': False,
        }
        return http.request.render("website_aicros.documents_form", values)

    @http.route(['/normative'], type='http', auth="public", website=True, csrf=False)
    def service_normative(self, **kw):
        values = {
            'show': True,
            'structure': True,
            'inscription': True,
            'normative': False,
            'documents': True,
        }
        return http.request.render("website_aicros.marco_form", values)

    def _set_password(self, user, password):
        ctx = request.env[model_user].sudo()._crypt_context()
        self._set_encrypted_password(user, ctx.hash(password))

    def _set_encrypted_password(self, uid, pw):
        request.env.cr.execute(
            'UPDATE res_users SET password=%s WHERE id=%s',
            (pw, uid)
        )

    def create_user(self, **post):

        # self.validate_registration_data_simulated(**post)

        self.validate_registration_data(**post)
        print(post)
        password = post.get('password', '')
        confirm_password = post.get('confirm_password', '')

        if password != '' and confirm_password != '' and password != confirm_password:
            raise exceptions.ValidationError('Las contraseñas no coinciden')

        user = post.get('user', '')
        exist = request.env[model_user].sudo().search(
            [('login', '=', str(user)), '|', ('active', '=', True), ('active', '=', False)])
        if exist:
            raise exceptions.ValidationError('El usuario no esta disponible. Ya esta siendo utilizado en el sistema')

        name = post.get('name', False)
        email = post.get('email', False)
        first_lastname = post.get('first_lastname', False)
        second_lastname = post.get('second_lastname', False)
        identification = post.get('identification', False)

        exist_identification = request.env[model_user].sudo().search(
            [('identification', '=', str(identification))])
        if exist_identification:
            raise exceptions.ValidationError('El CI o pasaporte ya fue registrado en el sistema')

        nationalities = post.get('nationalities', False)

        if nationalities == '':
            raise exceptions.ValidationError('No se puede registrar el usuario. Debe seleccionar una nacionalidad')

            # ✅ Validar si la nacionalidad requiere FUC (CI de 11 dígitos)
        nationality = request.env['nomenclators.nationality'].sudo().browse(int(nationalities))
        identification = post.get('identification', '').strip()

        if nationality.validate_fuc:
            if not identification.isdigit() or len(identification) != 11:
                raise exceptions.ValidationError(
                    "Los ciudadanos de nacionalidad '%s' deben registrar un Carné de Identidad válido (11 dígitos numéricos)." % nationality.name
                )
        else:
            # Para no cubanos: mínimo 2 caracteres (pasaporte, etc.)
            if len(identification) < 2:
                raise exceptions.ValidationError("El CI o pasaporte debe tener al menos 2 caracteres.")

        cr = request.env.cr

        fullname = ' '.join(filter(None, [name, first_lastname, second_lastname]))

        # Creo PArtner activado
        data_partner = {
            'active': True,
            'type': 'contact',
            "name": name,
            "display_name": fullname,
            "email": email,
            'lang': "es_ES",
            'color': 0,
        }

        sql_insert = "INSERT INTO public.res_partner ({}) VALUES ({}) RETURNING id".format(
            ', '.join(data_partner.keys()),
            ', '.join(['%s'] * len(data_partner))
        )
        cr.execute(sql_insert, tuple(data_partner.values()))
        partner_id = cr.fetchone()[0]

        # Creo user activado
        data_user = {
            'active': True,
            'partner_id': partner_id,
            'notification_type': 'email',
            "login": user,
            "share": False,
            "company_id": request.env.company.id,
            "full_name": fullname,
            "first_last_name": first_lastname,
            "second_last_name": second_lastname,
            "identification": identification,
            "nationality_id": int(nationalities),
            "create_date": datetime.utcnow(),
            "user_type": 'client',
            'sidebar_type': 'large',
            'chatter_position': 'sided'
        }

        sql_insert = "INSERT INTO public.res_users ({}) VALUES ({}) RETURNING id".format(
            ', '.join(data_user.keys()),
            ', '.join(['%s'] * len(data_user))
        )
        cr.execute(sql_insert, tuple(data_user.values()))
        print(cr)
        user_id = cr.fetchone()[0]

        self._set_password(user_id, password)

        group = request.env['res.groups'].sudo().search([('name', '=', 'Cliente Online')], limit=1)
        print(group)
        query = """
        INSERT INTO public.res_groups_users_rel(gid, uid) VALUES 
        (""" + str(group.id) + """,""" + str(user_id) + """)"""
        cr.execute(query)

        sql_insert = f"""
        INSERT INTO public.res_company_users_rel(cid, user_id)VALUES ({request.env.company.id}, {user_id});
        """
        cr.execute(sql_insert)

        sql_select = """SELECT id FROM res_groups WHERE name = 'Internal User'"""
        cr.execute(sql_select)
        group_id = cr.fetchone()[0]

        sql_insert = "INSERT INTO public.res_groups_users_rel(gid, uid) VALUES (%s, %s)"
        cr.execute(sql_insert, (group_id, user_id))

        return True

    @http.route('/web/get_specialties', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def get_specialties(self, **kwargs):
        profession_id = request.params.get('profession_id')

        # Verificamos si profession_id contiene la palabra "Profesión"
        if profession_id and "Todas" not in profession_id:
            try:
                profession_id = int(profession_id)  # Convertir a entero si es válido
            except ValueError:
                # Manejo del error si no se puede convertir a entero
                return request.make_response(json.dumps({'error': 'ID de profesión inválido'}),
                                             headers={'Content-Type': 'application/json'})

            # Buscar las especialidades relacionadas con la profesión
            specialties = request.env['nomenclators.specialties'].sudo().search([('profession_id', '=', profession_id)],
                                                                                order='name asc')
            return request.make_response(
                json.dumps([{'id': specialty.id, 'name': specialty.name} for specialty in specialties]),
                headers={'Content-Type': 'application/json'}
            )
        else:
            # Si la palabra "Profesión" está presente o no se proporciona un ID válido, va al else
            specialties = request.env['nomenclators.specialties'].sudo().search([], order='name asc')

            return request.make_response(
                json.dumps([{'id': specialty.id, 'name': specialty.name} for specialty in specialties]),
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/professional/public/check/<int:record_id>', type='json', auth='public')
    def check_public_availability(self, record_id):
        public_config = request.env['professional_registers.public_request'].sudo().search_count([
            ('request_id', '=', record_id)
        ])
        return {'available': bool(public_config)}

    @http.route('/web/get_category_fields', type='json', auth='user')
    def get_category_fields(self, category):
        PublicField = request.env['professional_registers.public_field'].sudo()
        fields = PublicField.get_fields_by_category(category)
        return fields

    @http.route(['/professional/public/view/<int:record_id>'], type='http', auth='public', website=True)
    def professional_public_view(self, record_id, **kw):
        try:
            # Verificar si el profesional existe
            professional = request.env['professional_registers.professional_request'].sudo().browse(record_id)
            if not professional.exists():
                return request.render("website.page_404")

            # Obtener configuración pública
            public_config = request.env['professional_registers.public_request'].sudo().search([
                ('request_id', '=', record_id)
            ], limit=1)

            # Campos visibles por categoría
            visible_fields = {
                'personal': [],
                'contact': [],
                'academic': [],
                'professional': [],
                'work': False,
                'language': False,
                'documents': False
            }

            # Mapear campos visibles
            if public_config.show_name:
                visible_fields['personal'].append('name')
            if public_config.show_first_last_name:
                visible_fields['personal'].append('first_last_name')
            if public_config.show_second_last_name:
                visible_fields['personal'].append('second_last_name')
            if public_config.show_nationality_id:
                visible_fields['personal'].append('nationality_id')
            if public_config.show_identity:
                visible_fields['personal'].append('identity')
            if public_config.show_sex:
                visible_fields['personal'].append('sex')
            if public_config.show_image:
                visible_fields['personal'].append('image')

            if public_config.show_phone:
                visible_fields['contact'].append('phone')
            if public_config.show_email:
                visible_fields['contact'].append('email')
            if public_config.show_address:
                visible_fields['contact'].append('address')
            if public_config.show_country:
                visible_fields['contact'].append('country')
            if public_config.show_country_states:
                visible_fields['contact'].append('country_states')
            if public_config.show_city:
                visible_fields['contact'].append('city')

            if public_config.show_teaching_level:
                visible_fields['academic'].append('teaching_level')
            if public_config.show_study_center:
                visible_fields['academic'].append('study_center')
            if public_config.show_degree_date:
                visible_fields['academic'].append('degree_date')
            if public_config.show_volume:
                visible_fields['academic'].append('volume')
            if public_config.show_folio:
                visible_fields['academic'].append('folio')
            if public_config.show_number:
                visible_fields['academic'].append('number')

            if public_config.show_profession:
                visible_fields['professional'].append('profession')
            if public_config.show_specialties:
                visible_fields['professional'].append('specialties')
            if public_config.show_teaching_category:
                visible_fields['professional'].append('teaching_category')
            if public_config.show_teaching_category_date:
                visible_fields['professional'].append('teaching_category_date')
            if public_config.show_degree_sciences:
                visible_fields['professional'].append('degree_sciences')
            if public_config.show_degree_sciences_year:
                visible_fields['professional'].append('degree_sciences_year')
            if public_config.show_unaicc_date:
                visible_fields['professional'].append('unaicc_date')

            visible_fields['work'] = public_config.show_history_work
            visible_fields['language'] = public_config.show_professional_language

            # Documentos requeridos públicos
            required_docs = public_config.show_required_documents

            # Buscar documentos asociados a esta solicitud y documento requerido
            pr_documents = request.env['professional_registers.pr_document'].sudo().search([
                ('request', '=', professional.id),
                ('documents', 'in', required_docs.ids)
            ])

            # Obtener todos los adjuntos vinculados a esos documentos
            attachments = pr_documents.mapped('attachment_ids').filtered(lambda a: a.datas)

            visible_fields['documents'] = bool(attachments)

            # Caso 1: No existe configuración pública
            if not public_config:
                return request.render("website_aicros.professional_not_available", {
                    'message': _('Este profesional no ha habilitado su información pública')
                })

            # Caso 2: Existe configuración pero todos los campos están vacíos/desactivados
            all_empty = (
                    not any(visible_fields['personal']) and
                    not any(visible_fields['contact']) and
                    not any(visible_fields['academic']) and
                    not any(visible_fields['professional']) and
                    not visible_fields['work'] and
                    not visible_fields['language'] and
                    not visible_fields['documents']
            )

            if all_empty:
                return request.render("website_aicros.professional_not_available", {
                    'message': _('El profesional no ha compartido información pública')
                })

            return request.render('website_aicros.professional_public_details', {
                'professional': professional,
                'visible_fields': visible_fields,
                'public_documents': attachments
            })



        except Exception as e:
            # Registrar error y mostrar página genérica
            _logger.error("Error al cargar profesional público: %s", str(e))
            return request.render("website.page_500")

    def _is_cuban_nationality(self, nationality_id):
        """Verifica si la nacionalidad es Cuba."""
        if not nationality_id:
            return False
        nationality = request.env['nomenclators.nationality'].sudo().browse(int(nationality_id))
        check = nationality.name == 'Cubano'
        return check  # Ajusta si el nombre es "Cubana", etc.

    def _validate_cuban_id(self, identification, nationality_id):
        """Valida que los cubanos usen CI de 11 dígitos numéricos."""
        if self._is_cuban_nationality(nationality_id):
            if not (identification.isdigit() and len(identification) == 11):
                raise exceptions.ValidationError(
                    "Los ciudadanos cubanos deben registrar su Carné de Identidad (11 dígitos numéricos)."
                )
        elif not (len(identification) >= 6 and len(identification) <= 11) :
            raise exceptions.ValidationError(
                "Los ciudadanos extranjeros deben registrar su Pasaporte (6-11 dígitos numéricos y letras)."
            )

    def _check_existing_email_or_identification(self, email, identification):
        """Valida que email y CI/pasaporte no estén en uso."""
        user_model = request.env['res.users'].sudo()
        if user_model.search(
                [('identification', '=', identification), '|', ('active', '=', True), ('active', '=', False)]):
            raise exceptions.ValidationError("Este CI o pasaporte ya está registrado.")
        if user_model.search([('email', '=', email), '|', ('active', '=', True), ('active', '=', False)]):
            raise exceptions.ValidationError("Este correo electrónico ya está registrado.")

    def _check_and_generate_login(self, base_login):
        """Verifica si el login existe y sugiere alternativas."""
        user_model = request.env['res.users'].sudo()
        login = base_login

        # Verificar si el login original ya existe
        existing_user = user_model.search([('login', '=', login), '|', ('active', '=', True), ('active', '=', False)])

        if existing_user:
            raise exceptions.ValidationError(
                f"El nombre de usuario '{login}' ya está en uso. "
                f"Por favor, elige un nombre de usuario diferente."
            )

        return login

    def _validate_with_fuc(self, identification, is_simulated=False):
        """
        Valida el CI contra la FUC.
        - is_simulated=True → usa localhost:5000
        - is_simulated=False → usa URL real configurada
        """
        # Obtener configuración base
        keys = request.env['security.configure_keys'].sudo().search([], limit=1, order='id desc')
        if is_simulated:
            url_base = "http://localhost:5000/api/v1/nivel10?"
        else:
            if not keys or not keys.url_base:
                raise exceptions.ValidationError(_(
                    "Configuración incompleta: No se ha configurado la URL base del servicio de validación FUC. "
                    "Contacte al administrador del sistema."
                ))
            url_base = keys.url_base

        url = f"{url_base}identidad_numero={identification}"
        headers = {'Accept': 'application/json'}

        # Solo para producción se añade token
        if not is_simulated:
            token = self._generate_fuc_token()  # Esta función debe lanzar ValidationError si falla
            headers['Authorization'] = f"Bearer {token}"

        # Configuración de reintentos
        max_retries = 3
        retry_delay = 1  # segundos

        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                _logger.info("Validación FUC (intento %d/%d) para CI: %s", attempt, max_retries, identification)
                response = requests.get(url, headers=headers, timeout=10)  # timeout añadido

                # Manejo de códigos de estado HTTP
                if response.status_code == 200:
                    data = response.json()
                    # Validar estructura mínima (esperamos lista con un diccionario)
                    if (isinstance(data, list) and len(data) > 0 and
                            isinstance(data[0], dict) and
                            data[0].get('identidad_numero') == identification):
                        # Verificar si la persona está fallecida
                        if data[0].get('fallecido'):
                            _logger.warning("CI %s marcado como fallecido en FUC", identification)
                            raise exceptions.ValidationError(
                                _('Carné de identidad registrado como fallecido en la FUC. '
                                  'Si cree que es un error, diríjase a la entidad encargada.')
                            )
                        _logger.info("Validación exitosa para CI: %s", identification)
                        return True
                    else:
                        _logger.warning("Respuesta FUC inesperada: %s", data)
                        raise exceptions.ValidationError(
                            _("El número de identificación %s no se encuentra registrado en el sistema FUC. "
                              "Verifique que el CI sea correcto.") % identification
                        )

                # Errores que no se reintentan (problemas de lógica o autorización)
                elif response.status_code == 401:
                    _logger.error("Error 401: Token inválido o expirado")
                    raise exceptions.ValidationError(
                        _("Error de autenticación en el servicio FUC: Token inválido o expirado. "
                          "Contacte al administrador del sistema.")
                    )

                elif response.status_code == 404:
                    _logger.warning("CI %s no encontrado en FUC (404)", identification)
                    raise exceptions.ValidationError(
                        _("El número de identificación %s no fue encontrado en el sistema FUC. "
                          "Verifique que el CI sea correcto o contacte a las autoridades.") % identification
                    )

                # Errores de servidor (5xx) se reintentan
                elif 500 <= response.status_code < 600:
                    _logger.warning("Error %d del servidor FUC (intento %d)", response.status_code, attempt)
                    if attempt == max_retries:
                        raise exceptions.ValidationError(
                            _("El servicio de validación FUC no está disponible temporalmente. "
                              "Por favor, intente nuevamente en unos minutos.")
                        )
                    # No lanzamos excepción aún, dejamos que reintente

                else:
                    # Cualquier otro código de estado no esperado
                    _logger.warning("Código de estado inesperado %d", response.status_code)
                    if attempt == max_retries:
                        raise exceptions.ValidationError(
                            _("El servicio FUC respondió con un error inesperado. "
                              "Por favor, intente nuevamente más tarde.")
                        )

            except requests.exceptions.Timeout:
                _logger.warning("Timeout en intento %d de validación FUC", attempt)
                if attempt == max_retries:
                    raise exceptions.ValidationError(
                        _("Tiempo de espera agotado al conectar con el servicio de validación FUC. "
                          "Por favor, intente nuevamente.")
                    )

            except requests.exceptions.ConnectionError:
                _logger.warning("Error de conexión en intento %d", attempt)
                if attempt == max_retries:
                    raise exceptions.ValidationError(
                        _("No se pudo establecer conexión con el servicio de validación FUC. "
                          "Verifique su conexión a internet o contacte al administrador.")
                    )

            except requests.exceptions.RequestException as e:
                _logger.error("Error en solicitud HTTP (intento %d): %s", attempt, str(e))
                if attempt == max_retries:
                    raise exceptions.ValidationError(
                        _("Error en la comunicación con el servicio FUC: %s. "
                          "Por favor, intente nuevamente.") % str(e)
                    )

            except exceptions.ValidationError:
                # Si ya lanzamos una ValidationError (por ejemplo, por 404/401), se propaga directamente
                raise

            except Exception as e:
                # Cualquier otra excepción inesperada (ej. JSON mal formado, error de lógica)
                _logger.exception("Error inesperado en validación FUC (intento %d): %s", attempt, str(e))
                if attempt == max_retries:
                    raise exceptions.ValidationError(
                        _("Error inesperado en el proceso de validación. "
                          "Por favor, intente nuevamente o contacte al administrador.")
                    )

            # Si llegamos aquí (error transitorio y no es el último intento), esperamos y reintentamos
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue

        # Esto no debería alcanzarse porque siempre se lanza alguna excepción
        raise exceptions.ValidationError(
            _("No se pudo completar la validación del CI después de varios intentos. "
              "Por favor, intente nuevamente más tarde.")
        )

    # def _validate_with_fuc(self, identification, is_simulated=False):
    #     """
    #     Valida el CI contra la FUC.
    #     - is_simulated=True → usa localhost:5000
    #     - is_simulated=False → usa URL real
    #     """
    #     try:
    #         # Obtener configuración
    #         keys = request.env['security.configure_keys'].sudo().search([], limit=1, order='id desc')
    #         if is_simulated:
    #             url_base = "http://localhost:5000/api/v1/nivel10?"
    #         else:
    #             if not keys or not keys.url_base:
    #                 raise exceptions.ValidationError(_(
    #                     "Configuración incompleta: No se ha configurado la URL base del servicio de validación FUC. "
    #                     "Contacte al administrador del sistema."
    #                 ))
    #             url_base = keys.url_base
    #
    #         # Obtener token (solo para producción)
    #         if not is_simulated:
    #             token = self._generate_fuc_token()  # Esta función ahora maneja todos los errores
    #             headers = {'Authorization': f"Bearer {token}", 'Accept': 'application/json'}
    #
    #         # Hacer solicitud con reintentos
    #         url = f"{url_base}identidad_numero={identification}"
    #         last_exception = None
    #
    #         for attempt in range(3):
    #             try:
    #                 _logger.info(f"Intento {attempt + 1} de validación FUC para CI: {identification}")
    #                 response = requests.get(url, headers=headers)
    #
    #                 if response.status_code == 200:
    #                     data = response.json()
    #                     # Validar estructura mínima
    #                     if isinstance(data[0], dict) and data[0].get('identidad_numero') == identification:
    #                         _logger.info(f"Validación FUC exitosa para CI: {identification}")
    #                         print(f"Validación FUC exitosa para CI: {identification}")
    #                         if data[0].get('fallecido'):
    #                             print(f"Numero de carnet de fallecido")
    #                             raise exceptions.ValidationError(
    #                                 'Carné de identidad registrado como fallecido en la FUC.'
    #                                 'En caso de no ser correcto dicho dato diríjase a la entidad encargada de arreglar este error.')
    #
    #                         return True
    #                     else:
    #                         raise exceptions.ValidationError(_(
    #                             f"El número de identidad {identification} no se encuentra registrado en el sistema FUC. "
    #                             f"Verifique que el CI sea correcto o contacte a las autoridades correspondientes."
    #                         ))
    #
    #                 elif response.status_code == 401:
    #                     raise exceptions.ValidationError(_(
    #                         "Error de autenticación en el servicio FUC: Token inválido o expirado. "
    #                         "Contacte al administrador del sistema."
    #                     ))
    #
    #                 elif response.status_code == 404:
    #                     raise exceptions.ValidationError(_(
    #                         f"El número de identidad {identification} no fue encontrado en el sistema FUC. "
    #                         f"Verifique que el CI sea correcto o contacte a las autoridades correspondientes."
    #                     ))
    #
    #                 elif response.status_code >= 500:
    #                     _logger.warning(f"Error del servidor FUC (intento {attempt + 1}): {response.status_code}")
    #                     last_exception = exceptions.ValidationError(_(
    #                         "El servicio de validación FUC no está disponible temporalmente. "
    #                         "Por favor, intente nuevamente en unos minutos."
    #                     ))
    #
    #             except requests.exceptions.Timeout:
    #                 _logger.warning(f"Timeout en intento {attempt + 1} de validación FUC")
    #                 last_exception = exceptions.ValidationError(_(
    #                     "Tiempo de espera agotado al conectar con el servicio de validación FUC. "
    #                     "Por favor, intente nuevamente."
    #                 ))
    #
    #             except requests.exceptions.ConnectionError:
    #                 _logger.warning(f"Error de conexión en intento {attempt + 1} de validación FUC")
    #                 last_exception = exceptions.ValidationError(_(
    #                     "No se pudo establecer conexión con el servicio de validación FUC. "
    #                     "Verifique su conexión a internet o contacte al administrador."
    #                 ))
    #
    #             except requests.exceptions.RequestException as e:
    #                 _logger.error(f"Error de solicitud FUC (intento {attempt + 1}): {str(e)}")
    #                 last_exception = exceptions.ValidationError(_(
    #                     f"Error en la comunicación con el servicio FUC: {str(e)}. "
    #                     "Por favor, intente nuevamente o contacte al administrador."
    #                 ))
    #
    #             except Exception as e:
    #                 _logger.error(f"Error inesperado en validación FUC (intento {attempt + 1}): {str(e)}")
    #                 last_exception = exceptions.ValidationError(_(
    #                     "Error inesperado en el proceso de validación. "
    #                     "Por favor, intente nuevamente o contacte al administrador."
    #                 ))
    #
    #             # Esperar antes del próximo intento (excepto en el último)
    #             if attempt < 2:
    #                 time.sleep(1)
    #
    #         # Si llegamos aquí, todos los intentos fallaron
    #         if last_exception:
    #             raise last_exception
    #         else:
    #             raise exceptions.ValidationError(_(
    #                 "No se pudo completar la validación del CI después de varios intentos. "
    #                 "Por favor, intente nuevamente más tarde."
    #             ))
    #
    #     except exceptions.ValidationError:
    #         # Re-lanzar las ValidationError para que sean capturadas arriba
    #         raise
    #     except Exception as e:
    #         # Capturar cualquier otro error inesperado
    #         _logger.error(f"Error crítico en validación FUC: {str(e)}")
    #         raise exceptions.ValidationError(_(
    #             "Error crítico en el sistema de validación. "
    #             "Contacte al administrador del sistema para obtener asistencia."
    #         ))

    def _generate_fuc_token(self):
        """Genera token para FUC (solo producción)."""
        try:
            keys = request.env['security.configure_keys'].sudo().search([], limit=1, order='id desc')
            if not keys:
                raise exceptions.ValidationError(_(
                    "Configuración incompleta: No se encontraron las claves de autenticación FUC. "
                    "Contacte al administrador del sistema para configurar las credenciales de acceso."
                ))

            # Validar que todas las claves necesarias estén configuradas
            if not keys.key_1 or not keys.key_2:
                raise exceptions.ValidationError(_(
                    "Configuración incompleta: Las claves de autenticación FUC no están completamente configuradas. "
                    "Verifique que tanto Key 1 como Key 2 estén establecidas en la configuración de seguridad."
                ))

            if not keys.url:
                raise exceptions.ValidationError(_(
                    "Configuración incompleta: La URL del servicio de autenticación FUC no está configurada. "
                    "Contacte al administrador del sistema."
                ))

            message = f"{keys.key_1}:{keys.key_2}"
            url_token = f"{keys.url}?grant_type=client_credentials&scope=nivel10"

            # Codificar credenciales
            try:
                auth = base64.b64encode(message.encode()).decode()
            except Exception as e:
                raise exceptions.ValidationError(_(
                    "Error al codificar las credenciales de autenticación. "
                    "Verifique el formato de las claves configuradas."
                ))

            headers = {'Authorization': f"Basic {auth}"}

            _logger.info(f"Solicitando token FUC desde: {keys.url}")

            try:
                response = requests.post(url_token, headers=headers, timeout=10)
            except requests.exceptions.Timeout:
                raise exceptions.ValidationError(_(
                    "Tiempo de espera agotado al conectar con el servicio de autenticación FUC. "
                    "El servicio puede estar sobrecargado. Por favor, intente nuevamente."
                ))
            except requests.exceptions.ConnectionError:
                raise exceptions.ValidationError(_(
                    "No se pudo establecer conexión con el servicio de autenticación FUC. "
                    "Verifique la URL configurada y la conexión a internet."
                ))
            except requests.exceptions.RequestException as e:
                raise exceptions.ValidationError(_(
                    f"Error de comunicación con el servicio de autenticación FUC: {str(e)}. "
                    "Contacte al administrador del sistema."
                ))

            # Analizar respuesta
            if response.status_code == 200:
                try:
                    token_data = response.json()
                    token = token_data.get('access_token')
                    if not token:
                        raise exceptions.ValidationError(_(
                            "El servicio de autenticación FUC no devolvió un token válido. "
                            "La respuesta no contiene el campo 'access_token'."
                        ))

                    # Guardar token en parámetros del sistema
                    request.env['ir.config_parameter'].sudo().set_param('fuc.token', token)
                    _logger.info("Token FUC generado y almacenado exitosamente")
                    return token

                except ValueError as e:
                    raise exceptions.ValidationError(_(
                        "Error al procesar la respuesta del servicio de autenticación FUC. "
                        "La respuesta no es un JSON válido."
                    ))

            elif response.status_code == 401:
                raise exceptions.ValidationError(_(
                    "Error de autenticación: Las credenciales FUC (Key 1 y Key 2) son incorrectas o han expirado. "
                    "Contacte al administrador del sistema para actualizar las credenciales."
                ))

            elif response.status_code == 400:
                raise exceptions.ValidationError(_(
                    "Solicitud incorrecta al servicio de autenticación FUC. "
                    "Verifique los parámetros de la solicitud (grant_type y scope)."
                ))

            elif response.status_code == 403:
                raise exceptions.ValidationError(_(
                    "Acceso denegado: No tiene permisos para acceder al servicio de autenticación FUC. "
                    "Verifique que el alcance (scope) 'nivel10' esté autorizado para las credenciales."
                ))

            elif response.status_code >= 500:
                raise exceptions.ValidationError(_(
                    "El servicio de autenticación FUC no está disponible temporalmente. "
                    "Por favor, intente nuevamente en unos minutos. "
                    f"Error del servidor: {response.status_code}"
                ))

            else:
                raise exceptions.ValidationError(_(
                    f"Error inesperado del servicio de autenticación FUC. Código: {response.status_code}. "
                    "Contacte al administrador del sistema."
                ))

        except exceptions.ValidationError:
            # Re-lanzar las ValidationError para mantener el mensaje específico
            raise
        except Exception as e:
            # Capturar cualquier error inesperado
            _logger.error(f"Error crítico al generar token FUC: {str(e)}")
            raise exceptions.ValidationError(_(
                "Error crítico en el sistema de autenticación. "
                "Contacte al administrador del sistema para obtener asistencia."
            ))

    def validate_registration_data(self, **post):
        """Validación REAL (producción)."""
        email = post.get('email')
        identification = post.get('identification')
        nationality_id = post.get('nationalities')
        base_login = post.get('user')

        # Validaciones comunes
        self._validate_cuban_id(identification, nationality_id)
        self._check_existing_email_or_identification(email, identification)
        post['user'] = self._check_and_generate_login(base_login)

        # Validar con FUC si aplica
        nationality = request.env['nomenclators.nationality'].sudo().browse(int(nationality_id))
        if nationality.validate_fuc:
            if not self._validate_with_fuc(identification, is_simulated=False):
                raise exceptions.ValidationError(
                    "Sus datos no están validados por la Ficha Única del Ciudadano (FUC).\n"
                    "Debe dirigirse a la oficina más cercana de trámites para verificar su información."
                )
        return True

    def validate_registration_data_simulated(self, **post):
        """Validación SIMULADA (localhost:5000)."""
        email = post.get('email')
        identification = post.get('identification')
        nationality_id = post.get('nationalities')
        base_login = post.get('user')

        # Validaciones comunes
        self._validate_cuban_id(identification, nationality_id)
        self._check_existing_email_or_identification(email, identification)
        post['user'] = self._check_and_generate_login(base_login)

        # Validar con API local si aplica
        nationality = request.env['nomenclators.nationality'].sudo().browse(int(nationality_id))
        if nationality.validate_fuc:
            if not self._validate_with_fuc(identification, is_simulated=True):
                raise exceptions.ValidationError(
                    "Sus datos no existen en el sistema de prueba (localhost:5000).\n"
                    "Asegúrese de que el CI esté registrado en su API local."
                )
        return True
