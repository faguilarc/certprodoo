# -*- coding: utf-8 -*-
{
    "name": "CertProdoo Security",
    "summary": "Módulo de seguridad, permisos y roles del sistema CertProdoo",
    "description": """
        Sistema de permisos granular para CertProdoo que proporciona:
        - Roles: Perfiles de permisos asignables a usuarios
        - Opciones: Mapeo de pantallas/modelos securizables
        - Permisos por Rol: Visibilidad (propias/todas) y escritura por rol y opción
        - Permisos por Usuario: Sobreescribir permisos del rol a nivel usuario
        - Permisos por Estado: Control de quién puede ejecutar transiciones
        - Motor de permisos basado en ir.rules (reemplaza fields_view_get/search_read)
        - Dashboard de estadísticas de seguridad
        - Wizard de limpieza de base de datos

        Migración de Odoo 14 → 17:
        - fields_view_get + search_read → ir.rule + computed attrs
        - security.traces → certprodoo.audit.mixin (heredado de certprodoo_base)
        - security.state_configuration → certprodoo.base.state.config
        - security.configure_keys → certprodoo.base.api.config
        - AbstractAction dashboard → OWL component
        - attrs → Python expression syntax
    """,
    "author": "Frank Aguilar Caraballo",
    "website": "https://github.com/faguilarc/certprodoo",
    "category": "CertProdoo/Security",
    "version": "17.0.1.0.0",
    "depends": ["base", "mail", "certprodoo_base"],
    "data": [
        "security/security_groups.xml",
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "data/default_roles.xml",
        "views/security_role_views.xml",
        "views/security_option_views.xml",
        "views/security_role_permission_views.xml",
        "views/security_user_permission_views.xml",
        "views/security_state_permission_views.xml",
        "views/res_users_views.xml",
        "views/res_company_views.xml",
        "views/dashboard_views.xml",
        "views/menu.xml",
        "wizard/clean_registers_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "certprodoo_security/static/src/js/security_dashboard.js",
        ],
        "web.assets_backend_css": [
            "certprodoo_security/static/src/css/dashboard.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
