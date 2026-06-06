# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class PermitsRole(models.Model):
    _name = "security.clear_registers"
    _description = "Borrar datos de BD"

    erase_type = fields.Selection([('only_pr', 'Solo Registros Profesionales'),
                                   ('all', 'Todo')], default='only_pr',string="Tipo de borrado")


    def eraser(self):
        if self.erase_type == 'only_pr':
            self.erase_professional_registers()
        else:
            self.erase_all()

    def erase_professional_registers(self):
        profesional_registers = self.env['professional_registers.professional_request'].search([])
        request_model_help = self.env['professional_registers.request_help'].search([])
        for rmh in request_model_help:
            rmh.unlink()

        inscriptions_model_help = self.env['professional_registers.inscriptions_help'].search([])
        for imh in inscriptions_model_help:
            imh.unlink()

        for pr in profesional_registers:
            pr.write({
                'force_erase': True
            })

            #Borrar work_history
            work_history = self.env['professional_registers.work_history'].search([('profesional_request', '=', int(pr.id))])
            for wh in work_history:
                wh.unlink()

            #Borrar request_profile_documents
            request_profile_documents = self.env['professional_registers.pr_document'].search([('request', '=', int(pr.id))])
            for rpd in request_profile_documents:
                rpd.unlink()

            #Borrar request_model_help
            request_model_help = self.env['professional_registers.request_help'].search([('request_id', '=', int(pr.id))])
            for rmh in request_model_help:
                rmh.unlink()

            #Borrar inscriptions
            inscriptions = self.env['professional_registers.inscription'].search([('request_id', '=', int(pr.id))])
            for insc in inscriptions:
                insc.write({
                    'force_erase': True
                })

                #Borrar inscriptions_model_help
                inscriptions_model_help = self.env['professional_registers.inscriptions_help'].search([('inscription_id', '=', int(insc.id))])
                for imh in inscriptions_model_help:
                    imh.unlink()

                #Borrar identity_model_help
                identity_model_help = self.env['professional_registers.identity'].search([('inscription_id', '=', int(insc.id))])
                for imh in identity_model_help:
                    imh.unlink()

                #Borrar Side Notes
                side_notes = self.env['professional_registers.side_notes'].search([('inscription', '=', int(insc.id))])
                for sn in side_notes:
                    sn.unlink()

                insc.unlink()

            #Borrar Profile
            profile = self.env['professional_registers.profile'].search([('user', '=', str(pr.user))])
            for p in profile:
                p.unlink()
            #Borrar Profesional Request
            pr.unlink()

        #Traces
        self.erase_traces()
    def erase_traces(self):
        arra_models = ['professional_registers.professional_request',
                       'professional_registers.work_history',
                       'professional_registers.pr_document',
                       'professional_registers.request_help',
                       'professional_registers.inscription',
                       'professional_registers.profile',
                       'professional_registers.inscriptions_help',
                       'professional_registers.identity',
                       'professional_registers.side_notes']
        model = self.env['ir.model'].search([('model', 'in', arra_models)])
        for m in model:
            traces = self.env['security.traces'].search([('model', '=', int(m.id))])
            for t in traces:
                t.unlink()

    def erase_all(self):
        self.erase_professional_registers()