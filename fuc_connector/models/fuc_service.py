import os
import requests
import base64
import json
import time
from odoo import models, fields, api, exceptions
from datetime import datetime


class FUCService(models.Model):
    _name = 'fuc.service'
    _description = 'Servicio de Consulta a FUC'
    _auto = False  # No es un modelo persistente

    @api.model
    def get_config(self):
        return self.env['fuc.config'].get_default_config()

    @api.model
    def generate_token(self):
        config = self.get_config()
        return config.generate_token()

    @api.model
    def get_token(self):
        config = self.get_config()
        return config.get_token()

    @api.model
    def update_token(self, token):
        config = self.get_config()
        return config.update_token(token)

    @api.model
    def get_url_base(self):
        config = self.get_config()
        return config.url_base

    @api.model
    def get_token_url(self):
        config = self.get_config()
        return config.url_token

    @api.model
    def get_keys(self):
        config = self.get_config()
        return f"{config.key_1}:{config.key_2}"

    @api.model
    def validate_fuc(self, json_data):
        required_keys = ['id','identidad_numero', 'primer_nombre', 'primer_apellido', 'sexo', 'edad', 'direccion',
                         'municipio_residencia_cod_dpa', 'provincia_residencia_cod_dpa', ]

        # Si json_data es una lista, tomar el primer elemento
        if isinstance(json_data, list) and json_data:
            data = json_data[0]
        else:
            data = json_data

        for key in required_keys:
            if key not in data or data[key] is None or data[key] == '':
                return False
        return True

    @api.model
    def search_data(self, identity_number, use_simulation=False):
        config = self.get_config()

        # Forzar el modo de simulación si se especifica
        original_use_simulation = config.use_simulation
        if use_simulation:
            config.write({'use_simulation': True})

        try:
            # Generar token si no existe o está expirado
            if not config.token or not config.token_expiry:
                result = config.generate_token()
                if result['status'] != 'success':
                    return {'status': 'error', 'message': result['message']}

            # Determinar la URL a usar
            if config.use_simulation:
                url = f"http://127.0.0.1:5000/api/v1/nivel10?identidad_numero={identity_number}"
            else:
                url = f"{config.url_base}identidad_numero={identity_number}"

            token = config.get_token()
            headers = {'Authorization': f"Bearer {token}", 'Accept': 'application/json'}

            reintentos = 0
            response_ok = False
            data = []

            while reintentos < 3 and not response_ok:
                response = requests.get(url=url, headers=headers)
                if response.status_code == 200 :
                    data = response.json()
                    response_ok = True
                else:
                    reintentos += 1
                    time.sleep(3)

            if response_ok:
                return {'status': 'success', 'data': data}
            else:
                return {'status': 'error', 'message': 'No se pudieron obtener los datos después de 3 intentos.'}
        except Exception as e:
            return {'status': 'error', 'message': f'Excepción: {str(e)}'}
        finally:
            # Restaurar el modo de simulación original
            if use_simulation:
                config.write({'use_simulation': original_use_simulation})

    @api.model
    def search_simulated_data(self, identity_number):
        return self.search_data(identity_number, use_simulation=True)