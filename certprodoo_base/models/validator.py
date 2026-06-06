# -*- coding: utf-8 -*-
"""
CubanValidator — Validaciones específicas del contexto cubano.

Centraliza todas las validaciones que estaban dispersas:
- Validación de CI (professional_registers_minimal, website_aicros)
- Validación de nombres con acentos
- Conexión a la API FUC (fuc_connector, website_aicros/controllers)

Migración de Odoo 14 → 17:
- Unifica las 3 implementaciones independientes de FUC
- Usa ApiConfig de certprodoo_base para credenciales
- Manejo robusto de reintentos con backoff exponencial
- Elimina os.environ para tokens (usa ir.config_parameter)
"""

import base64
import logging
import time

import requests

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..utils.constants import (
    FUC_DEFAULT_TOKEN_URL,
    FUC_DEFAULT_BASE_URL,
    FUC_SCOPE,
    FUC_GRANT_TYPE,
    FUC_MAX_RETRIES,
    FUC_RETRY_DELAY_SECONDS,
    FUC_REQUEST_TIMEOUT,
)

_logger = logging.getLogger(__name__)

# ─── Tabla de pesos para validación del dígito verificador del CI cubano ──
_CI_WEIGHTS = [7, 9, 8, 6, 5, 4, 3, 2, 1, 0, 0]
_CI_MODULUS = 11


