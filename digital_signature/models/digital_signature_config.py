# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DigitalSignatureConfig(models.Model):
    _name = 'digital.signature.config'
    _description = 'Configuración de Solicitud de Firma Digital'
    _inherit = ['mail.thread']

    # Hacerlo singleton
    def _get_default_config(self):
        return self.search([],)

    # Forzar que solo haya un registro
    @api.model
    def create(self, vals):
        if self.search_count([]) >= 1:
            raise UserError(_("Solo puede haber una configuración de firma digital."))
        return super().create(vals)

    @api.model
    def get_active_config(self):
        """Retorna la configuración activa, crea una si no existe"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'admin_email': 'admin@empresa.com',
                'admin_contact': 'Administrador',
                'validity_days': 30,
                'terms_html': '<p>Aceptar términos y condiciones del servicio...</p>',
            })
        return config

    # --- Campos existentes ---
    admin_email = fields.Char('Correo de Administración', required=True, default='admin@empresa.com', tracking=True)
    admin_contact = fields.Char('Contacto Administrativo', help='Nombre o teléfono de contacto')
    validity_days = fields.Integer('Tiempo de Validez (Días)', default=30, required=True, tracking=True)
    terms_html = fields.Html('Términos y Condiciones', required=True,
                             default='<p>Aceptar términos y condiciones del servicio...</p>')

    # Campos booleanos para visibilidad
    conf_show_name = fields.Boolean('Mostrar Nombre y Apellidos', default=True)
    conf_show_identity = fields.Boolean('Mostrar Carnet de Identidad', default=True)
    conf_show_email = fields.Boolean('Mostrar Correo', default=True)
    conf_personal_show_profession = fields.Boolean('Nivel Personal: Mostrar Profesión', default=True)
    conf_personal_show_specialty = fields.Boolean('Nivel Personal: Mostrar Especialidad', default=True)
    conf_inst_show_profession = fields.Boolean('Nivel Institución: Mostrar Profesión', default=True)
    conf_inst_show_specialty = fields.Boolean('Nivel Institución: Mostrar Especialidad', default=True)
    conf_inst_show_organism = fields.Boolean('Nivel Institución: Mostrar Organismo', default=True)
    conf_inst_show_entity = fields.Boolean('Nivel Institución: Mostrar Empresa/Entidad', default=True)
    conf_inst_show_job = fields.Boolean('Nivel Institución: Mostrar Cargo', default=True)

    # Campos adicionales para mejor gestión
    auto_create_request = fields.Boolean(
        'Crear Solicitud Automáticamente',
        default=True,
        help='Crear registro de solicitud al enviar el wizard'
    )
    notify_admin = fields.Boolean(
        'Notificar al Administrador',
        default=True,
        help='Enviar email al administrador cuando se envía una solicitud'
    )
    notify_user = fields.Boolean(
        'Notificar al Usuario',
        default=True,
        help='Enviar email de confirmación al usuario'
    )

    active = fields.Boolean('Activa', default=False)