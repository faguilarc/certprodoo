# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DigitalSignatureWizard(models.TransientModel):
    _name = 'digital.signature.wizard'
    _description = 'Asistente de Solicitud de Firma Digital'

    # Referencia a la inscripción
    inscription_id = fields.Many2one(
        'professional_registers.inscription',
        string='Inscripción',
        required=True
    )
    config_id = fields.Many2one(
        'digital.signature.config',
        string='Configuración',
        required=True,

    )

    # Datos de la solicitud
    level = fields.Selection([
        ('personal', 'Nivel Personal'),
        ('institution', 'Nivel Institución')
    ], string='Nivel', required=True, default='personal')

    request_type = fields.Selection([
        ('affiliation', 'Filiación'),
        ('renewal', 'Renovación')
    ], string='Tipo de Solicitud', required=True, default='affiliation')

    terms_accepted = fields.Boolean('Acepto los términos y condiciones')
    terms_accepted_date = fields.Datetime(
        'Fecha de Aceptación',
        default=fields.Datetime.now
    )

    # Campos de visualización (Snapshot)
    disp_name = fields.Char('Nombre y Apellidos', compute='_compute_display_data', store=False)
    disp_identity = fields.Char('CI / Pasaporte', compute='_compute_display_data', store=False)
    disp_email = fields.Char('Correo Electrónico', compute='_compute_display_data', store=False)
    disp_profession = fields.Char('Profesión', compute='_compute_display_data', store=False)
    disp_specialty = fields.Char('Especialidad', compute='_compute_display_data', store=False)
    disp_organism = fields.Char('Organismo', compute='_compute_institution_data', store=False)
    disp_entity = fields.Char('Empresa / Entidad', compute='_compute_institution_data', store=False)
    disp_job = fields.Char('Cargo', compute='_compute_institution_data', store=False)
    disp_has_history = fields.Boolean('Tiene Historial Laboral', compute='_compute_institution_data', store=False)

    # Campos relacionados para visibilidad
    conf_show_name = fields.Boolean(string='Mostrar Nombre', default=False)
    conf_show_identity = fields.Boolean(string='Mostrar Identidad', default=False)
    conf_show_email = fields.Boolean(string='Mostrar Email', default=False)
    conf_personal_show_profession = fields.Boolean(string='Mostrar Profesión (Personal)', default=False)
    conf_personal_show_specialty = fields.Boolean(string='Mostrar Especialidad (Personal)', default=False)
    conf_inst_show_profession = fields.Boolean(string='Mostrar Profesión (Institución)', default=False)
    conf_inst_show_specialty = fields.Boolean(string='Mostrar Especialidad (Institución)', default=False)
    conf_inst_show_organism = fields.Boolean(string='Mostrar Organismo', default=False)
    conf_inst_show_entity = fields.Boolean(string='Mostrar Entidad', default=False)
    conf_inst_show_job = fields.Boolean(string='Mostrar Cargo', default=False)
    terms_display = fields.Html(string='Terminos y Condiciones', readonly=True)

    @api.depends('inscription_id', 'config_id')
    def _compute_display_data(self):
        for rec in self:
            if rec.inscription_id:
                rec.disp_name = rec.inscription_id.full_name
                rec.disp_identity = rec.inscription_id.identity
                rec.disp_email = rec.inscription_id.email
                rec.disp_profession = rec.inscription_id.profession.name if rec.inscription_id.profession else ''
                rec.disp_specialty = rec.inscription_id.specialties.name if rec.inscription_id.specialties else ''
            else:
                rec.disp_name = rec.disp_identity = rec.disp_email = ''
                rec.disp_profession = rec.disp_specialty = ''

    @api.depends('inscription_id', 'inscription_id.profile_id')
    def _compute_institution_data(self):
        for rec in self:
            rec.disp_organism = rec.disp_entity = rec.disp_job = ''
            rec.disp_has_history = False

            if rec.inscription_id and rec.inscription_id.profile_id:
                history = rec.inscription_id.profile_id.history_work
                if history:
                    rec.disp_has_history = True
                    last_job = history[0]
                    if last_job:
                        rec.disp_organism = last_job.organism.name or ''
                        rec.disp_entity = last_job.work_center or ''
                        rec.disp_job = last_job.activity or ''

    @api.onchange('level')
    def _onchange_level(self):
        self._compute_display_data()
        self._compute_institution_data()



    def action_send_request(self):
        self.ensure_one()

        # Validaciones
        if not self.terms_accepted:
            raise UserError(_("Debe aceptar los términos y condiciones para continuar."))

        if self.level == 'institution' and not self.disp_has_history:
            raise ValidationError(_(
                "Para el nivel Institución, es necesario tener datos laborales registrados "
                "en su perfil. Por favor actualice su historial laboral."
            ))

        # Crear registro de solicitud
        request_vals = {
            'inscription_id': self.inscription_id.id,
            'config_id': self.config_id.id,
            'level': self.level,
            'request_type': self.request_type,
            'terms_accepted': True,
            'terms_accepted_date': fields.Datetime.now(),
            'terms_html': self.config_id.terms_html,
            # Snapshot de datos
            'snapshot_name': self.disp_name,
            'snapshot_identity': self.disp_identity,
            'snapshot_email': self.disp_email,
            'snapshot_profession': self.disp_profession,
            'snapshot_specialty': self.disp_specialty,
            'snapshot_organism': self.disp_organism,
            'snapshot_entity': self.disp_entity,
            'snapshot_job': self.disp_job,
        }

        request = self.env['digital.signature.request'].create(request_vals)
        request.action_submit()  # Cambia estado y envía email

        # Mensaje de éxito
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'digital.signature.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'readonly'},
        }

    @api.model
    def default_get(self, fields_list):
        """Sobrescribe para obtener la inscripción del contexto"""
        res = super().default_get(fields_list)

        # Obtener inscription_id del contexto si está presente
        context = self.env.context
        if context.get('default_inscription_id'):
            res['inscription_id'] = context.get('default_inscription_id')

        # Obtener config_id del contexto si está presente
        config_id = False
        if context.get('default_config_id'):
            config_id = context.get('default_config_id')
            res['config_id'] = config_id

        # Si tenemos una configuración, mapeamos sus valores a los campos del wizard
        if config_id:
            config = self.env['digital.signature.config'].browse(config_id)
            if config.exists():
                # Mapeo de campos de configuración a los campos del wizard
                config_mapping = {
                    'conf_show_name': config.conf_show_name,
                    'conf_show_identity': config.conf_show_identity,
                    'conf_show_email': config.conf_show_email,
                    'conf_personal_show_profession': config.conf_personal_show_profession,
                    'conf_personal_show_specialty': config.conf_personal_show_specialty,
                    'conf_inst_show_profession': config.conf_inst_show_profession,
                    'conf_inst_show_specialty': config.conf_inst_show_specialty,
                    'conf_inst_show_organism': config.conf_inst_show_organism,
                    'conf_inst_show_entity': config.conf_inst_show_entity,
                    'conf_inst_show_job': config.conf_inst_show_job,
                    'terms_display': config.terms_html,
                }

                # Solo establecemos los campos que están en fields_list
                for field, value in config_mapping.items():
                    if field in fields_list:
                        res[field] = value

        return res

