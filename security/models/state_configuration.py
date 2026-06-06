# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import datetime
from lxml import etree
import json


class StateConfigurtion(models.Model):
    _name = "security.state_configuration"
    _description = "Configuración de Estados"

    name = fields.Char(string="Nombre")
    priority = fields.Integer(string="Prioridad")
    description = fields.Text()
    model = fields.Many2one(
        "ir.model",
        string="Modelo",
    )
    fold = fields.Boolean("Cambio de estado")

    @api.model
    def create(self, vals_list):
        priority = vals_list.get('priority')
        model_id = vals_list.get('model')
        register = self.env['security.state_configuration'].search([('model', '=', int(model_id)), ('priority', '=', int(priority))])
        if register:
            raise exceptions.ValidationError('Ya existe un estado con esa prioridad para el modelo seleccionado.')

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.state_configuration')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Creación de estados satisfactoria'
        })

        return super(StateConfigurtion, self).create(vals_list)

    def write(self, vals):
        if vals.get('priority'):
            priority = vals.get('priority')
            model_id = vals.get('model') if vals.get('model') else self.model.id
            register = self.env['security.state_configuration'].search(
                [('model', '=', int(model_id)), ('priority', '=', int(priority))])
            if register:
                raise exceptions.ValidationError('Ya existe un estado con esa prioridad para el modelo seleccionado.')

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.state_configuration')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Edición de estados satisfactoria'
        })

        return super(StateConfigurtion, self).write(vals)

    def unlink(self):
        cantidad_registros = 0
        for rec in self:
            cantidad_registros = cantidad_registros + 1

        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.state_configuration')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de estado satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de estados satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': msg
        })
        return super(StateConfigurtion, self).unlink()