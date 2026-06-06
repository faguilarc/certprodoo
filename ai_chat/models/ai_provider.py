# ai_chat/models/ai_provider.py

from odoo import models, fields, api


class AiProvider(models.Model):
    _name = 'ai.provider'
    _description = 'AI Provider Configuration'
    _order = 'sequence, name'

    name = fields.Char('Provider Name', required=True, help="e.g., 'Mi Ollama en VPS'")
    provider_type = fields.Selection([
        ('ollama', 'Ollama'),
        # ('openai', 'OpenAI'), # Futuros proveedores
    ], string='Provider Type', required=True, default='ollama')

    api_base = fields.Char('API Base URL', required=True,
                           help="URL base del proveedor. Para Ollama: http://direccion:puerto")
    model = fields.Char('Model Name', required=True, help="Nombre del modelo a usar. e.g., 'llama3', 'mistral'")

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)

    # Campos específicos para proveedores que los necesiten (como OpenAI)
    api_key = fields.Char('API Key', help='Clave de API para proveedores que la requieran.')

    @api.model
    def get_default_provider(self):
        """Obtiene el proveedor activo por defecto."""
        return self.search([('active', '=', True)], order='sequence ASC', limit=1)