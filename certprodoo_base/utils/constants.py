# -*- coding: utf-8 -*-
"""
Constantes centralizadas del sistema certprodoo.

Todas las constantes que antes estaban dispersas en múltiples módulos
se centralizan aquí para facilitar el mantenimiento y la consistencia.
"""

# ─── Estados de Solicitudes ───────────────────────────────────────
REQUEST_STATE_DRAFT = "draft"
REQUEST_STATE_SUBMITTED = "submitted"
REQUEST_STATE_PROCESSING = "processing"
REQUEST_STATE_VALIDATION = "validation"
REQUEST_STATE_APPROVED = "approved"
REQUEST_STATE_DENIED = "denied"
REQUEST_STATE_CANCELLED = "cancelled"
REQUEST_STATE_STOPPED = "stopped"
REQUEST_STATE_RESOLVED = "resolved"

# Prioridad de estados (coincide con security.state_configuration.priority)
STATE_PRIORITY_DRAFT = 1
STATE_PRIORITY_PROCESSING = 2
STATE_PRIORITY_VALIDATION = 3
STATE_PRIORITY_STOPPED = 4
STATE_PRIORITY_RESOLVED = 5
STATE_PRIORITY_APPROVED = 6
STATE_PRIORITY_CANCELLED = 7
STATE_PRIORITY_DENIED = 8

# ─── Tipos de Trámite ────────────────────────────────────────────
PROCEDURE_TYPE_INSCRIPTION = "inscription"
PROCEDURE_TYPE_UPDATE = "update"
PROCEDURE_TYPE_RENEWAL = "renewal"
PROCEDURE_TYPE_CLAIM = "claim"

PROCEDURE_TYPE_SELECTION = [
    (PROCEDURE_TYPE_INSCRIPTION, "Inscripción"),
    (PROCEDURE_TYPE_UPDATE, "Actualización"),
    (PROCEDURE_TYPE_RENEWAL, "Renovación"),
    (PROCEDURE_TYPE_CLAIM, "Reclamación"),
]

# ─── Niveles de Firma Digital ─────────────────────────────────────
SIGNATURE_LEVEL_PERSONAL = "personal"
SIGNATURE_LEVEL_INSTITUTION = "institution"

SIGNATURE_LEVEL_SELECTION = [
    (SIGNATURE_LEVEL_PERSONAL, "Nivel Personal"),
    (SIGNATURE_LEVEL_INSTITUTION, "Nivel Institución"),
]

# ─── Tipos de Firma Digital ───────────────────────────────────────
SIGNATURE_TYPE_AFFILIATION = "affiliation"
SIGNATURE_TYPE_RENEWAL = "renewal"

SIGNATURE_TYPE_SELECTION = [
    (SIGNATURE_TYPE_AFFILIATION, "Filiación"),
    (SIGNATURE_TYPE_RENEWAL, "Renovación"),
]

# ─── Estados de Firma Digital ─────────────────────────────────────
SIGNATURE_STATE_DRAFT = "draft"
SIGNATURE_STATE_SUBMITTED = "submitted"
SIGNATURE_STATE_PROCESSING = "processing"
SIGNATURE_STATE_PENDING_VERIFICATION = "pending_verification"
SIGNATURE_STATE_VERIFIED = "verified"
SIGNATURE_STATE_APPROVED = "approved"
SIGNATURE_STATE_REJECTED = "rejected"
SIGNATURE_STATE_EXPIRED = "expired"

SIGNATURE_STATE_SELECTION = [
    (SIGNATURE_STATE_DRAFT, "Borrador"),
    (SIGNATURE_STATE_SUBMITTED, "Enviada"),
    (SIGNATURE_STATE_PROCESSING, "En Proceso"),
    (SIGNATURE_STATE_PENDING_VERIFICATION, "Pendiente de Verificación"),
    (SIGNATURE_STATE_VERIFIED, "Verificada"),
    (SIGNATURE_STATE_APPROVED, "Aprobada"),
    (SIGNATURE_STATE_REJECTED, "Rechazada"),
    (SIGNATURE_STATE_EXPIRED, "Expirada"),
]

