# -*- coding: utf-8 -*-
"""
ResUsers Inherit — Extiende usuarios con rol y tipo.

Agrega campos:
- certprodoo_role_id: Rol de seguridad asignado
- user_type: Tipo de usuario (cliente, cliente_online, sistema)

En O14 era security.models.res_user.
"""

from odoo import models, fields, api, _


class ResUsers(models.Model):
    """Extensión de usuarios para CertProdoo.

    Agrega el rol de seguridad y el tipo de usuario,
    que determinan los permisos en el sistema.
    """
    _inherit = "res.users"

    certprodoo_role_id = fields.Many2one(
        "certprodoo.security.role",
        string="Rol de Seguridad",
        tracking=True,
        help="Rol de seguridad asignado al usuario. "
             "Determina los permisos base del usuario en el sistema.",
    )
    user_type = fields.Selection(
        [("client", "Cliente"),
         ("client_online", "Cliente Online"),
         ("system", "Sistema")],
        string="Tipo de Usuario",
        default="system",
        tracking=True,
        help="Clasificación del usuario:\n"
             "- Cliente: Usuario que solicita trámites presencialmente\n"
             "- Cliente Online: Usuario que solicita trámites por el portal web\n"
             "- Sistema: Usuario interno que procesa trámites",
    )

    # ─── Métodos de Permisos ──────────────────────────────────

    def _get_effective_permission(self, option):
        """Obtiene el permiso efectivo del usuario para una opción.

        La precedencia es:
        1. Permiso explícito de usuario (user_permission)
        2. Permiso del rol del usuario (role_permission)
        3. Por defecto: propias, sin escritura

        Args:
            option: Record de certprodoo.security.option o ID.

        Returns:
            dict: {'perm_show': str, 'field_write': bool}
        """
        self.ensure_one()

        if isinstance(option, int):
            option = self.env["certprodoo.security.option"].browse(option)

        # 1. Permiso explícito de usuario
        user_perm = self.env["certprodoo.security.user.permission"].search([
            ("user_id", "=", self.id),
            ("option_id", "=", option.id),
            ("active", "=", True),
        ], limit=1)

        if user_perm:
            return {
                "perm_show": user_perm.perm_show,
                "field_write": user_perm.field_write,
                "source": "user",
            }

        # 2. Permiso del rol
        if self.certprodoo_role_id:
            role_perm = self.env["certprodoo.security.role.permission"].search([
                ("role_id", "=", self.certprodoo_role_id.id),
                ("option_id", "=", option.id),
                ("active", "=", True),
            ], limit=1)

            if role_perm:
                return {
                    "perm_show": role_perm.perm_show,
                    "field_write": role_perm.field_write,
                    "source": "role",
                }

        # 3. Por defecto
        return {
            "perm_show": "propias",
            "field_write": False,
            "source": "default",
        }

    def _has_write_permission(self, model_name):
        """Verifica si el usuario tiene permiso de escritura para un modelo.

        Args:
            model_name: Nombre técnico del modelo.

        Returns:
            bool: True si tiene permiso de escritura.
        """
        self.ensure_one()

        # Administradores siempre tienen permiso
        if self.has_group("certprodoo_base.group_certprodoo_admin"):
            return True

        option = self.env["certprodoo.security.option"].search([
            ("model_name", "=", model_name),
        ], limit=1)

        if not option:
            # Si no hay opción definida, permitir (seguridad por defecto)
            return True

        perm = self._get_effective_permission(option)
        return perm["field_write"]

    def _get_visibility_domain(self, model_name):
        """Retorna el domain para filtrar registros según permisos.

        Args:
            model_name: Nombre técnico del modelo.

        Returns:
            list: Domain para filtrar registros visibles.
        """
        self.ensure_one()

        # Administradores ven todo
        if self.has_group("certprodoo_base.group_certprodoo_admin"):
            return []

        option = self.env["certprodoo.security.option"].search([
            ("model_name", "=", model_name),
        ], limit=1)

        if not option:
            return []

        perm = self._get_effective_permission(option)

        if perm["perm_show"] == "todas":
            return []  # Sin restricción adicional
        else:
            # Solo registros propios (del usuario o de su compañía)
            return ["|",
                    ("user_id", "=", self.id),
                    ("company_id", "child_of", self.company_id.ids)]
