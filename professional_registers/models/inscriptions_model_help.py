# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date

import json

from lxml import etree

class InscriptionsModelReport(models.Model):
    _name = 'professional_registers.inscriptions_help'
    _description = 'Modelo para reporte de detalles de inscripción'

    full_name = fields.Char('Nombre y apellidos')
    inscription_number = fields.Char('Nro. Inscripción')
    date = fields.Date('Fecha de inscripción')
    profession = fields.Many2one('nomenclators.professions', string="Profesión")
    identity = fields.Char('CI o pasaporte')
    inscription_id = fields.Many2one('professional_registers.inscription', string="Inscripción")
    email = fields.Char('Correo')
    state = fields.Char('Estado')
    # nationality = fields.Selection([('national', 'Nacional'),
    #                                 ('foreign', 'Extranjero')], string="Nacionalidad")

    nationality_id = fields.Many2one('nomenclators.nationality', related='inscription_id.nationality_id',string="Nacionalidad")


    history_ids = fields.One2many(
        'professional_registers.inscription_history',
        'inscription_help_id',
        string='Histórico de Cambios de Estado'
    )


    @api.model
    def default_get(self, fields_list):
        id_inscription = self._context.get('id_inscription')
        if id_inscription:
            inscription = self.env['professional_registers.inscriptions_help'].search([('id', '=', int(id_inscription))])
            history_ids = self.env['professional_registers.inscription_history'].search([('inscription_id', '=', int(self._context.get('ins_id')))])

            return {
                'id': inscription.id,
                'inscription_number': inscription.inscription_number,
                'full_name': inscription.full_name,
                'nationality_id': inscription.nationality_id.id if inscription.nationality_id else '',
                'identity': inscription.identity,
                'email': inscription.email,
                'profession': inscription.profession.id,
                'date': inscription.date,
                'state': inscription.state,
                'history_ids': history_ids,

            }
        else:
            return super(InscriptionsModelReport, self).default_get(fields_list)

    def report_inscription(self):
        email = self.email if self.email else ''
        nationality = self.nationality_id.name if self.nationality_id else ''
        logo = self.env['nomenclators.logo'].search([('name', '=', 'Escudo')])
        id_inscription = self._context.get('id_inscription')
        inscription = False
        if id_inscription:
            inscription = self.env['professional_registers.inscription'].search([('id', '=', int(id_inscription))])
        data = {
            'request_number': self.inscription_number,
            'identity': self.identity,
            'nationality': nationality,
            'email': email,
            'profession': self.profession.id,
            'profession_name': self.profession.name,
            'state': self.state,
            'tramit_type': 'Solicitud',
            'date': self.date,
            'days': self.date.day,
            'month': self.date.month,
            'year': self.date.year,
            'full_name': self.full_name,
            'company': logo[0],
            'id_transaction': inscription.id_transaction if inscription else ''
        }
        return self.env.ref('professional_registers.inscriptions_detail').report_action(self, data)