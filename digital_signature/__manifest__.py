# -*- coding: utf-8 -*-
{
    'name': 'Solicitud de Firma Digital',
    'version': '14.0.1.0.0',
    'category': 'Servicios',
    'summary': 'Gestión de solicitudes de firma digital para inscripciones',
    'author': 'Frank Aguilar Caraballo',
    'depends': ['base', 'website', 'professional_registers', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/digital_signature_security.xml',
        'data/digital_signature_data.xml',
        'views/digital_signature_config_views.xml',
        'views/digital_signature_request_views.xml',
        'views/digital_signature_wizard_views.xml',
        'views/inscription_extended_views.xml',
        'templates/digital_signature_templates.xml',
        'templates/website_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'digital_signature/static/src/css/digital_signature.css',
        ],
        'web.assets_frontend': [
            'digital_signature/static/src/css/digital_signature.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/ds_icon.png'],
}
