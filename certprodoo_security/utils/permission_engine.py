# -*- coding: utf-8 -*-
"""
Permission Engine — Lógica compartida de verificación de permisos.

Provee funciones helper para verificar permisos desde cualquier
módulo del sistema CertProdoo sin depender directamente de
certprodoo_security.

Uso:
    from certprodoo_security.utils.permission_engine import (
        check_write_permission,
        get_visibility_domain,
        check_state_permission,
    )
"""


def check_write_permission(env, user, model_name):
    """Verifica si un usuario tiene permiso de escritura para un modelo.

    Args:
        env: Odoo environment.
        user: Record de res.users.
        model_name: Nombre técnico del modelo.

    Returns:
        bool: True si tiene permiso de escritura.
    """
    return user._has_write_permission(model_name)


def get_visibility_domain(env, user, model_name):
    """Retorna el domain para filtrar registros visibles.

    Args:
        env: Odoo environment.
        user: Record de res.users.
        model_name: Nombre técnico del modelo.

    Returns:
        list: Domain para search().
    """
    return user._get_visibility_domain(model_name)


def check_state_permission(env, user, model_name, from_code, to_code):
    """Verifica si un usuario puede ejecutar una transición de estado.

    Args:
        env: Odoo environment.
        user: Record de res.users.
        model_name: Nombre técnico del modelo.
        from_code: Código del estado origen.
        to_code: Código del estado destino.

    Returns:
        bool: True si tiene permiso.
    """
    return env["certprodoo.security.state.permission"].can_user_transition(
        user, model_name, from_code, to_code
    )
