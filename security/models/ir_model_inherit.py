# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class IrModelInherit(models.Model):
    _inherit = "ir.model"