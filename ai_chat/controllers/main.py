# ai_chat/controllers/main.py

import json
import requests
from odoo import http
from odoo.http import request, content_disposition


class AiChatController(http.Controller):

    @http.route('/ai_chat/get_providers', type='json', auth='user', methods=['POST'])
    def get_providers(self):
        """Obtiene lista de proveedores activos"""
        providers = request.env['ai.provider'].sudo().search([
            ('active', '=', True)
        ], order='sequence ASC')

        return [{
            'id': p.id,
            'name': p.name,
            'model': p.model,
            'provider_type': p.provider_type,
        } for p in providers]

    @http.route('/ai_chat/update_chat_provider', type='json', auth='user', methods=['POST'])
    def update_chat_provider(self, chat_id, provider_id):
        """Actualiza el proveedor de un chat existente"""
        try:
            chat = request.env['ai.chat'].browse(chat_id)
            if not chat.exists():
                return {'error': 'Chat no encontrado'}

            chat.write({'provider_id': provider_id})
            return {'success': True, 'provider_id': provider_id}
        except Exception as e:
            return {'error': str(e)}

    
    @http.route('/ai_chat/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, chat_id, message_content):
        """
        Recibe un mensaje del usuario, lo envía a la IA y devuelve la respuesta.
        """
        chat = request.env['ai.chat'].browse(chat_id)
        if not chat.exists():
            return {'error': 'Chat session not found.'}

        # 1. Crear el mensaje del usuario en la BD
        request.env['ai.chat.message'].create({
            'chat_id': chat_id,
            'role': 'user',
            'content': message_content,
        })

        # 2. Obtener el proveedor del chat
        provider = chat.provider_id
        if not provider:
            return {'error': 'No hay proveedor configurado para este chat.'}

        if provider.provider_type == 'ollama':
            try:
                # Obtener historial de conversación
                conversation_history = [
                    {'role': msg.role, 'content': msg.content}
                    for msg in chat.message_ids
                ]

                payload = {
                    "model": provider.model,
                    "messages": conversation_history,
                    "stream": False,
                }

                api_url = f"{provider.api_base.rstrip('/')}/api/chat"

                response = requests.post(api_url, json=payload, timeout=120)
                response.raise_for_status()

                response_data = response.json()
                ai_response_content = response_data.get('message', {}).get('content', '')

                # 3. Guardar la respuesta de la IA en la BD
                if ai_response_content:
                    request.env['ai.chat.message'].create({
                        'chat_id': chat_id,
                        'role': 'assistant',
                        'content': ai_response_content,
                    })
                    return {
                        'status': 'success',
                        'response': ai_response_content,
                        'provider_name': provider.name,
                        'model': provider.model,
                    }
                else:
                    return {'error': 'Respuesta vacía de la IA.'}

            except requests.exceptions.RequestException as e:
                return {'error': f'Error de conexión API: {str(e)}'}
            except Exception as e:
                return {'error': f'Error inesperado: {str(e)}'}

        else:
            return {'error': f'Proveedor {provider.provider_type} no soportado aún.'}