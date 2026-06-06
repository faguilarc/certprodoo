# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree


class SideNotes(models.Model):
    _name = 'professional_registers.side_notes'
    _description = 'Notas al margen'

    inscription = fields.Many2one('professional_registers.inscription', string="Inscripción")

    date = fields.Date('Fecha')
    side_notes = fields.Text('Notas al margen')

    attachment_ids = fields.Many2many('ir.attachment', string="Documentos")
