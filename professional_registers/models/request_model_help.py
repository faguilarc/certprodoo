# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date

import json

from lxml import etree

class RequestModelReport(models.Model):
    _name = 'professional_registers.request_help'
    _description = 'Modelo para reporte de detalles de solicitud'

    full_name = fields.Char('Nombre y apellidos')
    request_number = fields.Char('Nro. Solicitud')
    date = fields.Date('Fecha de solicitud')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    identity = fields.Char('CI o pasaporte')
    request_id = fields.Many2one('professional_registers.professional_request', string="Solicitud")
    email = fields.Char('Correo')
    speciality = fields.Many2one('nomenclators.specialties', string="Especialidad")
    state = fields.Char('Estado actual')
    counter = fields.Integer("Días hábiles", default=0)
    # nationality = fields.Selection([('national', 'Nacional'),
    #                                 ('foreign', 'Extranjero')], string="Nacionalidad")

    nationality_id = fields.Many2one('nomenclators.nationality', related='request_id.nationality_id',string="Nacionalidad")
    # Relación One2many con el modelo ProfessionalRequestHistory
    history_ids = fields.One2many(
        'professional_registers.professional_request_history',
        'request_help_id',
        string='Histórico de Cambios de Estado'
    )

    @api.model
    def default_get(self, fields_list):
        id_request = self._context.get('id_request')
        if id_request:
            request = self.env['professional_registers.request_help'].search([('id', '=', int(id_request))])
            history_ids = self.env['professional_registers.professional_request_history'].search([('request_id', '=', int(self._context.get('req_id')))])
            return {
                'id': request.id,
                'request_number': request.request_number,
                'full_name': request.full_name,
                'nationality_id': request.nationality_id.id,
                'identity': request.identity,
                'email': request.email,
                'profession': request.profession.id,
                'speciality': request.speciality.id,
                'date': request.date,
                'state': request.state,
                'history_ids': history_ids,

            }
        else:
            return super(RequestModelReport, self).default_get(fields_list)

    def report_request(self):
        id_request = self._context.get('id_request')
        request = self.env['professional_registers.professional_request'].search([('id', '=', int(id_request))])

        email = request.email if request.email else ''
        nationality = request.nationality_id.name

        degree_sciences = ''
        if request.degree_sciences == 'esp':
            degree_sciences = 'Especialista'
        elif request.degree_sciences == 'msc':
            degree_sciences = 'Master'
        elif request.degree_sciences == 'dr':
            degree_sciences = 'Doctor'

        history_work = []
        for hw in request.history_work:
            history_work.append({
                'work_center': hw.work_center,
                'organism': hw.organism.name if  hw.organism else '',
                'activity': hw.activity,
                'phone': hw.phone,
                'date_from': hw.date_from,
                'date_to': hw.date_to,
            })

        data = {
            'request_number': request.request_number,
            'identity': request.identity,
            'nationality': nationality,
            'email': email,
            'profession': request.profession.name,
            'speciality': request.specialties.name,
            'state': request.states,
            'tramit_type': 'Solicitud',
            'date': request.date,
            'name': request.name,
            'first_last_name': request.first_last_name,
            'second_last_name': request.second_last_name,
            'sex': 'Masculino' if request.sex == 'male' else 'Femenino',
            'address1': request.address,
            'country': request.country.name,
            'country_state': request.country_states.name,
            'city': request.city.name,
            'phone': request.phone,
            'teaching_level': request.teaching_level.name,
            'study_center': request.study_center.name,
            'degree_date': request.degree_date,
            'tomo': request.volume,
            'folio': request.folio,
            'convalidation_degree_tittle': request.convalidation_degree_tittle,
            'teaching_category': request.teaching_category.name,
            'teaching_category_date': request.teaching_category_date,
            'investigations': 'Si' if request.investigations else 'No',
            'investigations_year': request.investigations_year,
            'degree_sciences': degree_sciences,
            'degree_sciences_year': request.degree_sciences_year,
            'unaicc_date': request.unaicc_date,
            'user': request.user,
            'retired': 'Si' if request.retired else 'No',
            'retired_date': request.date,
            'password': request.password,
            'history_work': history_work,
        }
        return self.env.ref('professional_registers.professional_request_detail').report_action(self, data)