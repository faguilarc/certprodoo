# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree


class Normative(models.Model):
    _name = 'nomenclators.normative'
    _description = 'Normativas'
    _rec_name = 'name'

    name = fields.Text('nombre')
    user_id = fields.Many2one('res.users', string="Usuario")
    company_id = fields.Many2one('res.company', string="Compañía")

    attachment_ids = fields.Many2many('ir.attachment', string="Subir")

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Normative, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Normative, self).fields_view_get(view_id=view_id,
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
    def create(self, vals_list):
        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.normative')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de normativas satisfactoria.'
        })

        return super(Normative, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.normative')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de normativas satisfactoria.'
        })

        return super(Normative, self).write(vals)

    def unlink(self):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.normative')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de normativas satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(Normative, self).unlink()