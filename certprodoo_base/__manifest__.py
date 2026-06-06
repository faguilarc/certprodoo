# -*- coding: utf-8 -*-
{
    "name": "CertProdoo Base",
    "summary": "Módulo base del sistema de Registro Profesional",
    "description": """
        Módulo fundacional que proporciona modelos abstractos, mixins,
        utilidades y constantes compartidas por todos los módulos del
        sistema certprodoo. Incluye:
        - BaseProcessRequest: Modelo abstracto para solicitudes con state y kanban_state
        - AuditMixin: Trazabilidad automática de operaciones CRUD (configurable vs chatter)
        - StateMixin: Máquina de estados configurable con historial
        - CubanValidator: Validaciones de CI y FUC para Cuba
        - SequenceMixin: Secuencias nominadas dinámicas
        - ApiConfig: Configuración de APIs externas (FUC)
        - SystemConfig: Parámetros globales del sistema
        - ProcessHistory: Historial de cambios de estado
        - StateTransition: Transiciones con correo automático, adjuntos y timers
        - StateTimer: Reglas de auto-transición por tiempo
        - StateChangeWizard: Asistente para cambio de estado guiado
    """,
    "author": "Frank Aguilar Caraballo",
    "website": "https://github.com/faguilarc/certprodoo",
    "category": "CertProdoo/Base",
    "version": "17.0.1.1.0",
    "depends": ["base", "mail"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "data/default_config.xml",
        "data/sequence_data.xml",
        "views/api_config_views.xml",
        "views/system_config_views.xml",
        "views/audit_log_views.xml",
        "views/state_config_views.xml",
        "views/menu.xml",
    ],
    # Assets se agregarán cuando existan archivos JS/CSS reales
    # "assets": {
    #     "web.assets_backend": [
    #         "certprodoo_base/static/src/js/*.js",
    #         "certprodoo_base/static/src/css/*.css",
    #     ],
    # },
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
