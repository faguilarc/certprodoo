from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date

import json

from lxml import etree


class RequestUpdateModelReport(models.Model):
    _name = 'professional_registers.professional_request_update_help'
    _description = 'Modelo para reporte de detalles de actualizacion'

    full_name = fields.Char('Nombre y apellidos')
    request_number = fields.Char('Nro. Solicitud')
    date = fields.Date('Fecha de solicitud')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    identity = fields.Char('CI o pasaporte')
    request_id = fields.Many2one(
        'professional_registers.professional_request_update',
        string='Actualización',
        required=True,
        ondelete='cascade'
    )
    email = fields.Char('Correo')
    speciality = fields.Many2one('nomenclators.specialties', string="Especialidad")
    state = fields.Char('Estado actual')
    counter = fields.Integer("Días hábiles", default=0)
    # nationality = fields.Selection([('national', 'Nacional'),
    #                                 ('foreign', 'Extranjero')], string="Nacionalidad")

    nationality_id = fields.Many2one('nomenclators.nationality', related='request_id.nationality_id',
                                     string="Nacionalidad")
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
            history_ids = self.env['professional_registers.professional_request_history'].search(
                [('request_id', '=', int(self._context.get('req_id')))])
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
            return super(RequestUpdateModelReport, self).default_get(fields_list)
