# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Notificaciones",
    "summary": "Módulo de notificaciones",
    "version": "1.0",
    "category": "Personal",
    "author": "Dclick Soluciones",
    "description": "Gestionar Notificaciones y Avisos",
    "website": "",
    "depends": ["base", "web_notify", "base_automation", 'security'],
    "data": [
        # SECURITY
        "security/ir.model.access.csv",
        # DATA DEFAULT
        # VIEWS
        "views/manage_notifications.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
