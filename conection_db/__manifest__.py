# -*- coding: utf-8 -*-
{
    'name': "Conection DB",

    'summary': """
        Conexión a Base de datos""",

    'description': """
        Conexión a Base de datos postgresql para la extracción de datos
    """,

    'author': "Dclick Soluciones",
    'website': "https://dreamsolutionsco.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'security', 'professional_registers'],

    # always loaded
    'data': [
        'security/categorias.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/conection_test_view.xml',
        'views/menu.xml',
    ],
    'qweb': [
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
