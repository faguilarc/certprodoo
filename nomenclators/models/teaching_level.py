# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree


class TeachingLevel(models.Model):
    _name = 'nomenclators.teaching_level'
    _description = 'Nivel de enseñanza'
    _rec_name = 'name'

    name = fields.Char('Nombre')
    description = fields.Text('Descripción')
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Ya existe un nivel de enseñanza con ese nombre!'),
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(TeachingLevel, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(TeachingLevel, self).fields_view_get(view_id=view_id,
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

        res = super(TeachingLevel, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):
        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.teaching_level')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de nivel de enseñanza satisfactoria.'
        })

        return super(TeachingLevel, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.teaching_level')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de nivel de enseñanza satisfactoria.'
        })
        return super(TeachingLevel, self).write(vals)

    def unlink(self):
        count = 0
        for rec in self:
            profesional_request = self.env['professional_registers.professional_request'].search(
                [('teaching_level', '=', int(rec.id))])
            profile = self.env['professional_registers.profile'].search([('teaching_level', '=', int(rec.id))])
            study_centers = self.env['nomenclators.study_centers'].search([('teaching_level_id', '=', int(rec.id))])

            if profesional_request or profile or study_centers:
                count = count + 1
        if count != 0:
            msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
            if count > 1:
                msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'

            raise exceptions.ValidationError(msg)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.teaching_level')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de nivel de enseñanza satisfactoria.'
        if count > 1:
            msg = 'Eliminación de nivel de enseñanza satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(TeachingLevel, self).unlink()
