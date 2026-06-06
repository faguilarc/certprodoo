# -*- coding: utf-8 -*-
{
    'name': "Nomencladores",

    'summary': """
        Nomencladores del sistema Registro de Profesionales""",

    'description': """
        Gestión de los nomencladores del sistema Registro de Profesionales
    """,

    'author': "Adrián Hernández Aguilera",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Nomenclators',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'security', 'base_address_city'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        #Data
        'data/nomenclators_data.xml',

        'data/res_country_state_data.xml',
        'data/res_city_data.xml',
        'data/res_organism_data.xml',
        'data/procedure_type_data.xml',
        'data/nationality_data.xml',
        'data/term_and_conditions_data.xml',
        #Views
        'views/professions_view.xml',
        'views/specialties_view.xml',
        # 'views/teaching_level_view.xml',
        'views/study_center_view.xml',
        'views/professional_language_view.xml',
        'views/labour_sector_view.xml',
        'views/detention_causes_view.xml',
        'views/teaching_categories_view.xml',
        'views/document_required_view.xml',
        'views/res_country_view.xml',
        'views/res_country_state_view.xml',
        'views/res_city_view.xml',
        "views/dashboard_security.xml",
        "views/assets.xml",
        'views/res_organism_view.xml',
        'views/procedure_type_view.xml',
        'views/terms_conditions_view.xml',
        'views/nationality_view.xml',
        'views/logo_view.xml',
        'views/structures_view.xml',
        'views/who_enrrolls_view.xml',
        'views/normative_view.xml',

        'views/menu.xml',

        # Wizard
        'wizard/documents_required_wizard.xml',

        #Reports
        'views/menu_reports.xml',
        'report/report_documents_required.xml',
    ],
    "qweb": [
        "static/src/xml/dashboard.xml",
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
