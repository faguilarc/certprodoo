import os
import requests
import base64
import json
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError
from datetime import datetime

class FUCConfig(models.Model):
    _name = 'fuc.config'
    _description = 'Configuración de FUC'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # ← HERENCIA AÑADIDA
    _rec_name = 'key_1'

    key_1 = fields.Char('Key 1', required=True, tracking=True)
    key_2 = fields.Char('Key 2', required=True, tracking=True)
    url_token = fields.Char('URL Token', required=True, default='https://apis-fuc.minjus.gob.cu/token', tracking=True)
    url_base = fields.Char('URL Base', required=True,
                           default='https://apis-fuc.minjus.gob.cu/pn-api-consulta/2.0.210131/api/v1/nivel10?', tracking=True)
    token = fields.Text('Token Actual', readonly=True)
    token_expiry = fields.Datetime('Fecha de Expiración del Token', readonly=True)
    last_test = fields.Datetime('Última Prueba', readonly=True)
    last_test_result = fields.Text('Resultado de la Última Prueba', readonly=True)
    use_simulation = fields.Boolean('Usar Simulación', default=False,
                                    help='Usa un servidor local de simulación en lugar del API real', tracking=True)

    @api.model
    def get_default_config(self):
        config = self.search([], limit=1, order='id desc')
        if config:
            return config
        else:
            return self.create({})

    def generate_token(self):
        self.ensure_one()

        message = f"{self.key_1}:{self.key_2}"
        url_token = f"{self.url_token}?grant_type=client_credentials&scope=nivel10"
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        variableencode = base64_bytes.decode('ascii')
        headers = {'Authorization': f"Basic {variableencode}"}

        try:
            response = requests.post(url=url_token, headers=headers)
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                if token:
                    self.write({
                        'token': token,
                        'token_expiry': datetime.now(),
                    })
                    # Actualizar la variable de entorno
                    os.environ['TOKEN_FICHA_UNICA'] = token
                    return {'status': 'success', 'message': 'Token generado correctamente.'}
                else:
                    return {'status': 'error', 'message': 'No se pudo obtener el token de la respuesta.'}
            else:
                return {'status': 'error',
                        'message': f'Error en la solicitud: {response.status_code} - {response.text}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Excepción: {str(e)}'}

    def test_connection(self, identity_number):
        # Generar token si no existe o está expirado
        if not self.token or not self.token_expiry:
            result = self.generate_token()
            if result['status'] != 'success':
                return result

        # Determinar la URL a usar
        if self.use_simulation:
            url = f"http://127.0.0.1:5000/api/v1/nivel10?identidad_numero={identity_number}"
        else:
            url = f"{self.url_base}identidad_numero={identity_number}"

        headers = {'Authorization': f"Bearer {self.token}", 'Accept': 'application/json'}

        try:
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                data = response.json()

                # Si todo está bien, guardar el resultado de la prueba
                self.write({
                    'last_test': datetime.now(),
                    'last_test_result': f"Consulta exitosa para CI: {identity_number}"
                })
                return {'status': 'success', 'data': data}
            else:
                self.write({
                    'last_test': datetime.now(),
                    'last_test_result': f"Error en la consulta: {response.status_code} - {response.text}"
                })
                return {'status': 'error', 'message': f'Error en la consulta: {response.status_code} - {response.text}'}
        except Exception as e:
            self.write({
                'last_test': datetime.now(),
                'last_test_result': f"Excepción: {str(e)}"
            })
            return {'status': 'error', 'message': f'Excepción: {str(e)}'}

    def action_generate_token(self):
        result = self.generate_token()
        if result['status'] == 'success':
            self.message_post(body=result['message'])  # ← Ahora funciona
        else:
            raise UserError(result['message'])

    def action_test_connection(self):
        # Pedir el número de identidad mediante un wizard
        return {
            'name': 'Probar Conexión',
            'type': 'ir.actions.act_window',
            'res_model': 'fuc.test.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def get_token(self):
        try:
            return os.environ.get('TOKEN_FICHA_UNICA')
        except Exception:
            raise exceptions.ValidationError(
                'Configure el token de la ficha única en las variables de entorno del sistema.')

    def update_token(self, token):
        os.environ['TOKEN_FICHA_UNICA'] = str(token)