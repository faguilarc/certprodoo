# -*- coding: utf-8 -*-
{
    'name': 'Multi-Compañía para Registros Profesionales',
    'version': '14.0.1.0.0',
    'category': 'Professional Registers',
    'summary': 'Agrega soporte multi-compañía (company_id) a todos los modelos de professional_registers',
    'description': """
        Módulo patch que agrega el campo company_id a todos los modelos del
        módulo professional_registers para habilitar el soporte multi-compañía.

        Incluye:
        - Campo company_id (Many2one a res.company) en modelos principales
        - Campo company_id (related) en modelos hijos
        - Defaults automáticos en create()
        - Record rules para filtrado por compañía
        - Vistas heredadas con el campo company_id visible
        - Dashboard models para actualizaciones y reclamaciones
    """,
    'author': 'Aicros',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'professional_registers',
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/professional_expedient_views.xml',
        'views/professional_request_update_views.xml',
        'views/professional_request_claim_views.xml',
        'data/populate_company_id.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
