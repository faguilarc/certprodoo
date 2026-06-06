# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class UserInherit(models.Model):
    _inherit = "res.users"

    full_name = fields.Char('Nombre y apellidos')
    first_last_name = fields.Char("Primer Apellido")
    second_last_name = fields.Char("Segundo Apellido")
    identification = fields.Char("CI o Pasaporte")
    nationality_id = fields.Many2one('nomenclators.nationality', string="Nacionalidad")