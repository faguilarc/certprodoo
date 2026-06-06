# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, date

class Traces(models.Model):
    _name = 'security.traces'
    _description = 'Trazas'

    register_time = fields.Datetime('Fecha de registro', default=datetime.now())
    user = fields.Char("Usuario", required=False)
    description = fields.Text(string='Observaciones')
    model = fields.Many2one('ir.model', string="Modelo")