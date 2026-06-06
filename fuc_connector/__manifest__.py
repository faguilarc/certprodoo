{
    'name': 'FUC Connector',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Conector para la Ficha Única de Ciudadano (FUC)',
    'description': """
        Módulo para gestionar la conexión a la API de la Ficha Única de Ciudadano (FUC).
        Permite configurar las claves y URLs, probar la conexión y realizar consultas.
    """,
    'author': 'Tu Nombre',
    'website': 'https://tu-sitio-web.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/fuc_config_views.xml',
        'views/fuc_test_views.xml',
        'wizards/fuc_test_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
}