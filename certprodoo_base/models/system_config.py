# -*- coding: utf-8 -*-
"""
SystemConfig — Parámetros globales del sistema.

Centraliza la configuración del sistema que antes usaba
ir.config_parameter directamente o estaba hardcodeada.
"""

from odoo import models, fields, api


class SystemConfig(models.Model):
    """Parámetros globales del sistema certprodoo.

    Provee una interfaz amigable para gestionar parámetros
    que antes se almacenaban en ir.config_parameter sin
    una vista de administración dedicada.

    Los valores se sincronizan bidireccionalmente con
    ir.config_parameter para compatibilidad con código
    que usa get_param/set_param.
    """
    _name = "certprodoo.base.system.config"
    _description = "Parámetros del Sistema"
    _rec_name = "key"

    key = fields.Char(
        string="Clave",
        required=True,
        index=True,
    )
    value = fields.Text(
        string="Valor",
    )
    description = fields.Char(
        string="Descripción",
    )
    module = fields.Char(
        string="Módulo",
        default="certprodoo_base",
        help="Módulo al que pertenece este parámetro.",
    )
    is_readonly = fields.Boolean(
        string="Solo Lectura",
        default=False,
        help="Si True, el valor no se puede modificar desde la UI.",
    )

    _sql_constraints = [
        ("key_uniq", "unique (key)", "La clave del parámetro debe ser única!"),
    ]

    @api.model
    def get_param(self, key, default=None):
        """Obtiene un parámetro del sistema.

        Busca primero en este modelo, luego en ir.config_parameter
        para compatibilidad con código legacy.

        Args:
            key: Clave del parámetro.
            default: Valor por defecto si no se encuentra.

        Returns:
            str: Valor del parámetro o default.
        """
        config = self.search([("key", "=", key)], limit=1)
        if config:
            return config.value
        # Fallback a ir.config_parameter
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    @api.model
    def set_param(self, key, value):
        """Establece un parámetro del sistema.

        Sincroniza tanto en este modelo como en ir.config_parameter.

        Args:
            key: Clave del parámetro.
            value: Valor a establecer.
        """
        config = self.search([("key", "=", key)], limit=1)
        if config:
            config.write({"value": str(value) if value else ""})
        else:
            self.create({"key": key, "value": str(value) if value else ""})
        # Sincronizar con ir.config_parameter
        self.env["ir.config_parameter"].sudo().set_param(key, value)

    def write(self, vals):
        if self.is_readonly and vals.get("value"):
            # Permitir solo a administradores modificar readonly
            if not self.env.user.has_group("base.group_system"):
                return self
        return super().write(vals)
