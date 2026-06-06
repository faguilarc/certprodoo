# -*- coding: utf-8 -*-
{
    'name': "Registros de Profesionales",

    'summary': """
       Gestión de los Registros de profesionales""",

    'description': """
        Gestión de los procesos de registros de profesionales y documentación
    """,

    'author': "Adrián Hernández Aguilera",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Professional Register',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'nomenclators', 'mail','dms'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_crong_data.xml',
        "views/assets.xml",
        'data/email_templates.xml',
        'views/solicitud_observacion_wizard_views.xml',
        'views/indentity_view_help.xml',
        'views/public_field_view.xml',
        'views/request_view_help.xml',
        'views/inscription_view_help.xml',
        'views/professional_request_view.xml',
        'views/public_request_view.xml',
        'views/expedient_load_identity_wizard_views.xml',
        'views/professional_request_history_view.xml',
        'views/professional_request_claim_views.xml',
        'views/professional_expedient_views.xml',
        'views/dms_expedient_menu.xml',
        'views/professional_request_update.xml',
        'views/inscription_history_view.xml',
        'views/permit_state_inherit_view.xml',
        'views/inscriptions_view.xml',
        'views/profile_view.xml',
        'views/profile_sync_log_views.xml',
        "views/dashboard_security.xml",
        "wizard/generate_request_view.xml",
        "wizard/message_view.xml",
        'views/menu.xml',
        # Reports
        'views/menu_reports.xml',
        'report/report_professional_request.xml',
        'report/report_inscriptions.xml',
        'report/report_identity.xml',
        'report/report_notification.xml',
    ],
    "qweb": [
        "static/src/xml/dashboard.xml",
        "static/src/xml/dashboard_inscriptions.xml",
        "static/src/xml/dashboard_expedients.xml",
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
