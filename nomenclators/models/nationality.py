# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree


class Nationality(models.Model):
    _name = 'nomenclators.nationality'
    _description = 'Nacionalidad'
    _rec_name = 'name'

    name = fields.Char('Nombre')
    validate_fuc = fields.Boolean('Validar FUC', default=False)
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Ya existe una nacionalidad con ese nombre!'),
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Nationality, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Nationality, self).fields_view_get(view_id=view_id,
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

        res = super(Nationality, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):
        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.nationality')])

        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de nacionalidad satisfactoria.'
        })

        return super(Nationality, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.nationality')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de nacionalidad satisfactoria.'
        })
        return super(Nationality, self).write(vals)

    def unlink(self):
        count = 0
        for rec in self:
            profesional_request = self.env['professional_registers.professional_request'].search(
                [('profession', '=', int(rec.id))])
            profile = self.env['professional_registers.profile'].search([('profession', '=', int(rec.id))])
            inscription = self.env['professional_registers.inscription'].search([('profession', '=', int(rec.id))])

            if profesional_request or profile or inscription:
                count = count + 1
        if count != 0:
            msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
            if count > 1:
                msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'

            raise exceptions.ValidationError(msg)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.nationality')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de nacionalidad satisfactoria.'
        if count > 1:
            msg = 'Eliminación de nacionalidades satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(Nationality, self).unlink()
