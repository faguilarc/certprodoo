# __manifest__.py
{
    'name': 'Professional Registers Location',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Módulo de localización para profesionales',
    'description': """
        Este módulo añade funcionalidades de geolocalización para profesionales,
        permitiendo buscar y asignar profesionales según su ubicación geográfica.
    """,
    'author': 'Tu Nombre',
    'website': 'https://tu-sitio-web.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'professional_registers'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/profile_views.xml',
        'templates/geo_point_widget_templates.xml',
        'wizards/set_location_map_wizard_views.xml',
        'wizards/find_professionals_by_location_views.xml'
    ],
    'qweb': [
        'static/src/xml/geo_point_widget_templates.xml',
    ],
    'installable': True,
    'application': False,
}
