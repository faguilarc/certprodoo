# -*- coding: utf-8 -*-

{
    "name": "Seguridad",
    "summary": """
        Permisos de Lectura y Escritura""",
    "description": """
        Permisos de Lectura y Escritura para módulos de Odoo
    """,
    "author": "Adrián Hernández Aguilera",
    "website": "",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Técnico/Security",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "mail"],
    # always loaded
    "data": [
        "security/categories.xml",
        "security/security.xml",
        "security/ir.model.access.csv",

        "data/rol_data.xml",

        'wizard/clean_register_view.xml',

        "views/roles.xml",
        "views/permits_role.xml",
        "views/permits_option.xml",
        "views/permits_state.xml",
        "views/configuration.xml",
        "views/options.xml",
        "views/res_user.xml",
        "views/dashboard_security.xml",
        "views/assets.xml",
        "views/traces_view.xml",
        "views/configure_parameters_fuc_view.xml",
        "views/menu.xml",

    ],
    "qweb": [
        "static/src/xml/dashboard.xml",
    ],
    "installable": True,
    "application": True,
    "images": ["static/description/icon.png"],
}
