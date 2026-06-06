# -*- coding: utf-8 -*-
from datetime import datetime

from lxml import etree

from odoo import models, fields, api, exceptions


class DetentionCause(models.Model):
    _name = 'nomenclators.detention_causes'
    _description = 'Nomenclador de Causas'

    name = fields.Char('Nombre*')
    description = fields.Char('Descripción*')
    cause_type = fields.Selection([
        ('detention', 'Detención'),
        ('denial', 'Denegación'),
        ('cancellation', 'Cancelación')
    ], string='Tipo de Causa*', required=True)
    
    email_template = fields.Html('Plantilla de Correo')
    document_template = fields.Html('Plantilla de Documento')
    
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Ya existe una causa con el mismo nombre!'),
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(DetentionCause, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DetentionCause, self).fields_view_get(view_id=view_id,
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

        res = super(DetentionCause, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):
        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.detention_causes')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de causa de detención satisfactoria.'
        })

        return super(DetentionCause, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.detention_causes')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de causa de detención satisfactoria.'
        })
        return super(DetentionCause, self).write(vals)

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
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.detention_causes')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de causa de detención satisfactoria.'
        # if count > 1:
        #     msg = 'Eliminación de idiomas del profesional satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(DetentionCause, self).unlink()

    @api.constrains('name', 'description')
    def _check_fields(self):
        for record in self:
            # Validaciones para el nombre
            if record.name:
                if len(record.name) < 3:
                    raise exceptions.ValidationError('El nombre debe tener al menos 3 caracteres')
                if len(record.name) > 100:
                    raise exceptions.ValidationError('El nombre no puede exceder los 100 caracteres')
                if record.name.startswith(' '):
                    raise exceptions.ValidationError('El nombre no puede comenzar con espacios')
                if not record.name.replace(' ', '').replace('-', '').isalnum():
                    raise exceptions.ValidationError('El nombre solo puede contener letras, números, espacios y guiones')

            # Validaciones para la descripción
            if record.description:
                if len(record.description) < 10:
                    raise exceptions.ValidationError('La descripción debe tener al menos 10 caracteres')
                if len(record.description) > 255:
                    raise exceptions.ValidationError('La descripción no puede exceder los 255 caracteres')
                if record.description.startswith(' '):
                    raise exceptions.ValidationError('La descripción no puede comenzar con espacios')