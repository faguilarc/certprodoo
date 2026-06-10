# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json

from lxml import etree


class RequestProfileDocumentRequired(models.Model):
    _name = 'professional_registers.pr_document'
    _description = 'Documentos requeridos por solicitudes'

    profile = fields.Many2one('professional_registers.profile', string="Perfil")
    request_wizard = fields.Many2one('professional_registers.request_wizard', string="Solicitud")
    documents = fields.Many2one('nomenclators.documents_required', string="Documentos")
    request = fields.Many2one('professional_registers.professional_request', string="Solicitudes")
    checked = fields.Boolean('Revisado')
    commet = fields.Text('Comentarios')
    attachment_ids = fields.Many2many('ir.attachment', string="Subir")
    update_request = fields.Many2one(
        'professional_registers.professional_request_update',
        string="Solicitud de Actualización"
    )
    is_document_required = fields.Boolean("Requerido", related='documents.is_document_required',)
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
