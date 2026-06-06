# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree


class ProcedureType(models.Model):
    _name = 'nomenclators.procedure_types'
    _description = 'Tipos de trámite'
    _rec_name = 'name'

    name = fields.Char('Nombre')
    comodel_name = fields.Char('Identificador')
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'Ya existe un trámite con ese nombre!'),
        ('procedure_comodel_uniq', 'unique(procedure_comodel, company_id)',
         'Ya existe un trámite con ese identificador!')
    ]

    active = fields.Boolean('Activo', default=True)
    suspension_history_ids = fields.One2many(
        'procedure.suspension.history',
        'procedure_type_id',
        string='Histórico de Suspensiones'
    )
    current_suspension_id = fields.Many2one(
        'procedure.suspension.history',
        string='Suspensión Actual',
        compute='_compute_current_suspension'
    )

    def _compute_current_suspension(self):
        for record in self:
            record.current_suspension_id = self.env['procedure.suspension.history'].search([
                ('procedure_type_id', '=', record.id),
                ('resume_date', '=', False)
            ], limit=1)

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(ProcedureType, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProcedureType, self).fields_view_get(view_id=view_id,
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

        res = super(ProcedureType, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):

        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.procedure_types')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de trámite satisfactoria.'
        })

        return super(ProcedureType, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.procedure_types')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de trámite satisfactoria.'
        })
        return super(ProcedureType, self).write(vals)

    def unlink(self):
        count = 0
        for rec in self:
            profesional_request = self.env['professional_registers.professional_request'].search(
                [('procedure_type', '=', int(rec.id))])
            documents = self.env['nomenclators.documents_required'].search([('procedure1', '=', int(rec.id))])

            if documents or profesional_request:
                count = count + 1
        if count != 0:
            msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
            if count > 1:
                msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'

            raise exceptions.ValidationError(msg)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.procedure_types')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de trámite satisfactoria.'
        if count > 1:
            msg = 'Eliminación de trámites satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(ProcedureType, self).unlink()

    def _check_suspended_procedures(self):
        suspended_procedures = self.env['procedure.suspension.history'].search([
            ('resume_date', '=', False),
            ('state', '=', 'stopped')
        ])
        return suspended_procedures
