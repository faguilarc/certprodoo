{
    'name': 'AI Chat for Odoo',
    'version': '14.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Integra un chat con IA (tipo ChatGPT) en Odoo, soportando múltiples proveedores como Ollama.',
    'description': """
AI Chat Module for Odoo
=======================

Este módulo añade una interfaz de chat a Odoo que se comunica con
distintos modelos de lenguaje a través de varios proveedores.

Características:
* Interfaz de chat moderna y responsiva.
* Configuración de múltiples proveedores de IA.
* Soporte inicial para Ollama.
* Diseño modular para añadir fácilmente nuevos proveedores (OpenAI, Claude, etc.).
    """,
    'author': 'Frank Aguilar',
    # 'website': 'https://tu-web.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        "views/assets.xml",
        'views/ai_provider_views.xml',
        'views/ai_chat_views.xml',
    ],

    "qweb": [
        'static/src/xml/ai_chat_templates.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'images': ['static/description/icon2.png'],
}
