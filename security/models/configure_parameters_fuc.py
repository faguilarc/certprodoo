# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime
import os
import base64
import requests

class ParametersConectionFUC(models.Model):
    _name = "security.configure_keys"

    key_1 = fields.Char('Clave del consumidor')
    key_2 = fields.Char('Secreto del consumidor')
    url = fields.Char('URL TOKEN')
    url_base = fields.Char('URL BASE')

    name = fields.Char('Registro')

    def generate_token(self, key_1, key_2, url_token):
        # url_token = 'https://apis-fuc.xutil.cu/token'

        grant = '?grant_type=client_credentials'
        scope = '&scope=nivel10'
        url_token = f"{url_token}{grant}{scope}"

        message = str(key_1) + ':' + str(key_2)

        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        variableencode = base64_bytes.decode('ascii')
        headers = {'Authorization': f"Basic {variableencode}"}
        try:
            response = requests.post(url=url_token, headers=headers)
            variable = response.json()
            variable = variable.get('access_token')
            return variable
        except Exception:
            raise exceptions.AccessError("No hay conexión a la ficha del ciudadano. Inténtelo más tarde")

    @api.model
    def create(self, vals_list):
        vals_list['name'] = 'Registro de configuración ' + str(datetime.utcnow().date())
        key_1 = vals_list.get('key_1')
        key_2 = vals_list.get('key_2')
        url_token = vals_list.get('url')
        os.environ['TOKEN_FICHA_UNICA'] = str(self.generate_token(key_1, key_2, url_token))
        return super(ParametersConectionFUC, self).create(vals_list)