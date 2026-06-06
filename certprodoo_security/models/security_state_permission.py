# -*- coding: utf-8 -*-
"""
SecurityStatePermission — Permisos por Estado.

Controla qué usuarios pueden ejecutar transiciones de estado.
Un usuario listado aquí tiene permiso para cambiar estados
en los modelos configurados.

En O14 era security.permits_state. En O17 se mejora:
- Se vincula a StateTransition en vez de ser genérico
- Permite definir permisos por transición específica
- Integración con el motor de flujo de certprodoo_base
"""

from odoo import models, fields, api, _


class SecurityStatePermission(models.Model):
    """Permiso de usuario para ejecutar transiciones de estado.

    Controla qué usuarios pueden cambiar el estado de los registros.
    Se puede definir a nivel de:
    - Todas las transiciones (sin transition_id)
    - Una transición específica (con transition_id)
    - Un modelo específico (con model_name)

    La verificación se hace en StateTransition.execute_transition()
    consultando este modelo.
    """
    _name = "certprodoo.security.state.permission"
    _description = "Permiso por Estado"
    _rec_name = "user_id"
    _inherit = ["certprodoo.audit.mixin"]
    _order = "user_id"

    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        required=True,
        tracking=True,
        domain="[('share', '=', False)]",
        help="Usuario que tiene permiso para ejecutar transiciones.",
    )
    model_name = fields.Char(
        string="Modelo",
        tracking=True,
        help="Nombre técnico del modelo. Vacío = aplica a todos los modelos.",
    )
    transition_id = fields.Many2one(
        "certprodoo.base.state.transition",
        string="Transición Específica",
        tracking=True,
        ondelete="cascade",
        help="Transición específica permitida. Vacío = todas las transiciones del modelo.",
    )
    can_execute = fields.Boolean(
        string="Puede Ejecutar",
        default=True,
        tracking=True,
        help="Si True, el usuario puede ejecutar la transición. "
             "Si False, se le prohíbe explícitamente.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    _sql_constraints = [
        (
            "user_model_transition_uniq",
            "unique (user_id, model_name, transition_id)",
            "Ya existe un permiso para este usuario, modelo y transición!",
        ),
    ]

    # ─── Métodos de Verificación ──────────────────────────────

    @api.model
    def can_user_transition(self, user, model_name, from_code, to_code):
        """Verifica si un usuario puede ejecutar una transición.

        Args:
            user: Record de res.users.
            model_name: Nombre técnico del modelo.
            from_code: Código del estado origen.
            to_code: Código del estado destino.

        Returns:
            bool: True si el usuario tiene permiso.
        """
        # Buscar permiso específico para la transición
        specific = self.search([
            ("user_id", "=", user.id),
            ("model_name", "=", model_name),
            ("transition_id.from_code", "=", from_code),
            ("transition_id.to_code", "=", to_code),
            ("active", "=", True),
        ], limit=1)

        if specific:
            return specific.can_execute

        # Buscar permiso para el modelo (sin transición específica)
        model_perm = self.search([
            ("user_id", "=", user.id),
            ("model_name", "=", model_name),
            ("transition_id", "=", False),
            ("active", "=", True),
        ], limit=1)

        if model_perm:
            return model_perm.can_execute

        # Buscar permiso global (sin modelo ni transición)
        global_perm = self.search([
            ("user_id", "=", user.id),
            ("model_name", "=", False),
            ("transition_id", "=", False),
            ("active", "=", True),
        ], limit=1)

        if global_perm:
            return global_perm.can_execute

        # Si no hay permisos definidos, permitir por defecto
        # (la seguridad se controla por grupo en StateTransition)
        return True
