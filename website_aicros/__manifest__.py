# -*- coding: utf-8 -*-
{
    'name': "Website Aicros",

    'summary': """
        Creación de sitio web de aicros""",

    'description': """
        Creación y personalización del sitio públic de los registros profesionales
    """,

    'author': "Adrián Hernández Aguilera",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website', 'nomenclators', 'website_form', 'professional_registers'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/template.xml',
        'views/website_menu.xml',
        'views/res_user.xml',
        'views/menu.xml',
        'views/professional_public_details.xml'
    ],
    "qweb": [
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
