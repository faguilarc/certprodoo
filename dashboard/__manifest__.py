# -*- coding: utf-8 -*-
{
    'name': "Cuadro de Mando - Registro Profesional",

    'summary': """
        Dashboard operativo para la gestion del registro profesional""",

    'description': """
        Cuadro de Mando para la toma de decisiones del sistema de registro
        profesional. Incluye KPIs de solicitudes, inscripciones, expedientes,
        reclamaciones, tiempos de procesamiento y tasas de aprobacion/rechazo.
        Filtrado por rol y empresa.
    """,

    'author': "certprodoo",
    'website': "",
    'category': 'Dashboard',
    'version': '14.0.1.0.0',

    'depends': ['base', 'web', 'professional_registers', 'security', 'nomenclators'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/dashboard.xml',
        'views/assets.xml',
        'views/dashboard_kanban_view.xml',
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
