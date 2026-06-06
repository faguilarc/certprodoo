# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree

class ProfessionalRegisters(models.Model):
    _name = 'professional_registers.inscription'
    _description = 'Inscripciones'
    _rec_name = 'inscription_number'

    inscription_number = fields.Char('Nro. Inscripción')
    name = fields.Char('Nombre')
    first_last_name = fields.Char('Primer apellido')
    second_last_name = fields.Char('Segundo apellido')

    full_name = fields.Char('Nombre y apellidos')

    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")

    identity = fields.Char('CI o pasaporte')
    email = fields.Char('Correo')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")


    image = fields.Image("Foto", max_width=1920, max_height=1920)

    date = fields.Date('Fecha de inscripción')

    def _get_states(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        arra_ids = []

        states = self.env['security.state_configuration'].search([('model', '=', int(model.id))], order="priority asc")
        for e in states:
            arra_ids.append(e.id)
        return [('id', 'in', arra_ids)]
    states = fields.Many2one('security.state_configuration', string='Estados', domain=_get_states)

    priority = fields.Integer('prioridad', default=1)

    is_view_datails = fields.Boolean('Vista', default=False)

    request_id = fields.Many2one('professional_registers.professional_request',string="Solicitud")
    specialties = fields.Many2one('nomenclators.specialties', related='request_id.specialties')

    sex = fields.Selection(related='request_id.sex', store=True)
    country_state = fields.Many2one('res.country.state', related='request_id.country_states', store=True)

    year = fields.Char('Año')
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario registrador")

    inscription_type = fields.Selection([('manual', 'Manual'),
                                         ('automatic', 'Automática')], string="Tipo de inscripción")

    side_notes_list = fields.One2many('professional_registers.side_notes', 'inscription', string="Notas al margen")

    certification = fields.Boolean('Certificación')
    certificate_attachment = fields.Many2many('ir.attachment', string="Certificación")
    force_erase = fields.Boolean('Borrar forzado', default=False)

    was_payment = fields.Boolean('Pagado', default=False)
    payment_type = fields.Selection([('exonerado', 'Exonerado'),
                                     ('sello', 'Sello'),
                                     ('no_pagado', 'No pagado'),
                                     ('pagado', 'Pagado')], string="Pago", default='no_pagado')

    id_transaction = fields.Char('Id de transacción', size=15)

    user_on_charge = fields.Many2one('res.users', string="Responsable")
    retired = fields.Boolean('Jubilado', default=False)

    history_ids = fields.One2many(
        'professional_registers.inscription_history',
        'inscription_id',
        string='Histórico de Cambios de Estado'
    )

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente')

    profile_id = fields.Many2one(
        'professional_registers.profile',
        string='Perfil Asociado',
        compute='_compute_profile_id',
        store=True
    )

    @api.depends('identity')
    def _compute_profile_id(self):
        for record in self:
            if record.identity:
                profile = self.env['professional_registers.profile'].search([
                    ('identity', '=', record.identity)
                ], limit=1)
                record.profile_id = profile.id if profile else False
            else:
                record.profile_id = False

    last_sync_date = fields.Datetime(
        'Última Sincronización',
        readonly=True,
        help="Fecha de la última sincronización con el perfil"
    )

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(ProfessionalRegisters, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'image', 'was_payment',
                   'priority', 'is_view_datails', 'certificate_attachment', 'force_erase', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def default_get(self, fields_list):
        id_inscription = self._context.get('id_inscription')
        if id_inscription:
            inscription = self.env['professional_registers.inscription'].search([('id', '=', int(id_inscription))])
            return {
                'is_view_datails': True,
                'inscription_number': inscription.inscription_number,
                'name': inscription.name,
                'first_last_name': inscription.first_last_name,
                'second_last_name': inscription.second_last_name,
                'full_name': inscription.full_name,
                'nationality_id': inscription.nationality_id.id,
                'identity': inscription.identity,
                'email': inscription.email,
                'profession': inscription.profession.id,
                'request_id': inscription.request_id.id,
                'inscription_type': inscription.inscription_type,
                'company_id': inscription.company_id.id,
                'user_id': inscription.user_id.id,
                'year': inscription.year,
                'states': inscription.states.id,
                'priority': inscription.priority,
            }
        else:
            return super(ProfessionalRegisters, self).default_get(fields_list)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProfessionalRegisters, self).fields_view_get(view_id=view_id,
                                                               view_type=view_type,
                                                               toolbar=toolbar,
                                                               submenu=submenu)

        user = self.env['res.users'].search([('id', '=', self.env.uid)])
        doc = etree.XML(res['arch'])

        for btn in doc.xpath("//button[@name='cancel']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('cancel_inscription', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        for btn in doc.xpath("//button[@name='reset']"):
            pe = self.env['security.permits_state'].sudo().search([('user', '=', user.id), ('reset_inscription', '=', True)])
            if not pe:
                btn.set("invisible", "1")
                modifiers = json.loads(btn.get("modifiers"))
                modifiers['invisible'] = True
                btn.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc)
        return res

    #Buttons
    def go_to_inscription(self):
        inscription = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(self.id))])
        if inscription:
            ir_model_data = self.env['ir.model.data']
            form_id = True
            ctx = []
            try:
                form_id = (
                ir_model_data.get_object_reference('professional_registers', 'inscription_help_form_view')[1])
            except ValueError:
                form_id = False

            ctx = {
                'id_inscription': inscription.id,
                'ins_id': self.id
            }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'professional_registers.inscriptions_help',
                'name': 'Inscripción del profesional',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                # 'res_id': request.id,
                'target': 'new',
                'context': ctx,
                # 'clear_breadcrumbs': True,
            }

    def go_to_identity(self):
        identity = self.env['professional_registers.identity'].search([('inscription_id', '=', int(self.id))])
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

    def report_inscription(self):
        if self.states.priority != 2:
            email = self.email if self.email else ''
            # nationality = 'Cubano'
            # if self.nationality_id.name != 'Cubano':
            #     nationality = 'Extranjero'

            nationality = self.nationality_id.name

            inscription_model_help = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(self.id))])
            logo = self.env['nomenclators.logo'].sudo().search([('name', '=', 'Escudo')])
            data = {
                'request_number': self.inscription_number,
                'id_transaction': self.id_transaction,
                'identity': self.identity,
                'nationality': nationality,
                'email': email,
                'profession': self.profession.id,
                'profession_name': self.profession.name,
                'retired': 'Si' if self.retired else 'No',
                'state': self.states.name,
                'tramit_type': 'Solicitud',
                'date': inscription_model_help.date,
                'days': inscription_model_help.date.day,
                'month': inscription_model_help.date.month,
                'year': inscription_model_help.date.year,
                'full_name': inscription_model_help.full_name,
                'company': logo[0],
            }
            return self.env.ref('professional_registers.inscriptions_detail').report_action(self, data)

    def cancel(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 2), ('model', '=', int(model.id))])

        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        self.env['professional_registers.inscription_history'].create({
            'inscription_id': self.id,
            'state_id': self.states.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 2,
            'user_on_charge': self.env.uid
        })

        register = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(self.id))])
        state = self.get_string_state(state_priority.priority, 'professional_registers.inscription')
        if register:
            register.write({
                'state': state,
            })

        self.generate_notifications(2)

    def reset(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        state_priority = self.env['security.state_configuration'].search(
            [('priority', '=', 1), ('model', '=', int(model.id))])

        current_date = datetime.utcnow().date().strftime('%Y-%m-%d')
        self.env['professional_registers.inscription_history'].create({
            'inscription_id': self.id,
            'state_id': self.states.id,
            'user_id': self.env.user.id,
            'date': current_date,
            'observation': f"Cambio de estado a {self.env['security.state_configuration'].browse(state_priority.id).name}"
        })

        self.write({
            'states': state_priority.id,
            'priority': 1,
            'user_on_charge': self.env.uid
        })

        register = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(self.id))])
        state = self.get_string_state(state_priority.priority, 'professional_registers.inscription')
        if register:
            register.write({
                'state': state,
            })


        self.generate_notifications(1)

    #Auxiliar
    def generate_notifications(self, priority):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        state_priority = self.env['security.state_configuration'].search(
            [('model', '=', int(model.id)), ('priority', '=', int(priority))])

        # Generando la notificacion
        notifications = self.env['notifications.notifications'].search(
            [('model_id', '=', int(model.id)), ('state', '=', int(state_priority.id))])
        msg = ''
        notification_ids = []
        for n in notifications:
            personal = n.persons
            msg = n.notification + ' [' + str(self.full_name) + '] '
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

    def get_string_state(self, priority, model):
        state = self.env['security.state_configuration'].search(
            [('priority', '=', int(priority)), ('model', '=', model)])
        if state:
            return state.name

    @api.model
    def create(self, vals_list):

        vals_list["user_id"] = self.env.uid
        user_id = self.env['res.users'].search([('id', '=', int(self.env.uid))])

        vals_list['company_id'] = user_id.company_id.id
        vals_list['year'] = datetime.now().year

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])

        user_name = 'System'
        if vals_list.get('inscription_type') == 'manual':
            user_name = user.name

        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user_name,
            'model': model.id,
            'description': 'Creación de inscripción No: ' + str(vals_list.get('inscription_number'))
        })
        res = super(ProfessionalRegisters, self).create(vals_list)

        # Create Details
        state = self.get_string_state(res['priority'], 'professional_registers.inscription')
        self.env['professional_registers.inscriptions_help'].create({
            'full_name': res['full_name'],
            'inscription_number': res['inscription_number'],
            'date': datetime.now().date(),
            'profession': int(res['profession']),
            'identity': res['identity'],
            'email': res['email'],
            'nationality_id': int(res['nationality_id']),
            'state': state,
            'inscription_id': res.id
        })
        inscription = res

        # Asociar al expediente de la solicitud original
        if inscription.request_id and inscription.request_id.expedient_id:
            inscription.write({'expedient_id': inscription.request_id.expedient_id.id})

            # Agregar al historial del expediente
            inscription.expedient_id._add_history(
                'Nueva inscripción creada',
                f'Se ha creado la inscripción {inscription.inscription_number} para la solicitud {inscription.request_id.request_number}'
            )

        return inscription

    def write(self, vals):

        if vals.get('certificate_attachment'):
            vals['certification'] = True

            request = self.env['professional_registers.professional_request'].search([('id', '=', int(self.request_id.id))])
            request.write({
                'certification': True,
                'certificate_attachment': vals.get('certificate_attachment'),
                'priority': 6
            })

        if vals.get('id_transaction'):
            vals['payment_type'] = 'pagado'

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])

        user_name = 'System'
        inscription_type = vals.get('inscription_type') if vals.get('inscription_type') else self.inscription_type
        if inscription_type == 'manual':
            user_name = user.name

        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user_name,
            'model': model.id,
            'description': 'Edición de inscripción No: ' + str(self.inscription_number)
        })

        # Update Details
        priority = vals.get('priority') if vals.get('priority') else self.priority
        state = self.get_string_state(priority, 'professional_registers.inscription')
        full_name = vals.get('full_name') if vals.get('full_name') else self.full_name
        inscription_number = vals.get('inscription_number') if vals.get('inscription_number') else self.inscription_number
        # date = vals.get('date_request') if vals.get('date_request') else self.date_request
        identity = vals.get('identity') if vals.get('identity') else self.identity
        email = vals.get('email') if vals.get('email') else self.email
        profession = vals.get('profession') if vals.get('profession') else self.profession.id
        nationality = vals.get('nationality_id') if vals.get('nationality_id') else self.nationality_id.id
        register = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(self.id))])
        register.write({
            'full_name': full_name,
            'inscription_number': inscription_number,
            # 'date': ,
            'profession': int(profession),
            'identity': identity,
            'email': email,
            'state': state,
            'nationality_id': int(nationality),
        })

        # Si se actualizan campos que normalmente se sincronizan, registrar la desconexión temporal
        sync_fields = [
            'name', 'first_last_name', 'second_last_name', 'full_name',
            'nationality_id', 'identity',
             'email', 'image',

        ]

        sync_fields_updated = any(field in vals for field in sync_fields)

        res = super(ProfessionalRegisters, self).write(vals)

        # Si se actualizaron campos de sincronización y hay un perfil asociado
        if sync_fields_updated and self.profile_id:
            # Registrar que esta inscripción tiene datos desactualizados
            self.write({'last_sync_date': False})

            # Notificar al administrador
            self._notify_desync()

        return res

    def unlink(self):
        cantidad_registros = 0
        for reg in self:
            cantidad_registros = cantidad_registros + 1
            if reg.states.priority != 1 and not reg.force_erase:
                name_state = self.get_string_state(reg.state.priority, 'professional_registers.inscription')
                msg = 'No se puede eliminar una inscripción que se encuentra en el estado ' + str(name_state)
                raise exceptions.ValidationError(msg)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación inscripción satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de inscripciones satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(ProfessionalRegisters, self).unlink()

    def _notify_desync(self):
        """Notifica sobre una inscripción desincronizada"""
        message = f"La inscripción {self.inscription_number} tiene datos desactualizados respecto al perfil {self.profile_id.full_name}"

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
                'subject': "Inscripción Desincronizada",
                'model': self._name,
                'res_id': self.id,
                'partner_ids': [(4, user.partner_id.id)],
            })

    def action_sync_with_profile(self):
        """Sincroniza manualmente esta inscripción con su perfil asociado"""
        if not self.profile_id:
            raise exceptions.ValidationError("No hay perfil asociado a esta inscripción.")

        # Campos que se sincronizarán
        sync_fields = {
            'name': self.profile_id.name,
            'first_last_name': self.profile_id.first_last_name,
            'second_last_name': self.profile_id.second_last_name,
            'full_name': self.profile_id.full_name,
            'nationality_id': self.profile_id.nationality_id.id if self.profile_id.nationality_id else False,
            'identity': self.profile_id.identity,


            'email': self.profile_id.email,
            'image': self.profile_id.image,

        }

        # Actualizar la inscripción
        self.write(sync_fields)

        # Actualizar la fecha de sincronización
        self.write({'last_sync_date': fields.Datetime.now()})

        # Registrar el evento
        self.env['professional_registers.profile_sync_log'].create({
            'profile_id': self.profile_id.id,
            'source_model': self._name,
            'source_id': self.id,
            'inscriptions_updated': 1,
            'details': f"Sincronización manual de la inscripción {self.inscription_number}",
            'sync_type': 'manual',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': 'La inscripción ha sido sincronizada con el perfil.',
                'type': 'success',
                'sticky': False,
            }
        }