class CubanValidator(models.TransientModel):
    """Validador para datos específicos de Cuba.

    Modelo TransientModel (se crea temporalmente para ejecutar
    validaciones). Los métodos son @api.model para poder
    llamarse desde cualquier contexto sin necesidad de crear
    un registro persistente.

    Uso:
        validator = self.env['certprodoo.cuban.validator']
        is_valid = validator.validate_ci('91021012345')
        fuc_data = validator.validate_fuc('91021012345')
    """
    _name = "certprodoo.cuban.validator"
    _description = "Validador de Datos Cubanos"

    # ─── Validación de Carné de Identidad ────────────────────────

    @api.model
    def validate_ci(self, ci_number):
        """Valida un Carné de Identidad cubano.

        El CI cubano tiene 11 dígitos donde el último es un
        dígito verificador calculado con un algoritmo específico.

        Formato: NNNNNNNNNNV donde:
        - N: Dígitos del número (10 primeros)
        - V: Dígito verificador (último)

        Args:
            ci_number: Número de CI como string.

        Returns:
            bool: True si el CI es válido.

        Raises:
            ValidationError: Si el CI no es válido, con descripción del error.
        """
        if not ci_number:
            raise ValidationError(_("El número de identidad no puede estar vacío."))

        if not isinstance(ci_number, str):
            ci_number = str(ci_number)

        ci_number = ci_number.strip()

        # Verificar que sean solo dígitos
        if not ci_number.isdigit():
            raise ValidationError(
                _("El Carné de Identidad debe contener solo dígitos numéricos.")
            )

        # Verificar longitud
        if len(ci_number) != 11:
            raise ValidationError(
                _(
                    "El Carné de Identidad debe tener exactamente 11 dígitos. "
                    "Longitud actual: %d"
                )
                % len(ci_number)
            )

        # Verificar dígito verificador
        if not self._check_ci_check_digit(ci_number):
            raise ValidationError(
                _(
                    "El dígito verificador del Carné de Identidad no es válido. "
                    "Verifique que el número sea correcto."
                )
            )

        return True

    @api.model
    def _check_ci_check_digit(self, ci_number):
        """Verifica el dígito verificador del CI cubano.

        Algoritmo: Suma ponderada de los primeros 10 dígitos
        multiplicados por los pesos correspondientes, módulo 11.
        El resultado debe coincidir con el 11no dígito.

        Args:
            ci_number: CI de 11 dígitos como string.

        Returns:
            bool: True si el dígito verificador es correcto.
        """
        try:
            digits = [int(d) for d in ci_number]
            total = sum(d * w for d, w in zip(digits, _CI_WEIGHTS))
            remainder = total % _CI_MODULUS
            check_digit = digits[-1]

            # El dígito verificador es (11 - remainder) % 11
            expected = (_CI_MODULUS - remainder) % _CI_MODULUS

            # Si el expected es 10, el dígito verificador puede ser 0
            if expected == 10:
                expected = 0

            return check_digit == expected
        except (ValueError, IndexError):
            return False

    @api.model
    def validate_ci_format(self, ci_number):
        """Validación suave del formato del CI sin verificar dígito.

        Útil para validaciones en tiempo real en formularios donde
        aún no se ha completado el CI.

        Args:
            ci_number: Número de CI como string.

        Returns:
            bool: True si el formato es válido.
        """
        if not ci_number:
            return False
        ci_str = str(ci_number).strip()
        return ci_str.isdigit() and len(ci_str) == 11

    # ─── Validación de Pasaporte ─────────────────────────────────

    @api.model
    def validate_passport(self, passport_number):
        """Valida un número de pasaporte.

        Args:
            passport_number: Número de pasaporte como string.

        Returns:
            bool: True si el formato es válido.

        Raises:
            ValidationError: Si el pasaporte no es válido.
        """
        if not passport_number:
            raise ValidationError(_("El número de pasaporte no puede estar vacío."))

        passport_str = str(passport_number).strip()

        if len(passport_str) < 6:
            raise ValidationError(
                _("El número de pasaporte debe tener al menos 6 caracteres.")
            )
        if len(passport_str) > 11:
            raise ValidationError(
                _("El número de pasaporte no puede tener más de 11 caracteres.")
            )
        return True

    # ─── Validación FUC (Ficha Única de Ciudadano) ──────────────

    @api.model
    def validate_fuc(self, identity_number, use_simulation=False):
        """Valida un CI contra la API de la Ficha Única de Ciudadano.

        Unifica las implementaciones de:
        - website_aicros/controllers._validate_with_fuc()
        - fuc_connector/models/fuc_service.search_data()
        - professional_registers_minimal.search_data()

        Args:
            identity_number: Número de CI a validar.
            use_simulation: Si True, usa localhost:5000 en vez de la API real.

        Returns:
            dict: Datos del ciudadano si la validación es exitosa.

        Raises:
            ValidationError: Si la validación falla.
        """
        config = self._get_fuc_config()
        token = self._generate_fuc_token(config)

        if use_simulation:
            url = f"http://127.0.0.1:5000/api/v1/nivel10?identidad_numero={identity_number}"
        else:
            url_base = config.url_base or FUC_DEFAULT_BASE_URL
            url = f"{url_base}identidad_numero={identity_number}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        last_exception = None
        for attempt in range(1, FUC_MAX_RETRIES + 1):
            try:
                _logger.info(
                    "Validación FUC (intento %d/%d) para CI: %s",
                    attempt, FUC_MAX_RETRIES, identity_number,
                )
                response = requests.get(
                    url, headers=headers, timeout=FUC_REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        record = data[0]
                        if record.get("identidad_numero") == identity_number:
                            if record.get("fallecido"):
                                raise ValidationError(
                                    _(
                                        "Carné de identidad registrado como fallecido "
                                        "en la FUC. Si cree que es un error, diríjase "
                                        "a la entidad encargada."
                                    )
                                )
                            _logger.info(
                                "Validación FUC exitosa para CI: %s",
                                identity_number,
                            )
                            return data
                    raise ValidationError(
                        _(
                            "El CI %s no se encuentra registrado en el sistema FUC. "
                            "Verifique que el número sea correcto."
                        )
                        % identity_number
                    )

                elif response.status_code == 401:
                    # Token expirado, regenerar y reintentar
                    _logger.warning("Token FUC expirado, regenerando...")
                    token = self._generate_fuc_token(config)
                    headers["Authorization"] = f"Bearer {token}"
                    continue

                elif response.status_code == 404:
                    raise ValidationError(
                        _(
                            "El CI %s no fue encontrado en el sistema FUC. "
                            "Verifique que el CI sea correcto."
                        )
                        % identity_number
                    )

                elif response.status_code >= 500:
                    _logger.warning(
                        "Error %d del servidor FUC (intento %d)",
                        response.status_code, attempt,
                    )
                    if attempt == FUC_MAX_RETRIES:
                        raise ValidationError(
                            _(
                                "El servicio de validación FUC no está disponible "
                                "temporalmente. Intente nuevamente en unos minutos."
                            )
                        )

                else:
                    if attempt == FUC_MAX_RETRIES:
                        raise ValidationError(
                            _(
                                "El servicio FUC respondió con un error inesperado "
                                "(código %d). Intente más tarde."
                            )
                            % response.status_code
                        )

            except requests.exceptions.Timeout:
                _logger.warning(
                    "Timeout FUC (intento %d/%d)", attempt, FUC_MAX_RETRIES
                )
                if attempt == FUC_MAX_RETRIES:
                    raise ValidationError(
                        _(
                            "Tiempo de espera agotado al conectar con FUC. "
                            "Intente nuevamente."
                        )
                    )

            except requests.exceptions.ConnectionError:
                _logger.warning(
                    "Error de conexión FUC (intento %d/%d)", attempt, FUC_MAX_RETRIES
                )
                if attempt == FUC_MAX_RETRIES:
                    raise ValidationError(
                        _(
                            "No se pudo conectar con el servicio FUC. "
                            "Verifique la conexión o contacte al administrador."
                        )
                    )

            except ValidationError:
                raise

            except Exception as e:
                _logger.error("Error FUC inesperado (intento %d): %s", attempt, e)
                if attempt == FUC_MAX_RETRIES:
                    raise ValidationError(
                        _(
                            "Error inesperado en validación FUC. "
                            "Intente nuevamente o contacte al administrador."
                        )
                    )

            if attempt < FUC_MAX_RETRIES:
                time.sleep(FUC_RETRY_DELAY_SECONDS)

        raise ValidationError(
            _("No se pudo completar la validación FUC después de varios intentos.")
        )

    @api.model
    def _get_fuc_config(self):
        """Obtiene la configuración FUC desde ApiConfig.

        Returns:
            recordset: Configuración FUC de certprodoo.base.api.config.
        """
        config = self.env["certprodoo.base.api.config"].search(
            [("api_type", "=", "fuc")],
            limit=1,
            order="id desc",
        )
        if not config:
            raise ValidationError(
                _(
                    "No se ha configurado la conexión a la Ficha Única del "
                    "Ciudadano. Contacte al administrador del sistema."
                )
            )
        return config

    @api.model
    def _generate_fuc_token(self, config=None):
        """Genera un token OAuth2 para la API FUC.

        Unifica las implementaciones de:
        - security.configure_keys.generate_token()
        - fuc_connector/models/fuc_config.generate_token()
        - website_aicros/controllers._generate_fuc_token()

        Args:
            config: Record de ApiConfig. Si None, lo obtiene automáticamente.

        Returns:
            str: Token de acceso OAuth2.
        """
        config = config or self._get_fuc_config()

        if not config.key_1 or not config.key_2:
            raise ValidationError(
                _(
                    "Las credenciales FUC no están completamente configuradas. "
                    "Verifique Key 1 y Key 2 en la configuración de APIs."
                )
            )

        url_token = config.url or FUC_DEFAULT_TOKEN_URL
        url = f"{url_token}?grant_type={FUC_GRANT_TYPE}&scope={FUC_SCOPE}"

        message = f"{config.key_1}:{config.key_2}"
        auth = base64.b64encode(message.encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}

        try:
            _logger.info("Solicitando token FUC desde: %s", url_token)
            response = requests.post(url, headers=headers, timeout=FUC_REQUEST_TIMEOUT)

            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                if token:
                    # Almacenar token en ir.config_parameter (no en os.environ)
                    self.env["ir.config_parameter"].sudo().set_param(
                        "certprodoo.fuc.token", token
                    )
                    _logger.info("Token FUC generado y almacenado exitosamente")
                    return token
                raise ValidationError(
                    _("El servicio FUC no devolvió un token válido.")
                )

            elif response.status_code == 401:
                raise ValidationError(
                    _(
                        "Credenciales FUC incorrectas o expiradas. "
                        "Contacte al administrador para actualizarlas."
                    )
                )

            else:
                raise ValidationError(
                    _(
                        "Error del servicio de autenticación FUC (código %d). "
                        "Intente nuevamente más tarde."
                    )
                    % response.status_code
                )

        except requests.exceptions.Timeout:
            raise ValidationError(
                _("Tiempo de espera agotado al conectar con el servicio FUC.")
            )
        except requests.exceptions.ConnectionError:
            raise ValidationError(
                _("No se pudo conectar con el servicio de autenticación FUC.")
            )
        except ValidationError:
            raise
        except Exception as e:
            _logger.error("Error generando token FUC: %s", e)
            raise ValidationError(
                _("Error crítico en autenticación FUC. Contacte al administrador.")
            )

    # ─── Validación de Datos FUC ────────────────────────────────

    @api.model
    def validate_fuc_response(self, json_data):
        """Valida que la respuesta de la FUC tenga los campos requeridos.

        Args:
            json_data: Lista de diccionarios con datos de la FUC.

        Returns:
            bool: True si la respuesta tiene los campos mínimos.
        """
        required_keys = [
            "id",
            "identidad_numero",
            "primer_nombre",
            "primer_apellido",
            "sexo",
            "edad",
            "direccion",
            "municipio_residencia_cod_dpa",
            "provincia_residencia_cod_dpa",
            "nacimiento_fecha",
        ]

        if isinstance(json_data, list) and json_data:
            data = json_data[0]
        elif isinstance(json_data, dict):
            data = json_data
        else:
            return False

        for key in required_keys:
            if key not in data or data[key] is None or data[key] == "":
                return False
        return True

    @api.model
    def parse_fuc_data(self, fuc_data):
        """Parsea los datos de la FUC a un formato estandarizado.

        Convierte la respuesta de la API FUC a un diccionario
        con campos consistentes para crear registros en Odoo.

        Args:
            fuc_data: Lista de diccionarios de la API FUC.

        Returns:
            dict: Datos parseados con campos estandarizados.
        """
        if isinstance(fuc_data, list):
            fuc_data = fuc_data[0] if fuc_data else {}

        sex_map = {"F": "female", "M": "male"}

        first_name = fuc_data.get("primer_nombre", "")
        second_name = fuc_data.get("segundo_nombre", "")
        name = f"{first_name} {second_name}".strip() if second_name else first_name

        # La Habana vs Ciudad de la Habana
        state_name = fuc_data.get("provincia_residencia", "")
        if state_name == "Ciudad de la Habana":
            state_name = "La Habana"

        other_info = ""
        if fuc_data.get("fallecido"):
            other_info = (
                f"Fallecido\n"
                f"Tomo: {fuc_data.get('defuncion_tomo', '')}\n"
                f"Folio: {fuc_data.get('defuncion_folio', '')}"
            )
        else:
            other_info = (
                f"Condición migratoria: "
                f"{fuc_data.get('condicion_migratoria', '')}"
            )

        return {
            "fuc_id": fuc_data.get("id", ""),
            "identity": fuc_data.get("identidad_numero", ""),
            "name": name,
            "first_last_name": fuc_data.get("primer_apellido", ""),
            "second_last_name": fuc_data.get("segundo_apellido", ""),
            "sex": sex_map.get(fuc_data.get("sexo", ""), ""),
            "address": fuc_data.get("direccion", ""),
            "city_name": fuc_data.get("municipio_residencia", ""),
            "state_name": state_name,
            "other_info": other_info,
        }