# ─── Tipos de Pago ───────────────────────────────────────────────
PAYMENT_TYPE_SEAL = "sello"
PAYMENT_TYPE_EXONERATED = "exonerado"
PAYMENT_TYPE_PAID = "pagado"
PAYMENT_TYPE_UNPAID = "no_pagado"

PAYMENT_TYPE_SELECTION = [
    (PAYMENT_TYPE_SEAL, "Sello"),
    (PAYMENT_TYPE_EXONERATED, "Exonerado"),
    (PAYMENT_TYPE_PAID, "Pagado"),
    (PAYMENT_TYPE_UNPAID, "No Pagado"),
]

# ─── Tipos de Usuario ────────────────────────────────────────────
USER_TYPE_CLIENT = "client"
USER_TYPE_CLIENT_ONLINE = "client_online"
USER_TYPE_SYSTEM = "system"

USER_TYPE_SELECTION = [
    (USER_TYPE_CLIENT, "Cliente"),
    (USER_TYPE_CLIENT_ONLINE, "Cliente Online"),
    (USER_TYPE_SYSTEM, "Sistema"),
]

# ─── Sexo ─────────────────────────────────────────────────────────
SEX_MALE = "male"
SEX_FEMALE = "female"

SEX_SELECTION = [
    (SEX_MALE, "Masculino"),
    (SEX_FEMALE, "Femenino"),
]

# ─── Prioridad de Solicitudes ─────────────────────────────────────
PRIORITY_LOW = "0"
PRIORITY_NORMAL = "1"
PRIORITY_HIGH = "2"

PRIORITY_SELECTION = [
    (PRIORITY_LOW, "Baja"),
    (PRIORITY_NORMAL, "Normal"),
    (PRIORITY_HIGH, "Alta"),
]

# ─── Tipos de Autenticación API ───────────────────────────────────
API_AUTH_OAUTH2_CLIENT_CREDENTIALS = "oauth2_client"
API_AUTH_BASIC = "basic"
API_AUTH_BEARER = "bearer"
API_AUTH_API_KEY = "api_key"

API_AUTH_SELECTION = [
    (API_AUTH_OAUTH2_CLIENT_CREDENTIALS, "OAuth2 Client Credentials"),
    (API_AUTH_BASIC, "Basic Auth"),
    (API_AUTH_BEARER, "Bearer Token"),
    (API_AUTH_API_KEY, "API Key"),
]

# ─── Acciones de Auditoría ────────────────────────────────────────
AUDIT_ACTION_CREATE = "create"
AUDIT_ACTION_WRITE = "write"
AUDIT_ACTION_UNLINK = "unlink"
AUDIT_ACTION_STATE_CHANGE = "state_change"
AUDIT_ACTION_READ = "read"

AUDIT_ACTION_SELECTION = [
    (AUDIT_ACTION_CREATE, "Creación"),
    (AUDIT_ACTION_WRITE, "Edición"),
    (AUDIT_ACTION_UNLINK, "Eliminación"),
    (AUDIT_ACTION_STATE_CHANGE, "Cambio de Estado"),
    (AUDIT_ACTION_READ, "Lectura"),
]

# ─── Configuración FUC ───────────────────────────────────────────
FUC_DEFAULT_TOKEN_URL = "https://apis-fuc.minjus.gob.cu/token"
FUC_DEFAULT_BASE_URL = "https://apis-fuc.minjus.gob.cu/pn-api-consulta/2.0.210131/api/v1/nivel10?"
FUC_SCOPE = "nivel10"
FUC_GRANT_TYPE = "client_credentials"
FUC_MAX_RETRIES = 3
FUC_RETRY_DELAY_SECONDS = 3
FUC_REQUEST_TIMEOUT = 10

# ─── Configuración de Tokens de Verificación ──────────────────────
VERIFICATION_TOKEN_LENGTH = 32
VERIFICATION_EXPIRY_DAYS = 7

# ─── Constantes de País ──────────────────────────────────────────
CUBA_COUNTRY_CODE = "CU"
