# -*- coding: utf-8 -*-
"""
Generador de tokens seguros para verificación y autenticación.

Unifica la generación de tokens que antes se hacía de forma
independiente en digital_signature (SHA-256) y en los módulos
de FUC (OAuth2).
"""

import hashlib
import secrets
from datetime import datetime


def generate_verification_token(length=32):
    """Genera un token seguro para verificación por email/enlace.

    Utiliza secrets.token_bytes para entropía criptográfica y
    SHA-256 para hashing, igual que el sistema actual de
    digital_signature pero centralizado.

    Args:
        length: Longitud del token resultante (default 32).

    Returns:
        str: Token hexadecimal de la longitud especificada.
    """
    random_bytes = secrets.token_bytes(32)
    timestamp = str(datetime.now().timestamp()).encode("utf-8")
    token = hashlib.sha256(random_bytes + timestamp).hexdigest()[:length]
    return token


def generate_hmac_token(data, secret_key):
    """Genera un token HMAC-SHA256 para datos que necesitan
    verificación de integridad (ej. tokens de verificación de email
    que no deben ser manipulados).

    Args:
        data: Datos a firmar (string).
        secret_key: Clave secreta para la firma (string).

    Returns:
        str: Token HMAC en formato hexadecimal.
    """
    import hmac
    if isinstance(data, str):
        data = data.encode("utf-8")
    if isinstance(secret_key, str):
        secret_key = secret_key.encode("utf-8")
    return hmac.new(secret_key, data, hashlib.sha256).hexdigest()


def verify_hmac_token(data, secret_key, token):
    """Verifica que un token HMAC sea válido para los datos dados.

    Args:
        data: Datos originales firmados (string).
        secret_key: Clave secreta usada para la firma (string).
        token: Token HMAC a verificar (string).

    Returns:
        bool: True si el token es válido, False en caso contrario.
    """
    expected = generate_hmac_token(data, secret_key)
    import hmac
    if isinstance(expected, str):
        expected = expected.encode("utf-8")
    if isinstance(token, str):
        token = token.encode("utf-8")
    return hmac.compare_digest(expected, token)
