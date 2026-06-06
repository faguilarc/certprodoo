# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

class ProfessionalRequest(models.Model):
    _inherit = 'security.permits_state'

    #Request
    in_process = fields.Boolean('En proceso', default=False)
    validation = fields.Boolean('En validación', default=False)
    stop = fields.Boolean('Detener', default=False)
    approved = fields.Boolean('Aprobar', default=False)
    init_process = fields.Boolean('Iniciar proceso', default=False)
    cancel = fields.Boolean('Cancelar', default=False)
    reset = fields.Boolean('Deshacer cancelación', default=False)
    send_email = fields.Boolean("Generar Correo", default=False)
    denied = fields.Boolean("Denegar", default=False)

    #Inscription
    cancel_inscription = fields.Boolean('Cancelar', default=False)
    reset_inscription = fields.Boolean('Deshacer cancelación', default=False)

