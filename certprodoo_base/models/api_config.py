# -*- coding: utf-8 -*-
"""
ApiConfig — Configuración de APIs externas.

Unifica las credenciales FUC que estaban en:
- security.configure_keys (key_1, key_2, url, url_base)
- fuc_connector.fuc_config (key_1, key_2, url_token, url_base)

En Odoo 17, toda configuración de API externa se gestiona desde
este modelo único, eliminando la duplicación.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApiConfig(models.Model):
    """Configuración de conexión a APIs externas.

    Soporta múltiples tipos de autenticación y APIs.
    Cada API tiene su propio registro de configuración.

    Uso:
        config = self.env['certprodoo.base.api.config'].search(
            [('api_type', '=', 'fuc')], limit=1
        )
    """
    _name = "certprodoo.base.api.config"
    _description = "Configuración de API Externa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    api_type = fields.Selection(
        [
            ("fuc", "Ficha Única de Ciudadano (FUC)"),
            ("other", "Otra API"),
        ],
        string="Tipo de API",
        required=True,
        default="fuc",
        tracking=True,
    )
    active = fields.Boolean(
        string="Activa",
        default=True,
    )

    # ─── Credenciales ───────────────────────────────────────────

    key_1 = fields.Char(
        string="Clave del Consumidor (Key 1)",
        tracking=True,
        help="Client ID o Consumer Key para la autenticación.",
    )
    key_2 = fields.Char(
        string="Secreto del Consumidor (Key 2)",
        tracking=True,
        help="Client Secret o Consumer Secret para la autenticación.",
    )

    # ─── URLs ───────────────────────────────────────────────────

    url = fields.Char(
        string="URL de Autenticación (Token)",
        tracking=True,
        help="URL del endpoint de autenticación para obtener tokens.",
    )
    url_base = fields.Char(
        string="URL Base (Consultas)",
        tracking=True,
        help="URL base del endpoint de consulta de datos.",
    )

    # ─── Configuración de Autenticación ─────────────────────────

    auth_type = fields.Selection(
        [
            ("oauth2_client", "OAuth2 Client Credentials"),
            ("basic", "Basic Auth"),
            ("bearer", "Bearer Token"),
            ("api_key", "API Key"),
        ],
        string="Tipo de Autenticación",
        default="oauth2_client",
        required=True,
        tracking=True,
    )
    scope = fields.Char(
        string="Scope / Alcance",
        default="nivel10",
        help="Scope para OAuth2 (ej. 'nivel10' para FUC).",
    )
    grant_type = fields.Char(
        string="Grant Type",
        default="client_credentials",
        help="Tipo de concesión OAuth2 (default: client_credentials).",
    )

    # ─── Token ──────────────────────────────────────────────────

    token = fields.Text(
        string="Token Actual",
        readonly=True,
        copy=False,
    )
    token_expiry = fields.Datetime(
        string="Fecha de Expiración del Token",
        readonly=True,
    )
    last_test = fields.Datetime(
        string="Última Prueba",
        readonly=True,
    )
    last_test_result = fields.Text(
        string="Resultado de la Última Prueba",
        readonly=True,
    )
    use_simulation = fields.Boolean(
        string="Usar Simulación",
        default=False,
        tracking=True,
        help="Usa un servidor local de simulación en lugar de la API real.",
    )

    # ─── Configuración de Reintentos ────────────────────────────

    max_retries = fields.Integer(
        string="Máximo de Reintentos",
        default=3,
        help="Número máximo de reintentos en caso de fallo.",
    )
    retry_delay = fields.Integer(
        string="Demora entre Reintentos (seg)",
        default=3,
        help="Segundos de espera entre reintentos.",
    )
    request_timeout = fields.Integer(
        string="Timeout de Solicitud (seg)",
        default=10,
        help="Segundos de espera máxima por respuesta.",
    )

    # ─── Constraints ────────────────────────────────────────────

    _sql_constraints = [
        (
            "api_type_uniq",
            "unique (api_type)",
            "Solo puede existir una configuración por tipo de API!",
        ),
    ]

    # ─── Métodos ────────────────────────────────────────────────

    @api.model
    def get_fuc_config(self):
        """Retorna la configuración FUC activa.

        Returns:
            recordset: Configuración FUC.
        """
        config = self.search([("api_type", "=", "fuc"), ("active", "=", True)], limit=1)
        if not config:
            # Buscar aunque esté inactiva
            config = self.search([("api_type", "=", "fuc")], limit=1)
        return config

    def action_test_connection(self):
        """Prueba la conexión a la API usando CubanValidator."""
        self.ensure_one()
        if self.api_type == "fuc":
            validator = self.env["certprodoo.cuban.validator"]
            try:
                validator._generate_fuc_token(self)
                self.write({
                    "last_test": fields.Datetime.now(),
                    "last_test_result": "Conexión exitosa. Token generado correctamente.",
                })
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Conexión Exitosa"),
                        "message": _("Token FUC generado correctamente."),
                        "type": "success",
                        "sticky": False,
                    },
                }
            except ValidationError as e:
                self.write({
                    "last_test": fields.Datetime.now(),
                    "last_test_result": f"Error: {e}",
                })
                raise
        raise ValidationError(_("Prueba de conexión no implementada para este tipo de API."))
