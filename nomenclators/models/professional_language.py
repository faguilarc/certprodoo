# -*- coding: utf-8 -*-
from datetime import datetime

from lxml import etree

from odoo import models, fields, api, exceptions


class ProfessionalLanguage(models.Model):
    _name = 'nomenclators.professional_language'
    _description = 'Nomenclador de Idiomas'

    language = fields.Many2one(
        'res.lang',
        string='Idioma',
        required=True,
        help="Selecciona el idioma de la lista de idiomas configurados en Odoo."
    )

    proficiency_level = fields.Selection([
        ('basica1', 'Básico A1'),
        ('basica2', 'Básico A2'),
        ('intermediateb1', 'Intermedio B1'),
        ('intermediateb2', 'Intermedio B2'),
        ('advancedc1', 'Avanzado C1'),
        ('advancedc2', 'Avanzado C2'),
        ('fluent', 'Nativo'),
    ], string='Nivel de Dominio', required=True, help="Nivel general de dominio del idioma.")

    speaking = fields.Selection([
        ('none', 'Ninguno'),
        ('basic', 'Básico'),
        ('good', 'Bueno'),
        ('fluent', 'Fluido'),
    ], string='Habilidad Oral', help="Nivel de habilidad al hablar.")

    writing = fields.Selection([
        ('none', 'Ninguno'),
        ('basic', 'Básico'),
        ('good', 'Bueno'),
        ('fluent', 'Fluido'),
    ], string='Habilidad Escrita', help="Nivel de habilidad para escribir.")

    reading = fields.Selection([
        ('none', 'Ninguno'),
        ('basic', 'Básico'),
        ('good', 'Bueno'),
        ('fluent', 'Fluido'),
    ], string='Habilidad Lectora', help="Nivel de habilidad para leer.")

    profesional_request = fields.Many2one('professional_registers.professional_request', string="Solicitud")
    profile = fields.Many2one('professional_registers.profile', string="Perfil")
    # Añadir el campo relacionado con la solicitud de actualización
    update_request = fields.Many2one('professional_registers.professional_request_update',
                                     string="Solicitud de Actualización")
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Ya existe un idiomas del profesional con ese registro!'),
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(ProfessionalLanguage, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProfessionalLanguage, self).fields_view_get(view_id=view_id,
                                                                view_type=view_type,
                                                                toolbar=toolbar,
                                                                submenu=submenu)
        doc = etree.XML(res['arch'])

        if not self.env['res.users'].has_group('security.group_professional_superadmin') and not self.env[
            'res.users'].has_group('security.group_professional_managment') and not self.env['res.users'].has_group(
            'security.group_professional_editor_managment'):
            doc.set('create', '0')
            doc.set('edit', '0')
            doc.set('delete', '0')

        res['arch'] = etree.tostring(doc)

        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user

        # Se verifican los permisos por roles y opciones.

        res = super(ProfessionalLanguage, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):
        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.professional_language')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de idiomas del profesional satisfactoria.'
        })

        return super(ProfessionalLanguage, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.professional_language')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de idiomas del profesional satisfactoria.'
        })
        return super(ProfessionalLanguage, self).write(vals)

    def unlink(self):
        # count = 0
        # for rec in self:
        #     profesional_request = self.env['professional_registers.professional_request'].search(
        #         [('teaching_category', '=', int(rec.id))])
        #     profile = self.env['professional_registers.profile'].search([('teaching_category', '=', int(rec.id))])
        #
        #     if profesional_request or profile:
        #         count = count + 1
        # if count != 0:
        #     msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
        #     if count > 1:
        #         msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'
        #
        #     raise exceptions.ValidationError(msg)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.professional_language')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de idiomas del profesional satisfactoria.'
        # if count > 1:
        #     msg = 'Eliminación de idiomas del profesional satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(ProfessionalLanguage, self).unlink()
