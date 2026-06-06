# -*- coding: utf-8 -*-
import base64
import re

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json
from unidecode import unidecode

from lxml import etree
import passlib.context

from odoo.exceptions import ValidationError, UserError
from odoo.tools import profile, html_sanitize

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


class ProfessionalRequest(models.Model):
    _name = 'professional_registers.professional_request'
    _description = 'Solicitud del profesional'
    _rec_name = 'request_number'

    PHONE_MIN_LENGTH = 8
    PHONE_MAX_LENGTH = 15
    INTERNATIONAL_MIN_LENGTH = 7
    INTERNATIONAL_MAX_LENGTH = 15

    request_number = fields.Char('Nro. solicitud')
    name = fields.Char('Nombre')
    first_last_name = fields.Char('Primer apellido')
    second_last_name = fields.Char('Segundo apellido')
    full_name = fields.Char('Nombre y apellidos')
    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")
    identity = fields.Char('CI o Pasaporte')
    id_fuc = fields.Char('Id FUC')
    sex = fields.Selection([('male', 'Masculino'),
                            ('female', 'Femenino')], string="Sexo")
    address = fields.Text('Dirección particular')
    country = fields.Many2one('res.country', string="País")
    country_states = fields.Many2one('res.country.state', string="Provincia")
    city = fields.Many2one('res.city', string="Municipio")
    phone = fields.Char('Teléfono*')
    email = fields.Char('Correo')


    teaching_level = fields.Many2one('nomenclators.teaching_level', string="Nivel de enseñanza*")
    study_center = fields.Many2one('nomenclators.study_centers', string="Centros de estudios*")
    degree_date = fields.Date('Fecha de graduación*')
    volume = fields.Char('Tomo*')
    folio = fields.Char('Folio*')
    number = fields.Char('Número')
    convalidation_degree_tittle = fields.Date('Fecha convalidación de título exp en el extranjero')
    profession = fields.Many2one('nomenclators.professions', string="Profesión*")
    specialties = fields.Many2one('nomenclators.specialties', string="Especialidad*")

    def _get_years(self):
        current_year = datetime.utcnow().year
        years = []
        for year in range(1950, current_year + 1):
            years.append((str(year), str(year)))
        return years

    investigations = fields.Boolean('Investigaciones', tracking=True)
    investigations_year = fields.Selection(
        selection='_get_years',
        string='Año de la investigación'
    )

    @api.onchange('investigations')
    def _onchange_investigations(self):
        if not self.investigations:
            self.investigations_year = False

    @api.constrains('investigations', 'investigations_year')
    def _check_investigations_year(self):
        for record in self:
            if record.investigations and not record.investigations_year:
                raise ValidationError('El año de investigación es requerido cuando se marca investigaciones.')

    degree_sciences = fields.Selection([('anything', 'Ninguno'),
                                        ('esp', 'Esp.'),
                                        ('msc', 'Msc.'),
                                        ('dr', 'Dr.')], string="Categoría científica")

    degree_sciences_year = fields.Selection(
        selection='_get_years', string='Año de categoría científica')

    @api.depends('degree_sciences')
    def _compute_degree_sciences_fields(self):
        for record in self:
            has_degree = bool(record.degree_sciences)
            is_none = record.degree_sciences == 'Ninguno'

            record.is_degree_sciences_none = is_none
            record.degree_sciences_year_required = has_degree and not is_none

    is_degree_sciences_none = fields.Boolean(compute='_compute_degree_sciences_fields', store=True)
    degree_sciences_year_required = fields.Boolean(compute='_compute_degree_sciences_fields', store=True)

    @api.onchange('degree_sciences')
    def _onchange_degree_sciences(self):
        if not self.degree_sciences or self.degree_sciences == 'Ninguno':
            self.degree_sciences_year = False

    @api.constrains('degree_sciences', 'degree_sciences_year')
    def _check_degree_sciences_year(self):
        for record in self:
            if record.degree_sciences and record.degree_sciences != 'Ninguno' and not record.degree_sciences_year:
                raise ValidationError(
                    _('El año de categoría científica es requerido cuando se selecciona una categoría.'))

    teaching_category = fields.Many2one('nomenclators.teaching_categories', string="Categoría docente")
    teaching_category_date = fields.Date('Fecha de categ. docente')

    @api.depends('teaching_category', 'teaching_category.name')
    def _compute_teaching_category_fields(self):
        for record in self:
            has_category = bool(record.teaching_category)
            is_none = record.teaching_category.name == 'Ninguna' if record.teaching_category else False

            record.is_teaching_category_none = is_none
            record.teaching_category_date_required = has_category and not is_none

    is_teaching_category_none = fields.Boolean(compute='_compute_teaching_category_fields', store=True)
    teaching_category_date_required = fields.Boolean(compute='_compute_teaching_category_fields', store=True)

    @api.constrains('teaching_category', 'teaching_category_date')
    def _check_teaching_category_date(self):
        for record in self:
            if record.teaching_category and record.teaching_category.name != 'Ninguna' and not record.teaching_category_date:
                raise ValidationError(
                    _('La fecha de categoría docente es requerida cuando se selecciona una categoría.'))

    unaicc_date = fields.Date('Fecha ingreso UNAICC')
    user = fields.Char('Usuario')
    password = fields.Char('Contraseña')

    image = fields.Image("Foto", max_width=1920, max_height=1920)
    date = fields.Date('Fecha Jubilación', )
    retired = fields.Boolean('Jubilado', default=False, tracking=True)

    @api.onchange('retired')
    def _onchange_retired(self):
        if not self.retired:
            self.date = False

    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario Registrador")
    id_user_register = fields.Many2one('res.users', string="Usuario asociado")

    register_user = fields.Char('Nombre del registrador')

    year = fields.Char('Año')

    attachment_ids = fields.Many2many('ir.attachment', string="Subir")
    # certificate_attachment = fields.Many2many('ir.attachment', string="Certificación")
    certificate_attachment = fields.Many2many(
        "ir.attachment",
        "professional_ir_attachments_rel",
        "professional_id",
        "attachment_id",
        "Certificación",
    )
    certification = fields.Boolean('Doc Certificación')

    public_field_ids = fields.Many2many(
        'professional_registers.public_field',
        string='Campos Públicos Globales',
        relation='prof_request_public_field_rel',
        column1='request_id',
        column2='field_id'
    )

    def get_public_fields(self):
        self.ensure_one()
        return {
            field.field_name: self[field.field_name]
            for field in self.public_field_ids.filtered(lambda f: f.active)
        }

    def _get_states(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        arra_ids = []
        states = []
        STATES_BY_PROCEDURE = {
            'inscription': [1, 2, 3, 4, 5, 6, 7, 8],
            'update': [1, 2, 3, 6, 8],
            'renewal': [1, 2, 3, 6, 8]
        }

        for procedure, ste in STATES_BY_PROCEDURE.items():
            if self.procedure_type.comodel_name == procedure:
                states = self.env['security.state_configuration'].search(
                    [('model', '=', int(model.id)), ('id', 'in', ste)],
                    order="priority asc"
                )

        for e in states:
            arra_ids.append(e.id)
        return [('id', 'in', arra_ids)]

    def _get_default_value(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([('model', '=', int(model.id))], order="priority asc")
        if states:
            return states[0].id

    states = fields.Many2one('security.state_configuration', string='Estados', domain=_get_states,
                             default=_get_default_value)

    priority = fields.Integer('prioridad', default=1)

    history_work = fields.One2many('professional_registers.work_history', 'profesional_request',
                                   string="Trayectoria laboral")
    professional_language = fields.One2many('nomenclators.professional_language', 'profesional_request',
                                            string="Idioma")
    history_ids = fields.One2many(
        'professional_registers.professional_request_history',
        'request_id',
        string='Histórico de Cambios de Estado'
    )

    is_view_datails = fields.Boolean('Vista', default=False)

    date_request = fields.Date('Fecha solicitud', default=datetime.utcnow().date().strftime('%Y-%m-%d'))

    register_type = fields.Selection([('register', 'Registrador'),
                                      ('other', 'Otro')], string="Tipo de registro")

    observation = fields.Text('Observación')

    # Validate documentation
    documents_required = fields.One2many('professional_registers.pr_document', 'request',
                                         string="Documentos requeridos")
    documents_required_registers = fields.One2many('professional_registers.pr_document', 'request',
                                                   string="Documentos registrados requeridos")

    register_date = fields.Date("Fecha de registro", default=datetime.utcnow().date().strftime('%Y-%m-%d'))

    day_passed_count = fields.Integer('Días transcurridos')

    force_erase = fields.Boolean('Borrar forzado', default=False)

    # For profile
    procedure_states = fields.Many2one('security.state_configuration', string='Estados Procedimiento',
                                       related='inscription_id.states')

    def get_procedure_default(self):
        procedure = self.env['nomenclators.procedure_types'].search([('comodel_name', '=', 'inscription')])
        return procedure.id

    procedure_type = fields.Many2one('nomenclators.procedure_types', string="Tipo de trámite*",
                                     default=get_procedure_default)
    inscription_id = fields.Many2one('professional_registers.inscription', string='Inscripción')

    is_inscription_fuc = fields.Boolean('Es inscripcion FUC', default=False)

    payment_type = fields.Selection([('sello', 'Sello'),
                                     ('no_pagado', 'No pagado')],
                                    string="Pago", default='no_pagado')

    is_register_online = fields.Boolean('Es registro online', default=False)
    others_professions = fields.One2many('professional_registers.others_professions', 'profile',
                                         string="Otras profesiones")

    is_validate = fields.Boolean()

    user_on_charge = fields.Many2one('res.users', string="Responsable")

    has_denied_request = fields.Boolean(
        string="Tiene solicitud denegada",
        compute='_compute_has_denied_request',
        help="Indica si existe una solicitud denegada previa para esta profesión"
    )

    update_ids = fields.One2many(
        'professional_registers.professional_request_update',
        'original_request_id',
        string='Actualizaciones Solicitadas'
    )

    update_count = fields.Integer(
        string='Actualizaciones',
        compute='_compute_update_count'
    )

    profile_id = fields.Many2one('professional_registers.profile', string="Perfil")

    claim_ids = fields.One2many(
        'professional_registers.claim_request',
        'original_request_id',
        string='Reclamaciones'
    )


    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente')

    has_public_fields = fields.Boolean(
        string='Tiene Campos Públicos',
        compute='_compute_has_public_fields',
        store=False
    )

    last_sync_date = fields.Datetime(
        'Última Sincronización',
        readonly=True,
        help="Fecha de la última sincronización con el perfil"
    )

    can_sync = fields.Boolean(
        'Se puede sincronizar',
        compute='_compute_can_sync',
        store=True,
        help="Indica si la solicitud se puede sincronizar con el perfil"
    )

    # @api.depends('identity')
    # def _compute_profile_id(self):
    #     for record in self:
    #         if not self.profile_id:
    #             if record.identity:
    #                 profile = self.env['professional_registers.profile'].search([
    #                     ('identity', '=', record.identity)
    #                 ], limit=1)
    #                 record.profile_id = profile.id if profile else False
    #             else:
    #                 record.profile_id = False

    @api.depends('priority')
    def _compute_can_sync(self):
        for record in self:
            # No se puede sincronizar si está en estado 3 (validación) o 6 (aprobada)
            record.can_sync = record.priority not in [3, 6]

    def _compute_has_public_fields(self):
        for record in self:
            record.has_public_fields = bool(
                self.env['professional_registers.public_request'].search_count([('request_id', '=', record.id)]))

    def _compute_update_count(self):
        for record in self:
            record.update_count = self.env['professional_registers.professional_request_update'].search_count(
                [('original_request_id', '=', record.id)]
            )

    @api.depends('profession', 'identity')
    def _compute_has_denied_request(self):
        denied_state = 8
        for record in self:
            if record.profession and record.identity:
                # Dominio base para buscar solicitudes denegadas con misma profesión/identidad
                domain = [
                    ('profession', '=', record.profession.id),
                    ('identity', '=', record.identity),
                    ('states', '=', denied_state),
                ]

                # Si el registro ya existe en BD (no es NewId), excluirlo de la búsqueda
                if record.id and isinstance(record.id, int):
                    domain.append(('id', '!=', record.id))

                # Buscar coincidencias (limit=1 para optimizar)
                denied_requests = self.search(domain, limit=1)
                record.has_denied_request = bool(denied_requests)
            else:
                record.has_denied_request = False

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(ProfessionalRequest, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'password', 'image', 'attachment_ids',
                   'priority', 'is_view_datails', 'history_work', 'certificate_attachment', 'is_inscription_fuc',
                   'documents_required', 'documents_required_registers', 'id_user_register', 'procedure_states',
                   'company_id', 'force_erase']

        for f in mfields:
            if f in res:
                res[f]['searchable'] = False
                res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProfessionalRequest, self).fields_view_get(view_id=view_id,
                                                               view_type=view_type,
                                                               toolbar=toolbar,
                                                               submenu=submenu)

        user = self.env['res.users'].search([('id', '=', self.env.uid)])
        doc = etree.XML(res['arch'])

        if not self.env['res.users'].has_group('security.group_professional_superadmin') and not self.env[
            'res.users'].has_group('security.group_professional_editor') and not self.env['res.users'].has_group(
            'security.group_professional_editor_managment') and not self.env['res.users'].has_group(
            'security.group_professional_register_employee') and not self.env['res.users'].has_group(
            'security.group_professional_reigster_managment'):
            doc.set('create', '0')
            doc.set('edit', '0')
            doc.set('delete', '0')

        if self.env['res.users'].has_group('security.group_professional_client_online'):
            doc.set('create', 'false')
            doc.set('edit', 'true')
            doc.set('delete', 'true')

        for btn in doc.xpath("//button[@name='process']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('in_process', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='validation']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('validation', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='stop']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('stop', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='approved']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('approved', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='init_process']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('init_process', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='cancel']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('cancel', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='reset_process']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('reset', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='send_email']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('send_email', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='denied']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('denied', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc)
        return res

    # @api.model
    # def default_get(self, fields_list):
    #     id_request = self._context.get('id_request')
    #     online_client_true = self.env['res.users'].has_group('security.group_professional_client_online')
    #     if online_client_true:
    #         profile = self.env['professional_registers.profile'].search([('user_id', '=', int(self.env.uid))], limit=1)
    #         id_request = self.env['professional_registers.professional_request'].search(
    #             [('id_user_register', '=', int(profile.user_id))], )
    #
    #     if id_request:
    #         request = self.env['professional_registers.professional_request'].search([('id', '=', int(id_request))])
    #         request_his = self.env['professional_registers.professional_request_history'].search(
    #             [('request_id', '=', int(id_request))])
    #         attach = []
    #         history_work = []
    #         for a in request.attachment_ids:
    #             attach.append(a.id)
    #         for hw in request.history_work:
    #             history_work.append(hw.id)
    #         return {
    #             'id': request.id,
    #             'attachment_ids': [[6, 0, attach]],
    #             'history_work': [[6, 0, history_work]],
    #             'is_view_datails': False,
    #             'request_number': request.request_number,
    #             'register_user': request.register_user,
    #             'name': request.name,
    #             'first_last_name': request.first_last_name,
    #             'second_last_name': request.second_last_name,
    #             'full_name': request.full_name,
    #             'nationality_id': request.nationality_id.id,
    #             'identity': request.identity,
    #             'sex': request.sex,
    #             'address': request.address,
    #             'country': request.country.id,
    #             'country_states': request.country_states.id,
    #             'city': request.city.id,
    #             'phone': request.phone,
    #             'email': request.email,
    #             'teaching_level': request.teaching_level.id,
    #             'study_center': request.study_center.id,
    #             'degree_date': request.degree_date,
    #             'volume': request.volume,
    #             'folio': request.folio,
    #             'profession': request.profession.id,
    #             'specialties': request.specialties.id,
    #             'teaching_category': request.teaching_category.id,
    #             'teaching_category_date': request.teaching_category_date,
    #             'investigations': request.investigations,
    #             'investigations_year': request.investigations_year,
    #             'degree_sciences': request.degree_sciences,
    #             'degree_sciences_year': request.degree_sciences_year,
    #             'unaicc_date': request.unaicc_date,
    #             'user': request.user,
    #             'password': request.password,
    #             'image': request.image,
    #             'date': request.date,
    #             'retired': request.retired,
    #             'company_id': request.company_id.id,
    #             'user_id': request.user_id.id,
    #             'year': request.year,
    #             'states': request.states.id,
    #             'priority': request.priority,
    #
    #         }
    #     else:
    #         return super(ProfessionalRequest, self).default_get(fields_list)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        if self.env["res.users"].has_group("security.group_professional_client"):
            aux = [('id_user_register', '=', int(user.id))]
            for a in aux:
                domain.append(a)
        if self.env["res.users"].has_group("security.group_professional_client_online"):
            aux = [('id_user_register', '=', int(user.id))]
            for a in aux:
                domain.append(a)
        elif self.env["res.users"].has_group("security.group_professional_register_employee"):
            aux = [('user_id', '=', int(user.id))]
            for a in aux:
                domain.append(a)

        res = super(ProfessionalRequest, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.onchange('name', 'first_last_name', 'second_last_name')
    def onchange_full_name(self):
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

        self.full_name = name

        if self.name and self.first_last_name and not self.is_register_online:
            first_letter = self.name[:1]
            request_number = self.request_number
            if not self.request_number:
                request_number = self.get_request_number()
                self.request_number = request_number
            user = first_letter + self.first_last_name + str(request_number)
            str_accent = unidecode(user)
            str_lower = str(str_accent).lower()
            self.user = str_lower

            str_empty = str(self.name).split(' ')
            password = self.name + '*123'
            if len(str_empty) > 1:
                password = ''.join(str_empty) + '*123'

            self.password = password

    @api.onchange('teaching_category_date', 'unaicc_date', 'degree_sciences_year', 'investigations_year', 'degree_date')
    def date_validates(self):
        if self.degree_date:
            year = self.degree_date.year
            current_date = datetime.utcnow().date()
            current_year = datetime.utcnow().year
            if self.degree_date > current_date:
                self.degree_date = current_date
                self.env.user.notify_warning(message='La fecha de graduación no puede ser mayor que la fecha actual')

            if self.teaching_category_date:
                if self.teaching_category_date < self.degree_date:
                    self.teaching_category_date = self.degree_date
                    self.env.user.notify_warning(
                        message='La fecha de categoría docente debe ser mayor o igual que la fecha de  graduación')

            if self.unaicc_date:
                if self.unaicc_date < self.degree_date:
                    self.unaicc_date = self.degree_date
                    self.env.user.notify_warning(
                        message='La fecha de ingreso a la UNAICC debe ser mayor o igual que la fecha de  graduación')

            if self.degree_sciences_year:
                if int(self.degree_sciences_year) < int(year):
                    self.degree_sciences_year = str(year)
                    self.env.user.notify_warning(
                        message='El año de grado científico debe ser mayor o igual que el año de graduación')

            if self.investigations_year:
                if int(self.investigations_year) < int(year):
                    self.investigations_year = str(year)
                    self.env.user.notify_warning(
                        message='El año de la investigación debe ser mayor o igual que el año de graduación')

    @api.onchange('country_states')
    def onchange_country_states(self):
        if self.country_states:
            cities = self.env['res.city'].search([('state_id', '=', int(self.country_states.id))])
            return dict(
                value=dict(
                    city=None
                ),
                domain=dict(
                    city=[('id', 'in', cities.ids)]
                )
            )

    @api.onchange('country')
    def onchange_country(self):
        if self.country:
            states = self.env['res.country.state'].search([('country_id', '=', int(self.country.id))])
            return dict(
                value=dict(
                    country_states=None
                ),
                domain=dict(
                    country_states=[('id', 'in', states.ids)]
                )
            )

    @api.onchange('profession')
    def onchange_profession(self):
        if self.profession:
            specialties = self.env['nomenclators.specialties'].search([('profession_id', '=', int(self.profession.id))])

            return dict(
                value=dict(
                    specialties=None  # Para que lo limpie
                ),
                domain=dict(
                    specialties=[('id', 'in', specialties.ids)]
                )
            )

    @api.onchange('is_validate')
    def onchange_procedure_type(self):
        if self.is_validate:
            documents = self.env['nomenclators.documents_required'].search(
                [('procedure1', '=', int(self.procedure_type.id))], order="order asc")
            arra_ids = []
            for d in documents:
                arra_ids.append((0, 0, {
                    'documents': d.id,
                    'checked': False,
                    'commet': ''
                }))
            self.documents_required = [[6, 0, []]]
            self.documents_required = arra_ids

    # Buttons
    def go_to_request(self):
        request = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])
        if request:

            ir_model_data = self.env['ir.model.data']
            form_id = True
            ctx = []
            try:
                form_id = (ir_model_data.get_object_reference('professional_registers', 'request_help_form_view')[1])
            except ValueError:
                form_id = False

            ctx = {
                'id_request': request.id,
                'req_id': self.id
            }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'professional_registers.request_help',
                'name': 'Solicitud del profesional',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                # 'res_id': request.id,
                'target': 'new',
                'context': ctx,
                # 'clear_breadcrumbs': True,
            }

    def go_to_identity(self):
        if not self.inscription_id:
            raise exceptions.ValidationError(
                'Su carné todavía no ha sido generado. Su trámite se encuentra en proceso.')

        identity = self.env['professional_registers.identity'].search(
            [('inscription_id', '=', int(self.inscription_id.id))])
        if identity:
            ir_model_data = self.env['ir.model.data']
            form_id = True
            ctx = []
            try:
                form_id = (
                    ir_model_data.get_object_reference('professional_registers', 'identity_form_view')[1])
            except ValueError:
                form_id = False

            ctx = {
                'id_identity': identity[0].id,
            }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'professional_registers.identity',
                'name': 'Carné del profesional',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                # 'res_id': request.id,
                'target': 'new',
                'context': ctx,
                # 'clear_breadcrumbs': True,
            }

    def process(self):
        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 2), ('model', '=', int(model.id))]
        )

        # ========================
        # Validación de Documentos (Versión Corregida)
        # ========================
        error_messages = []

        # 1. Obtener documentos requeridos para el trámite
        required_docs = self.env['nomenclators.documents_required'].search([
            ('is_document_required', '=', True)
        ])

        # 2. Documentos subidos por el usuario
        uploaded_docs = self.documents_required.mapped('documents')

        # 3. Encontrar documentos faltantes
        missing_docs = required_docs - uploaded_docs

        # 4. Verificar adjuntos en documentos requeridos subidos
        docs_without_attachments = []
        for doc_record in self.documents_required.filtered(lambda x: x.documents in required_docs):
            if not doc_record.attachment_ids:
                docs_without_attachments.append(doc_record.documents.name)

        # Construir mensajes para documentos
        if missing_docs:
            error_messages.append("🚨 Documentos requeridos faltantes:\n- " + "\n- ".join(missing_docs.mapped('name')))

        if docs_without_attachments:
            error_messages.append("🚨 Documentos requeridos faltantes :\n- " + "\n- ".join(docs_without_attachments))

        # ==============================
        # Validación de Campos Obligatorios
        # ==============================
        field_errors = []

        # if not self.history_work:
        #     field_errors.append("👔 Debe registrar al menos un elemento en Vínculo Laboral !! \n")

        if not self.professional_language:
            field_errors.append("🌐 Debe registrar al menos un idioma !! \n")

        if not self.is_validate:
            field_errors.append("🚨 Debe marcar el checkbox que declara la autenticidad de sus documentos subidos !! \n")


        # Combinar todos los errores
        all_errors = error_messages + field_errors

        # ========================
        # Manejo de Resultados
        # ========================
        if all_errors:
            full_message = "❌ Para completar el proceso:\n\n" + "\n\n".join(all_errors)
            raise exceptions.ValidationError(full_message)

        else:

            exp = self.env['professional_registers.expedient'].create({'professional_id':self.profile_id.id})

            exp.action_open()

            # TODO: todo está correcto, actualizar estado
            self.env['professional_registers.professional_request_history'].create({
                'request_id': self.id,
                'state_id': self.states.id,
                'state_id_new': state_priority.id,
                'user_id': self.env.user.id,
                'date': current_date,
                'observation': f"Cambio de estado a {state_priority.name}"
            })

            self.write({
                'states': state_priority.id,
                'priority': 2,
                'date_request': current_date
            })

            self.generate_notifications(2)

    def validation(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 3), ('model', '=', int(model.id))])

        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        self.env['professional_registers.professional_request_history'].create({
            'request_id': self.id,
            'state_id': self.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 3,
            'user_on_charge': self.env.uid
        })

        register = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])
        state = self.get_string_state(state_priority, 'professional_registers.professional_request')
        if register:
            register.write({
                'state': state,
            })

            # Enviar correo de notificación (versión mejorada)
        if not self.email:
            raise UserError("No se puede enviar notificación: la solicitud no tiene email asociado")

            # Obtener datos para el correo
        solicitud_data = {
            'solicitud_no': self.request_number,
            'solicitante': self.full_name,
            'tipo_solicitud': self.procedure_type.name,
            'fecha_solicitud': self.date_request,
            'user': self.env.user.partner_id.name,
            'nuevo_estado': state_priority.name
        }

        # Renderizar cuerpo del correo
        body_html = f"""
           <div style="font-family: Arial, sans-serif; line-height: 1.5;">
               <h2 style="color: #2c3e50;">Notificación de Cambio de Estado</h2>
               <p>Estimado/a {self.full_name},</p>
               <p>Le informamos que su solicitud <strong>{self.request_number}</strong> ha cambiado a estado: <strong>{state_priority.name}</strong>.</p>

               <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
               <ul>
                   <li><strong>Número:</strong> {self.request_number}</li>
                   <li><strong>Tipo:</strong> {self.procedure_type.name}</li>
                   <li><strong>Fecha:</strong> {self.date_request}</li>
                   <li><strong>Responsable:</strong> {self.env.user.partner_id.name}</li>
               </ul>

               <p style="margin-top: 20px;">
                   Puede consultar el estado de su solicitud en cualquier momento accediendo al sistema.
               </p>

               <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
                   Este es un mensaje automático, por favor no responda directamente a este correo.
               </p>
           </div>
           """

        # Sanitizar el HTML
        sanitized_html = html_sanitize(body_html)

        # Buscar o crear el partner asociado
        partner = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.full_name,
                'email': self.email
            })

        # Preparar valores del correo
        mail_values = {
            'subject': f"Solicitud en Validación - {self.request_number}",
            'body_html': sanitized_html,
            'email_to': self.email,
            'email_from': self.env.user.email or self.env.company.email,
            'partner_ids': [(4, partner.id)],
            'model': self._name,
            'res_id': self.id,
        }

        # Crear y enviar el correo
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        # Mostrar notificación al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Solicitud en Validación',
                'message': f'Se notificó al profesional ({self.email}) que su solicitud está en validación',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def stop(self):

        self.generate_notifications(4)

        return {
            "type": "ir.actions.act_window",
            "name": "Detener Solicitud",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_solicitud_id": self.id,
                "default_estado_destino": 4,
                "default_action_type": "detention",  # fill with the desired action type
                "default_email_to": self.email,  # fill with the recipient email
            },
        }

    def approved(self, register=None):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 6), ('model', '=', int(model.id))])

        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        self.env['professional_registers.professional_request_history'].create({
            'request_id': self.id,
            'state_id': self.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 6,
            'user_on_charge': self.env.user.id
        })

        self.generate_notifications(5)
        self.generate_insriptions(register)
        request_help = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])
        state = self.get_string_state(state_priority.id, 'professional_registers.professional_request')
        if request_help:
            request_help.write({
                'state': state,
            })

    def cancel(self):

        self.generate_notifications(7)

        return {
            "type": "ir.actions.act_window",
            "name": "Cancelar Solicitud",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_solicitud_id": self.id,
                "default_estado_destino": 7,
                "default_action_type": "cancellation",  # fill with the desired action type
                "default_email_to": self.email,  # fill with the recipient email
            },
        }

    def init_process(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 3), ('model', '=', int(model.id))])

        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        self.env['professional_registers.professional_request_history'].create({
            'request_id': self.id,
            'state_id': self.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 3,
            'user_on_charge': self.env.uid
        })

        register = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])
        state = self.get_string_state(state_priority, 'professional_registers.professional_request')
        if register:
            register.write({
                'state': state,
            })

        self.generate_notifications(3)

    def reset_process(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 2), ('model', '=', int(model.id))])
        current_date = datetime.utcnow().date()

        self.env['professional_registers.professional_request_history'].create({
            'request_id': self.id,
            'state_id': self.states.id,
            'state_id_new': state_priority.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'date_request': current_date,
            'states': state_priority.id,
            'priority': 2,
            'user_on_charge': self.env.uid
        })

        register = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])
        state = self.get_string_state(state_priority, 'professional_registers.professional_request')
        if register:
            register.write({
                'state': state,
            })

        self.generate_notifications(2)

    def denied(self):

        self.generate_notifications(8)

        return {
            "type": "ir.actions.act_window",
            "name": "Denegar Solicitud",
            "res_model": "solicitud.observacion.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_solicitud_id": self.id,
                "default_estado_destino": 8,
                "default_action_type": "denial",  # fill with the desired action type
                "default_email_to": self.email,  # fill with the recipient email
            },
        }

    def send_email(self):
        self.ensure_one()
        ir_model_data = self.env["ir.model.data"]
        try:
            compose_form_id = ir_model_data.get_object_reference(
                "professional_registers", "email_form"
            )[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})

        template_id = self.env['mail.template'].search([('name', '=', 'Professional Register comment')])
        user = self.env['res.users'].search([('login', '=', str(self.user))])
        body = """
         """
        for register in self.documents_required:
            body = body + '<strong>' + str(register.documents.name) + ": </strong>" + str(register.commet) + '<br>'

        template_id.write({
            'body_html': body
        })
        ctx.update(
            {
                "default_model": "professional_registers.professional_request",
                "default_res_id": self.id,
                "default_composition_mode": "comment",  # "comment",# mass_mail
                "force_email": True,
                "default_body": body,
                # "default_subject": 'dad',
                'default_template_id': template_id.id,
                # "mark_rfq_as_sent": True,
                'mark_so_as_sent': True,
                "default_partner_ids": user.partner_id.ids,
            }
        )

        return {
            "name": "Envío de comentarios a profesional",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }

    # def report_request(self):
    #     email = self.email if self.email else ''
    #     nationality = self.nationality_id.name
    #     degree_sciences = ''
    #     if self.degree_sciences == 'esp':
    #         degree_sciences = 'Especialista'
    #     elif self.degree_sciences == 'msc':
    #         degree_sciences = 'Master'
    #     elif self.degree_sciences == 'dr':
    #         degree_sciences = 'Doctor'
    #
    #     history_work = []
    #     for hw in self.history_work:
    #         history_work.append({
    #             'work_center': hw.work_center,
    #             'organism': hw.organism.siglas,
    #             'activity': hw.activity,
    #             'phone': hw.phone,
    #             'date_from': hw.date_from,
    #             'date_to': hw.date_to,
    #         })
    #
    #     data = {
    #         'request_number': self.request_number,
    #         'identity': self.identity,
    #         'nationality': nationality,
    #         'email': email,
    #         'profession': self.profession.name,
    #         'speciality': self.specialties.name,
    #         'state': self.states.name,
    #         'tramit_type': 'Inscripción',
    #         'date': self.date_request,
    #         'name': self.name,
    #         'first_last_name': self.first_last_name,
    #         'second_last_name': self.second_last_name,
    #         'sex': 'Masculino' if self.sex == 'male' else 'Femenino',
    #         'address1': self.address,
    #         'country': self.country.name,
    #         'country_state': self.country_states.name,
    #         'city': self.city.name,
    #         'phone': self.phone,
    #         'teaching_level': self.teaching_level.name,
    #         'study_center': self.study_center.name,
    #         'degree_date': self.degree_date,
    #         'tomo': self.volume,
    #         'folio': self.folio,
    #         'convalidation_degree_tittle': self.convalidation_degree_tittle,
    #         'teaching_category': self.teaching_category.name,
    #         'teaching_category_date': self.teaching_category_date,
    #         'investigations': 'Si' if self.investigations else 'No',
    #         'investigations_year': self.investigations_year,
    #         'degree_sciences': degree_sciences,
    #         'degree_sciences_year': self.degree_sciences_year,
    #         'unaicc_date': self.unaicc_date,
    #         'user_name': self.user,
    #         'retired': 'Si' if self.retired else 'No',
    #         'retired_date': self.date,
    #         'password': self.password,
    #         'history_work': history_work,
    #     }
    #     return self.env.ref('professional_registers.professional_request_detail').report_action(self, data)
    def report_request(self):
        """
        Acción llamada por el botón 'Imprimir' en el formulario.
        Devuelve la acción del reporte QWeb.
        """
        self.ensure_one()
        return self.env.ref('professional_registers.action_report_professional_request_pdf').report_action(self)

    def get_days_passed(self):
        # Obtener IDs de estados excluidos (prioridad 1,6,7,8)
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        excluded_states = self.env['security.state_configuration'].search([
            ('model', '=', model.id),
            ('priority', 'in', (1, 6, 7, 8))
        ])
        excluded_ids = excluded_states.ids

        today = fields.Date.today()

        # Buscar registros que NO tengan esos estados y tengan fecha
        # Como 'not in' no funciona, hacemos dos pasos o usamos filtered (si no son miles)
        all_requests = self.env['professional_registers.professional_request'].search([
            ('date_request', '!=', False)
        ])
        requests_to_update = all_requests.filtered(
            lambda r: r.states.id not in excluded_ids
        )

        # Actualización masiva por lotes (más eficiente)
        for rec in requests_to_update:
            delta = (today - rec.date_request).days
            rec.write({'day_passed_count': delta})  # o rec.day_passed_count = delta si estás en modo batch

    def desactive_users(self):
        users = self.env['res.users'].search([('user_type', '=', 'client')])
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search(
            [('model', '=', int(model.id)), ('priority', 'not in', (7, 8))])

        professional_request_users = self.env['professional_registers.professional_request'].search(
            [('states', 'in', states.ids)]).mapped('user')

        arra_ids = []
        for register in users:
            if register.login not in professional_request_users:
                arra_ids.append(register.id)

        result_ids = ', '.join(map(str, arra_ids))

        users_default = ['public', '__system__', 'portaltemplate', 'default']

        result_users_ids = ", ".join([f"'{user}'" for user in users_default])
        cr = self.env.cr

        sql_select = """SELECT id FROM res_users
        WHERE create_date is not NULL and  EXTRACT (DAY FROM (NOW() - res_users.create_date)) >= 30 """

        sql_partner_select = """SELECT partner_id FROM res_users
        WHERE create_date is not NULL and  EXTRACT (DAY FROM (NOW() - res_users.create_date)) >= 30 """

        if arra_ids:
            sql_select += f" and id in ({result_ids})"
            sql_partner_select += f" and id in ({result_ids})"
        else:
            sql_select += f" and login not in ({result_users_ids})"
            sql_partner_select += f" and login not in ({result_users_ids})"

        # Utiliza la consulta sql_select directamente en las consultas de eliminación
        sql_update_partner = f"""UPDATE res_partner SET active=False WHERE id in ({sql_partner_select})"""
        sql_update_user = f"""UPDATE res_users SET active=False WHERE id in ({sql_select})"""

        cr.execute(sql_update_partner)
        cr.execute(sql_update_user)

    @api.model
    def _cron_check_detained_requests(self):
        """Cron job para verificar solicitudes detenidas y denegar las que excedan el tiempo."""
        self.check_detained_requests()

    # Auxiliar
    def generate_notifications(self, priority):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        state_priority = self.env['security.state_configuration'].search(
            [('model', '=', int(model.id)), ('priority', '=', int(priority))])

        # Generando la notificacion
        notifications = self.env['notifications.notifications'].search(
            [('model_id', '=', int(model.id)), ('state', '=', int(state_priority.id))])
        msg = ''
        notification_ids = []
        for n in notifications:
            personal = n.persons
            msg = n.notification + ' [' + str(self.request_number) + '] del profesional [' + str(self.full_name) + ']'
            for p in personal:
                user = self.env['res.users'].search([('id', '=', int(p.id))])
                notification_ids.append((0, 0, {
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox'
                }))

        self.env['mail.message'].sudo().create({
            'message_type': "notification",
            'body': msg,
            'subject': "Message subject",
            'notification_ids': notification_ids,
            'partner_ids': [(4, self.env.user.partner_id.id)],
            'model': self._name,
            'res_id': self.id,
        })

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

    def get_older(self, list):
        older = 0
        for li in list:
            value = int(li.request_number)
            if value > older:
                older = value
        return older

    def get_request_number(self):
        requests = self.env['professional_registers.professional_request'].search([])
        if requests:
            tex = self.get_older(requests)
            result = tex + 1
        else:
            result = 1

        return result

    def get_older_inscription(self, list):
        older = 0
        for li in list:
            p = li.inscription_number.split("/")
            value = int(p[0])
            if value > older:
                older = value
        return older

    def get_inscription_number(self):
        domain = []
        result, cad = ['', '0']

        year = datetime.utcnow().date().year
        domain.append(('year', '=', str(year)))
        inscriptions = self.env['professional_registers.inscription'].search([])
        if inscriptions:
            tex = self.get_older_inscription(inscriptions)
            lex = len(str(tex))
            fix = str(tex + 1)
            if len(fix) > lex:
                lex = lex + 1
            cad = cad[:-lex]

            result = cad + str(tex + 1) + '/' + str(year)
        else:
            cad = cad[:-1]
            result = cad + str(1) + '/' + str(year)

        return result

    def generate_insriptions(self, register=None):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 1), ('model', '=', int(model.id))])

        if register != 'automatic':
            register = 'manual'
        inscription_number = self.get_inscription_number()
        certification = True if self.certificate_attachment else False
        expired_date = datetime.utcnow().date()
        inscription_id = self.env['professional_registers.inscription'].create({
            'inscription_number': inscription_number,
            'name': self.name,
            'first_last_name': self.first_last_name,
            'second_last_name': self.second_last_name,
            'full_name': self.full_name,
            'nationality_id': self.nationality_id.id,
            'identity': self.identity,
            'email': self.email,
            'profession': self.profession.id,
            'image': self.image,
            'states': state_priority.id,
            'is_view_datails': False,
            'year': self.year,
            'request_id': self.id,
            'priority': 1,
            'inscription_type': register,
            'certification': certification,
            'date': expired_date,
            'retired': self.retired,
            'user_on_charge': self.user_on_charge if self.states == 6 else None
        })

        self.env['professional_registers.identity'].create({
            'full_name': self.full_name,
            'inscription_number': inscription_number,
            'profession': self.profession.id,
            'inscription_id': inscription_id.id,
            'date': expired_date,
            'image': self.image,
            'image1': self.image,
        })

        self.write({
            'inscription_id': inscription_id.id,
            'states': self.states.id,
        })

    def get_string_state(self, priority, model):
        state = self.env['security.state_configuration'].search(
            [('priority', '=', int(priority)), ('model', '=', model)])
        if state:
            return state.name


    def create_traces(self, model, user, msg):
        model = self.env['ir.model'].search([('model', '=', model)])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

    def write(self, vals):

        if self.env.context.get('from_profile_sync'):
            return super(ProfessionalRequest, self).write(vals)

        # Add traces
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Edición de solicitud del profesional No: ' + str(self.request_number)
        self.create_traces('professional_registers.professional_request', user, msg)

        if vals.get('name') or vals.get('first_last_name'):
            request_number = self.request_number

            name = vals.get('name', self.name)
            first_last_name = vals.get('first_last_name', self.first_last_name)

            first_letter = str(name)[:1]
            user = first_letter + str(first_last_name) + str(request_number)
            requests = self.env['professional_registers.professional_request'].search([('user', '=', str(user))])

            if requests:
                requests_ids = self.env['professional_registers.professional_request'].search([])
                request_number = self.get_older(requests_ids) + 1 if requests_ids else 1

            user = first_letter + str(first_last_name) + str(request_number)
            vals['user'] = user

        if vals.get('payment_type') == 'sello':
            inscription_id = vals.get('inscription_id', self.inscription_id.id)
            inscription = self.env['professional_registers.inscription'].search([('id', '=', int(inscription_id))])
            if inscription:
                inscription.write({
                    'payment_type': 'sello',
                    'was_payment': True,
                })

        # register user
        if not self.is_register_online:
            user_get = vals.get('user', self.user)
            user = str(user_get).lower()
            vals['user'] = user
            password = vals.get('password', self.password)
            full_name = vals.get('full_name', self.full_name)
            image = vals.get('image', self.image)
            email = vals.get('email', self.email)

            user_id = False
            if user and password:
                password = self._set_password(password)
                user_id = self.env['res.users'].search([('login', '=', str(user))])
                if not user_id:
                    user_id = self.env['res.users'].create({
                        'name': full_name,
                        'login': str(user).lower(),
                        'image_1920': image,
                        'user_type': 'client',
                    })
                elif vals.get('image'):
                    user_id.write({
                        'image_1920': image
                    })
                partner = self.env['res.partner'].search([('id', '=', int(user_id.partner_id.id))])
                partner.write({
                    'email': email
                })
                if vals.get('password'):
                    user_id._set_encrypted_password(user_id.id, password)

            # ------------------------------------------------------------------
            # Gestión del perfil profesional: actualizar o crear, NUNCA borrar
            # ------------------------------------------------------------------
            # 1. Determinar qué campos del diccionario 'vals' pertenecen al modelo 'profile'
            profile_fields = [
                'name', 'first_last_name', 'second_last_name', 'full_name',
                'nationality_id', 'identity', 'sex', 'address', 'country',
                'country_states', 'city', 'phone', 'email','user', 'password', 'image', 'date', 'retired',
                'company_id', 'year', 'user_id'
            ]

            # 2. Construir un diccionario con los valores que se van a guardar en el perfil
            profile_vals = {}
            for field in profile_fields:
                if field in vals:
                    # Convertir a entero cuando sea necesario (campos Many2one)
                    if field in ['nationality_id', 'country', 'city', 'company_id']:
                        val = vals[field]
                        if val:
                            profile_vals[field] = int(val)
                        else:
                            profile_vals[field] = False
                    elif field in ['country_states']:
                        # country_states puede venir como entero o como False
                        val = vals.get('country_states')
                        if val:
                            profile_vals['country_states'] = int(val)
                        else:
                            profile_vals['country_states'] = False
                    else:
                        profile_vals[field] = vals[field]
                else:
                    # Si no viene en vals, usar el valor actual del registro (self)
                    # solo para los campos que realmente existen en self (evitar error)
                    if hasattr(self, field):
                        current_val = getattr(self, field)
                        # Si es un Many2one, tomar el id
                        if field in ['nationality_id', 'country', 'city', 'company_id',
                                     'country_states']:
                            if current_val:
                                profile_vals[field] = current_val.id
                            else:
                                profile_vals[field] = False
                        else:
                            profile_vals[field] = current_val

            # 3. Buscar el perfil asociado a esta solicitud (si existe)
            profile = self.profile_id  # Asumiendo que 'professional_request' tiene un campo 'profile_id'
            if not profile:
                # Si no hay relación directa, buscar por nombre de usuario (como hacía el original)
                user_login = vals.get('user', self.user)
                profile = self.env['professional_registers.profile'].search([('user', '=', str(user_login))], limit=1)

            # 4. Crear o actualizar el perfil
            if profile:
                profile.with_context(skip_profile_sync=True).write(profile_vals)
            else:
                profile = self.env['professional_registers.profile'].with_context(skip_profile_sync=True).create(profile_vals)
                self.write({'profile_id': profile.id})

            # 5. Gestionar el historial laboral (history_work)
            #    Si viene 'history_work' en vals, actualizar cada línea para que apunte al perfil actual
            if vals.get('history_work'):
                history_data = vals.get('history_work')
                for command in history_data:
                    # Los comandos de one2many son tuples: (0, 0, values) para crear, (1, id, values) para actualizar, etc.
                    if command[0] == 0:  # crear nueva línea
                        if 'profile' not in command[2]:
                            command[2]['profile'] = profile.id
                    elif command[0] == 1:  # actualizar línea existente
                        if 'profile' not in command[2]:
                            command[2]['profile'] = profile.id
                    elif command[0] == 2:  # borrar línea - no necesita perfil
                        pass
                    elif command[0] == 4:  # añadir existente (no usado normalmente)
                        pass
                    # No es necesario forzar perfil en líneas ya existentes porque ya lo tienen
            elif self.history_work and not vals.get('history_work'):
                # Si no se envía history_work pero ya existía, no hacemos nada
                pass
            # ------------------------------------------------------------------

        # Validar documentos
        if 'states' not in vals and self.states.priority != 6:
            documents = vals.get('documents_required')
            if not documents and vals.get('documents_required_registers'):
                documents = vals.get('documents_required_registers')
                vals['documents_required'] = []
            else:
                vals['documents_required_registers'] = []

            if documents:
                validate = False
                validate_all = True
                for d in documents:
                    if d[0] == 0:
                        if d[2]['checked']:
                            validate = True
                        else:
                            validate_all = False
                    elif d[0] == 1:
                        document = self.env['professional_registers.pr_document'].search([('id', '=', int(d[1]))])
                        checked = False
                        document_id = d[2]['documents'] if 'documents' in d[2] else document.documents.id
                        commet = d[2]['commet'] if 'commet' in d[2] else document.commet
                        attachment_ids = d[2]['attachment_ids'] if 'attachment_ids' in d[2] else document.attachment_ids
                        if 'checked' in d[2]:
                            if d[2]['checked']:
                                validate = True
                                checked = True
                            else:
                                validate_all = False
                        else:
                            if document.checked:
                                validate = True
                            else:
                                validate_all = False

                    elif d[0] == 4:
                        document = self.env['professional_registers.pr_document'].search([('id', '=', int(d[1]))])
                        if document.checked:
                            validate = True
                        else:
                            validate_all = False

                if validate_all:
                    model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
                    state_priority = self.env['security.state_configuration'].search(
                        [('priority', '=', 6), ('model', '=', int(model.id))])
                    vals['states'] = state_priority.id
                    vals['priority'] = 6
                    self.generate_notifications(6)
                    self.generate_insriptions()
                elif validate:
                    model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
                    state_priority = self.env['security.state_configuration'].search(
                        [('priority', '=', 3), ('model', '=', int(model.id))])
                    vals['states'] = state_priority.id
                    vals['priority'] = 3
                    self.generate_notifications(3)

        if vals.get('documents_required'):
            self._validate_and_clean_documents(vals.get('documents_required'))
        elif vals.get('documents_required_registers'):
            self._validate_and_clean_documents(vals.get('documents_required_registers'))

            # Update Details
        if 'states' not in vals and (self.states.priority == 3 or self.states.priority == 4) and not 'priority' in vals:
            model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
            state_priority = self.env['security.state_configuration'].search(
                [('priority', '=', 5), ('model', '=', int(model.id))])
            vals['states'] = state_priority.id
            vals['priority'] = 5
            self.generate_notifications(5)

        self.validate_required_documents(vals)

        if not self.is_register_online:
            priority = vals.get('priority') if vals.get('priority') else self.priority
        else:
            priority = 2
        state = self.get_string_state(priority, 'professional_registers.professional_request')
        full_name = vals.get('full_name') if vals.get('full_name') else self.full_name
        request_number = vals.get('request_number') if vals.get('request_number') else self.request_number
        date = vals.get('date_request') if vals.get('date_request') else self.date_request
        identity = vals.get('identity') if vals.get('identity') else self.identity
        email = vals.get('email') if vals.get('email') else self.email
        profession = vals.get('profession') if vals.get('profession') else self.profession.id
        specialties = vals.get('specialties') if vals.get('specialties') else self.specialties.id
        nationality = vals.get('nationality_id') if vals.get('nationality_id') else self.nationality_id.id
        register = self.env['professional_registers.request_help'].search([('request_id', '=', int(self.id))])

        if register:
            register.write({
                'full_name': full_name,
                'request_number': request_number,
                'date': date,
                'profession': int(profession) if profession else False,
                'identity': identity,
                'email': email,
                'speciality': int(specialties) if specialties else False,
                'state': state,
                'nationality_id': int(nationality) if nationality else False,
            })

        sync_fields = [
            'name', 'first_last_name', 'second_last_name', 'full_name',
            'nationality_id', 'identity', 'id_fuc', 'sex', 'address', 'country',
            'country_states', 'city', 'phone', 'email', 'image',
            'retired', 'date', 'teaching_level', 'study_center',
            'profession', 'specialties', 'teaching_category',
            'degree_sciences', 'investigations'
        ]

        # Verificar si hay cambios en campos relevantes
        sync_fields_updated = any(field in vals for field in sync_fields)

        res = super(ProfessionalRequest, self).write(vals)

        # Si se actualizaron campos de sincronización y hay un perfil asociado
        if sync_fields_updated and self.profile_id and self.can_sync:
            # Registrar que esta solicitud tiene datos desactualizados
            self.write({'last_sync_date': False})

            # Notificar al administrador
            self._notify_desync()

        return res

    def unlink(self):
        for reg in self:
            if reg.states.priority != 1 and not reg.force_erase:
                name_state = self.get_string_state(reg.states.priority, 'professional_registers.professional_request')
                msg = 'No se puede eliminar una solicitud del profesional que se encuentra en el estado ' + str(
                    name_state)
                raise exceptions.ValidationError(msg)

            if not reg.is_register_online:
                user_id = reg.id_user_register.id
                user = self.env['res.users'].search([('id', '=', int(user_id))])
                user.unlink()

            # Add traces
            model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
            user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
            msg = 'Eliminación de solicitud del profesional No: ' + str(reg.request_number)

            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': msg
            })
            super(ProfessionalRequest, reg).unlink()

        # Obtener todos los campos del modelo actual
        model_id = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
        fields = self.env['ir.model.fields'].search([('model_id', '=', model_id.id)])

        # Crear líneas del wizard
        wizard_lines = []
        for field in fields:
            wizard_lines.append((0, 0, {
                'model_id': model_id.id,
                'field_id': field.id,
                'is_public': False,
            }))

        # Abrir el wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar Campos Públicos',
            'res_model': 'public.fields.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_solicitud_id': self.id,
                'default_field_ids': wizard_lines,
            },
        }

    @api.constrains('profession')
    def _check_unique_related_id(self):
        for record in self:

            existing_records = self.search([
                ('profession', '=', record.profession.id),
                ('identity', '=', record.identity),
                ('states', '!=', 8)

            ])
            if len(existing_records) > 1:
                raise ValidationError("Ya posee una soilicitud con la misma profesión!!!!!!")

    @api.onchange('documents_required')
    def _onchange_documents_required(self):
        max_size = 5 * 1024 * 1024  # 5 MB en bytes
        oversized_files = []

        for document in self.documents_required:
            for attachment in document.attachment_ids:
                if attachment.datas and len(base64.b64decode(attachment.datas)) > max_size:
                    oversized_files.append(attachment.name)

        if oversized_files:
            raise ValidationError(
                "Los siguientes archivos superan los 5 MB y no pueden ser añadidos:\n- " +
                "\n- ".join(oversized_files)
            )

    def _validate_and_clean_documents(self, documents):
        max_size = 5 * 1024 * 1024  # 5 MB en bytes
        oversized_files = []
        invalid_attachments = []

        for document in documents:
            command = document[0]  # Tipo de comando
            if command in [1, 4]:  # Actualizar o enlazar un registro existente
                doc_id = document[1]
                doc_record = self.env['professional_registers.pr_document'].browse(doc_id)
                for attachment in doc_record.attachment_ids:
                    if attachment.datas and len(base64.b64decode(attachment.datas)) > max_size:
                        oversized_files.append(attachment.name)
                        invalid_attachments.append(attachment)
            elif command == 0:  # Crear un nuevo registro
                new_document_data = document[2]
                if new_document_data and 'attachment_ids' in new_document_data:
                    attachment_ids = new_document_data['attachment_ids'][0][2]
                    attachments = self.env['ir.attachment'].browse(attachment_ids)
                    for attachment in attachments:
                        if attachment.datas and len(base64.b64decode(attachment.datas)) > max_size:
                            oversized_files.append(attachment.name)
                            invalid_attachments.append(attachment)

        # Si hay archivos no válidos, elimínalos y lanza una excepción
        if oversized_files:
            # Elimina archivos no válidos del sistema
            for attachment in invalid_attachments:
                attachment.unlink()

            raise ValidationError(
                "Los siguientes archivos superan los 5 MB y han sido eliminados:\n- " +
                "\n- ".join(oversized_files)
            )

    def get_public_data(self):
        public_fields = self.env['professional_registers.public_field'].search([('active', '=', True)]).mapped(
            'field_name')
        result = {}
        for field in public_fields:
            if hasattr(self, field):
                result[field] = getattr(self, field)
        return result

    @api.model
    def get_public_fields_data(self, domain=None):
        if domain is None:
            domain = []

        # Get configured public fields
        public_fields = self.env['professional_registers.public_field'].search([
            ('active', '=', True)
        ], order='sequence')

        # Separate main fields and detail fields
        main_fields = public_fields.filtered(lambda f: f.is_main_field)
        detail_fields = public_fields.filtered(lambda f: not f.is_main_field)

        # Get records based on domain
        records = self.search(domain)

        result = {
            'main_data': [],
            'detail_fields': [],
            'total_records': len(records)
        }

        # Process records
        for record in records:
            main_record_data = {}
            detail_record_data = {}

            # Process main fields
            for field in main_fields:
                value = record[field.field_name]
                if hasattr(value, 'name'):  # Handle Many2one fields
                    value = value.name
                main_record_data[field.field_name] = {
                    'label': field.field_label,
                    'value': value
                }

            # Process detail fields
            for field in detail_fields:
                value = record[field.field_name]
                if hasattr(value, 'name'):  # Handle Many2one fields
                    value = value.name
                detail_record_data[field.field_name] = {
                    'label': field.field_label,
                    'value': value
                }

            result['main_data'].append(main_record_data)
            if detail_record_data:
                result['detail_fields'].append(detail_record_data)

        return result

    def action_open_public_fields(self):
        self.ensure_one()
        PublicRequest = self.env['professional_registers.public_request']

        # Buscar o crear el registro de campos públicos
        public_fields = PublicRequest.search([('request_id', '=', self.id)], limit=1)
        if not public_fields:
            public_fields = PublicRequest.create({'request_id': self.id})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Campos Públicos',
            'res_model': 'professional_registers.public_request',
            'res_id': public_fields.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'create': False}
        }

    def get_public_data(self):
        public_config = self.env['professional_registers.public_request'].search([('request_id', '=', self.id)],
                                                                                 limit=1)
        if not public_config:
            return {}

        public_data = {}
        for field in public_config._fields:
            if field.startswith('show_') and getattr(public_config, field):
                field_name = field[5:]  # Remove 'show_' prefix
                if hasattr(self, field_name):
                    public_data[field_name] = getattr(self, field_name)

        # Handle required documents
        if public_config.show_required_documents:
            public_data['required_documents'] = self.documents_required.filtered(
                lambda d: d in public_config.show_required_documents
            ).mapped('name')

        return public_data

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

    def validate_required_documents(self, vals):

        """
    Valida que no se eliminen los adjuntos de documentos obligatorios
    cuando el estado es 'En Proceso' o superior
    :param self: Registro actual
    :param vals: Valores que se intentan escribir
    :raise: UserError si se intenta eliminar adjuntos de documentos obligatorios
    """
        # Si no se está modificando documentos o el estado, no validar
        if 'documents_required' not in vals and 'states' not in vals:
            return

        # Obtener el estado actual
        current_state_priority = self.states.priority

        # Solo validar para estados En Proceso (2) o superior, excluyendo Aprobada (6)
        if current_state_priority < 2 or current_state_priority == 6:
            return

        # Obtener documentos actuales (antes de cambios)
        current_docs = self.documents_required

        # Obtener IDs de documentos obligatorios
        required_docs = self.env['nomenclators.documents_required'].search([
            ('is_document_required', '=', True),
            ('procedure1', '=', self.procedure_type.id)
        ]) if self.procedure_type else self.env['nomenclators.documents_required']

        required_doc_ids = required_docs.ids
        required_doc_names = {doc.id: doc.name for doc in required_docs}

        # Si no hay documentos obligatorios, no hay nada que validar
        if not required_doc_ids:
            return

        # Analizar las operaciones propuestas
        proposed_docs = vals.get('documents_required', [])
        invalid_docs = set()

        for operation in proposed_docs:
            op_code = operation[0]
            doc_id = operation[1]

            # Solo nos interesan operaciones de actualización (1)
            if op_code == 1:
                changes = operation[2]
                if 'attachment_ids' in changes:
                    # Buscar el documento en los actuales
                    document = current_docs.filtered(lambda d: d.id == doc_id)
                    if document.documents.id in required_doc_ids:
                        attachment_operation = changes['attachment_ids']
                        # Verificar diferentes formatos de operación
                        if attachment_operation and attachment_operation[0][0] == 6:
                            invalid_docs.add(document.documents.id)

        # Si hay documentos obligatorios afectados
        if invalid_docs:
            doc_names = [required_doc_names[doc_id] for doc_id in invalid_docs if doc_id in required_doc_names]
            if len(doc_names) == 1:
                message = f"No puedes eliminar los archivos adjuntos del documento obligatorio: {doc_names[0]}. Estado actual: {self.states.name}"
            else:
                docs_list = "\n- ".join(doc_names)
                message = (
                    "No puedes eliminar los archivos adjuntos de los siguientes documentos obligatorios:\n"
                    f"- {docs_list}\n"
                    f"Estado actual: {self.states.name}"
                )
            raise UserError(message)

    def go_to_updates(self):
        self.ensure_one()
        updates = self.env['professional_registers.professional_request_update'].search(
            [('original_request_id', '=', self.id)]
        )

        if not updates:
            raise exceptions.ValidationError(
                'No existen solicitudes de actualización para esta solicitud de inscripción.')

        ir_model_data = self.env['ir.model.data']
        try:
            tree_id = \
                ir_model_data.get_object_reference('professional_registers', 'view_professional_request_update_tree')[
                    1]
            form_id = \
                ir_model_data.get_object_reference('professional_registers', 'view_professional_request_update_form')[
                    1]
        except ValueError:
            tree_id = form_id = False

        return {
            'name': f'Solicitudes de Actualización de {self.request_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request_update',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'domain': [('original_request_id', '=', self.id)],
            'context': {'default_original_request_id': self.id}
        }

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         # Personalizar cómo se muestra el registro en el campo many2one
    #         name = f"{record.request_number} -({record.identity}) "
    #         result.append((record.id, name))
    #     return result

    def create_claim(self):
        """Crear una reclamación para esta solicitud"""
        self.ensure_one()

        # Verificar que la solicitud esté denegada o cancelada
        if self.states.priority not in [7, 8]:  # IDs para cancelado y denegado
            raise ValidationError("Solo se pueden crear reclamaciones para solicitudes denegadas o canceladas")

        profile = self.profile_id or self.env['professional_registers.profile'].search(
            [('identity', '=', self.identity)], limit=1)

        # Abrir formulario para crear reclamación
        return {
            'name': 'Crear Reclamación',
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.claim_request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_original_request_id': self.id,
                'default_profile_id': profile.id,
                'default_claim_type': 'denied' if self.states.priority == 8 else 'cancelled'
            }
        }

    def create_update_request(self):
        """Crear la solicitud de actualización"""
        self.ensure_one()

        profile = self.profile_id or self.env['professional_registers.profile'].search(
            [('identity', '=', self.identity)], limit=1)

        # Preparar valores para la creación
        vals = {
            'original_request_id': self.id,
            'profile_id': profile.id
        }

        # Crear la solicitud de actualización
        update_request = self.env['professional_registers.professional_request_update'].create(vals)

        # Abrir la vista de formulario
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request_update',
            'res_id': update_request.id,
            'view_mode': 'form',
            'target': 'current',

            'context': {'form_view_initial_mode': 'edit'}
        }

    def _notify_desync(self):
        """Notifica sobre una solicitud desincronizada"""
        message = f"La solicitud {self.request_number} tiene datos desactualizados respecto al perfil {self.profile_id.full_name}"

        # Notificar a los usuarios con permisos de administración
        admin_users = self.env['res.users'].search([
            ('groups_id', 'in', [
                self.env.ref('base.group_system').id,
                self.env.ref('security.group_professional_superadmin').id
            ])
        ])

        for user in admin_users:
            self.env['mail.message'].sudo().create({
                'message_type': "notification",
                'body': message,
                'subject': "Solicitud Desincronizada",
                'model': self._name,
                'res_id': self.id,
                'partner_ids': [(4, user.partner_id.id)],
            })

    def action_sync_with_profile(self):
        """Sincroniza manualmente esta solicitud con su perfil asociado"""
        if not self.profile_id:
            raise exceptions.ValidationError("No hay perfil asociado a esta solicitud.")

        if not self.can_sync:
            raise exceptions.ValidationError(
                "No se puede sincronizar una solicitud en estado de validación o aprobada.")

        # Campos que se sincronizarán
        sync_fields = {
            'name': self.profile_id.name,
            'first_last_name': self.profile_id.first_last_name,
            'second_last_name': self.profile_id.second_last_name,
            'full_name': self.profile_id.full_name,
            'nationality_id': self.profile_id.nationality_id.id if self.profile_id.nationality_id else False,
            'identity': self.profile_id.identity,
            'id_fuc': self.profile_id.id_fuc,

            'email': self.profile_id.email,
            'image': self.profile_id.image,

        }

        # Actualizar la solicitud
        self.write(sync_fields)

        # Actualizar la fecha de sincronización
        self.write({'last_sync_date': fields.Datetime.now()})

        # Registrar el evento
        self.env['professional_registers.profile_sync_log'].create({
            'profile_id': self.profile_id.id,
            'source_model': self._name,
            'source_id': self.id,
            'inscriptions_updated': 1,
            'details': f"Sincronización manual de la solicitud {self.request_number}",
            'sync_type': 'manual',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': 'La solicitud ha sido sincronizada con el perfil.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_request_model_id(self):
        """Obtiene el ir.model.id para este modelo."""
        return self.env['ir.model'].search([('model', '=', self._name)], limit=1).id

    def _ensure_state_configuration(self, priority):
        """Devuelve el state_configuration para una prioridad dada."""
        model_id = self._get_request_model_id()
        if not model_id:
            raise UserError(_("Modelo no registrado en ir.model"))

        state = self.env['security.state_configuration'].search([
            ('priority', '=', priority),
            ('model', '=', model_id)
        ], limit=1)

        if not state:
            raise UserError(_(
                "No se encontró un estado configurado con prioridad %(priority)s para el modelo '%(model)s'.\n"
                "Verifique la configuración en Ajustes > Estados."
            ) % {'priority': priority, 'model': self._name})

        return state

    def _create_or_link_user(self, vals):

        # Verificar si ya existe
        existing = self.env['res.users'].search([('identification', '=', vals.get('identity'))], limit=1)
        if existing:
            return existing.id

        # Crear nuevo usuario
        user_vals = {
            'name': vals.get('full_name'),
            'login': vals.get('user'),
            'user_type': 'client',
            'identification': vals.get('identity'),
            'image_1920': vals.get('image'),
        }
        user = self.env['res.users'].create(user_vals)

        # Asignar email al partner
        if vals.get('email'):
            user.partner_id.email = vals['email']

        # Asignar grupo "Cliente"
        client_group = self.env['res.groups'].search([('name', '=', 'Cliente')], limit=1)  # Ajusta el XML ID
        if client_group:
            user.groups_id |= client_group

        # Establecer contraseña
        # Cifrar la contraseña manualmente
        if vals.get('password'):
            encrypted_pw = self._set_password(vals['password'])  # ← Devuelve hash
            user._set_encrypted_password(user.id, encrypted_pw)

        return user

    def _create_or_update_profile(self, vals, user_id=False):
        """Crea o actualiza el perfil del profesional."""
        profile = self.env['professional_registers.profile'].search([
            ('identity', '=', vals.get('identity'))
        ], limit=1)

        if not profile:
            profile_vals = {
                'name': vals.get('name'),
                'first_last_name': vals.get('first_last_name'),
                'second_last_name': vals.get('second_last_name'),
                'full_name': vals.get('full_name'),
                'nationality_id': vals.get('nationality_id'),
                'identity': vals.get('identity'),
                'sex': vals.get('sex'),
                'address': vals.get('address'),
                'country': vals.get('country'),
                'country_states': vals.get('country_states'),
                'city': vals.get('city'),
                'phone': vals.get('phone'),
                'email': vals.get('email'),
                'user': vals.get('user'),
                'password': vals.get('password'),
                'image': vals.get('image'),
                'retired': vals.get('retired'),
                'history_work': vals.get('history_work'),
                'professional_language': vals.get('professional_language'),
                'user_id': self.env.uid,
                'id_user_register': user_id,
                'company_id': vals.get('company_id', self.env.company.id),
            }

            profile = self.env['professional_registers.profile'].create(profile_vals)

        return profile

    def _determine_priority_and_state(self, vals):
        """Determina prioridad y estado según documentos."""

        return 1, self._ensure_state_configuration(1)

    def _create_request_help(self, request):
        """Crea el registro auxiliar request_help."""
        state_str = self.get_string_state(request.priority, self._name)  # asumo que existe
        self.env['professional_registers.request_help'].create({
            'full_name': request.full_name,
            'request_number': request.request_number,
            'date': fields.Date.today(),
            'profession': request.profession.id if request.profession else False,
            'identity': request.identity,
            'email': request.email,
            'speciality': request.specialties.id if request.specialties else False,
            'nationality_id': request.nationality_id.id if request.nationality_id else False,
            'state': state_str,
            'request_id': request.id,
        })

    def _log_trace(self, description):
        """Registra una traza de seguridad."""
        model_id = self._get_request_model_id()
        self.env['security.traces'].create({
            'register_time': fields.Datetime.now(),
            'user': self.env.user.name,
            'model': model_id,
            'description': description,
        })

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        records = self.env['professional_registers.professional_request']
        creation_origin = self.env.context.get('creation_origin')

        for vals in vals_list:
            # 1. Preparar valores básicos
            vals['company_id'] = vals.get('company_id', self.env.company.id)
            vals['date_request'] = vals.get('date_request', fields.Date.today())
            vals['year'] = fields.Date.today().year
            vals['procedure_type'] = self.get_procedure_default()
            if creation_origin == 'profile':
                # ───────────────────────────────────────
                # FLUJO: Creación desde perfil existente
                # ───────────────────────────────────────

                profile = self.env['professional_registers.profile'].search([('identity', '=', vals.get('identity'))],
                                                                            limit=1)
                if not profile.exists():
                    raise UserError(_("Perfil no encontrado."))

                # Copiar datos del perfil
                vals.update({
                    'name': profile.name,
                    'first_last_name': profile.first_last_name,
                    'second_last_name': profile.second_last_name,
                    'full_name': profile.full_name,
                    'nationality_id': profile.nationality_id.id,
                    'identity': profile.identity,
                    'sex': profile.sex,
                    'address': profile.address,
                    'country': profile.country.id,
                    'country_states': profile.country_states.id,
                    'city': profile.city.id,
                    'phone': profile.phone,
                    'email': profile.email,
                    'user': profile.user,
                    'password': profile.password,
                    'image': profile.image,
                    'retired': profile.retired,
                    'history_work': profile.history_work,
                    'professional_language': profile.professional_language,
                })

            else:
                # ───────────────────────────────────────
                # FLUJO: request_minimal (o cualquier otro)
                # ───────────────────────────────────────
                # Crear/obtener usuario
                user_id = self._create_or_link_user(vals)
                vals['id_user_register'] = user_id.id

                # Crear/actualizar perfil
                profile = self._create_or_update_profile(vals, user_id=user_id.id)

            # 2. Determinar prioridad y estado (igual para ambos)
            priority, state = self._determine_priority_and_state(vals)
            vals['priority'] = priority
            vals['states'] = state.id
            vals['profile_id'] = profile.id

            # 3. Número de solicitud
            if not vals.get('request_number'):
                vals['request_number'] = self.get_request_number()

            # 4. Crear la solicitud
            record = super(ProfessionalRequest, self).create(vals)
            records += record

            # 5. Post-creación
            self._create_request_help(record)
            self._log_trace(f"Creación de solicitud del profesional No: {record.request_number}")

        return records

    def check_detained_requests(self):
        # Buscar el estado detenido (priority=4) y denegado (priority=8) para el modelo professional_request
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        detained_state = self.env['security.state_configuration'].search([
            ('model', '=', model.id),
            ('priority', '=', 4)
        ], limit=1)
        denied_state = self.env['security.state_configuration'].search([
            ('model', '=', model.id),
            ('priority', '=', 8)
        ], limit=1)

        if not detained_state or not denied_state:
            # Si no se encuentran los estados, no hacer nada
            return

        # Buscar todas las solicitudes en estado detenido
        detained_requests = self.search([('states', '=', detained_state.id)])

        for request in detained_requests:
            # Buscar el último historial de cambio a estado detenido para esta solicitud
            last_detained_history = self.env['professional_registers.professional_request_history'].search([
                ('request_id', '=', request.id),
                ('state_id_new', '=', detained_state.id)
            ], order='date desc', limit=1)
            print(request)
            print(last_detained_history)

            if last_detained_history:
                # Calcular los días desde que se detuvo
                detained_date = last_detained_history.date
                today = fields.Datetime.now()
                days_detained = (today - detained_date).days

                if days_detained > last_detained_history.counter:  # Límite de 30 días last_detained_history.counter
                    # Cambiar el estado a denegado
                    request.write({
                        'states': denied_state.id,
                        'priority': 8
                    })

                    # Registrar en el historial
                    self.env['professional_registers.professional_request_history'].create({
                        'request_id': request.id,
                        'state_id': denied_state.id,
                        'user_id': self.env.user.id,
                        'date': today,
                        'observation': 'Denegado automáticamente por exceder el tiempo máximo de detención'
                    })

                    # Enviar correo
                    self._send_denial_email(request, 'Pasado el término establecido para su arreglo o subsanación')

        # También podríamos considerar las suspensiones por tipo de trámite, pero el requerimiento no lo menciona.
        # Por ahora, solo las detenciones individuales.

    def _send_denial_email(self, request, reason):
        # Enviar correo de denegación
        # Usar la plantilla de correo que se usa en el wizard de denegación, pero con la razón fija.
        # Podemos crear una plantilla de correo para este caso, o usar la misma que el wizard.

        # Buscar la plantilla de correo para denegación

        # Crear el cuerpo del correo manualmente
        body_html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.5;">
                <h2 style="color: #2c3e50;">Notificación de Denegación</h2>
                <p>Estimado/a {request.full_name},</p>
                <p>Le informamos que su solicitud <strong>{request.request_number}</strong> ha sido denegada.</p>
                <p><strong>Razón:</strong> {reason}</p>

                <h3 style="color: #2c3e50; margin-top: 20px;">Detalles de la Solicitud:</h3>
                <ul>
                    <li><strong>Número:</strong> {request.request_number}</li>
                    <li><strong>Tipo:</strong> {request.procedure_type.name}</li>
                    <li><strong>Fecha:</strong> {request.date_request}</li>
                </ul>

                <p style="margin-top: 20px;">
                    Puede consultar el estado de su solicitud en cualquier momento accediendo al sistema.
                </p>

                <p style="margin-top: 30px; font-size: 0.9em; color: #7f8c8d;">
                    Este es un mensaje automático, por favor no responda directamente a este correo.
                </p>
            </div>
            """

        # Sanitizar el HTML (opcional, pero recomendado)
        sanitized_html = html_sanitize(body_html)

        # Preparar valores del correo
        mail_values = {
            'subject': f"Denegación de Solicitud - {request.request_number}",
            'body_html': sanitized_html,
            'email_to': request.email,
            'email_from': self.env.user.email or self.env.company.email,
            'model': self._name,
            'res_id': request.id,
        }

        # Crear y enviar el correo
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
