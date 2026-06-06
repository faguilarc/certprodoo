# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json
from dateutil.relativedelta import relativedelta

from lxml import etree

class IdentityModelReport(models.Model):
    _name = 'professional_registers.identity'
    _description = 'Modelo para reporte de identificación'

    full_name = fields.Char('Nombre y apellidos')
    inscription_number = fields.Char('Nro. Inscripción')
    date = fields.Date('Válido hasta')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    inscription_id = fields.Many2one('professional_registers.inscription', string="Inscripción")
    image = fields.Image("Foto", max_width=1920, max_height=1920)
    image1 = fields.Binary("Foto")

    @api.model
    def default_get(self, fields_list):
        id_identity = self._context.get('id_identity')
        if id_identity:
            identity = self.env['professional_registers.identity'].search([('id', '=', int(id_identity))])
            return {
                # 'res_id': identity.id,
                'inscription_number': identity.inscription_number,
                'full_name': identity.full_name,
                'date': identity.date,
                'profession': identity.profession.id,
                'inscription_id': identity.inscription_id.id,
                'image': identity.image,
            }
        else:
            return super(IdentityModelReport, self).default_get(fields_list)

    def report_identity(self):
        data = {
            'inscription_number': self.inscription_number,
            'full_name': self.full_name,
            'profession': self.profession.name,
            'date': self.date,
        }
        return self.env.ref('professional_registers.identity_detail').report_action(self, data)