# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json
from unidecode import unidecode

from lxml import etree
import passlib.context

from odoo.tools import profile

class OthersProfesions(models.Model):
    _name = 'professional_registers.others_professions'
    _description = 'Otras profesiones'

    profile = fields.Many2one('professional_registers.profile', string="Perfil")
    profesional_request = fields.Many2one('professional_registers.professional_request', string="Solicitud")

    professions_id = fields.Many2one('nomenclators.professions', "Profesión")
    specialtie_id = fields.Many2one('nomenclators.specialties', "Especialidad")
    number = fields.Integer('Número')
    volume = fields.Char('Tomo')
    folio = fields.Char('Folio')
    study_center = fields.Many2one('nomenclators.study_centers', string="Centro de estudio")
    degree_date = fields.Date('Fecha de graduación')

    @api.onchange('professions_id')
    def onchange_professions(self):
        if self.professions_id:
            specialties = self.env['nomenclators.specialties'].search([('profession_id', '=', int(self.professions_id.id))])
            return dict(
                value=dict(
                    specialtie_id=None,  # Para que lo limpie
                ),
                domain=dict(
                    specialtie_id=[('id', 'in', specialties.ids)],
                )
            )
