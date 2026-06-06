# -*- coding: utf-8 -*-
{
    'name': "Dashboard",

    'summary': """
        Cuadro de Mando""",

    'description': """
        Cuadro de Mando para la toma de desiciones de la empresa
    """,

    'author': "Adrian Hernandez",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Dashboard',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web', 'professional_registers'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/ir_crong_data.xml',

        'views/dashboard.xml',
        'views/assets.xml',
        'views/dashboard_kanban_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
        'static/src/xml/dashboard_client.xml',
        'static/src/xml/template_customs.xml',
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
