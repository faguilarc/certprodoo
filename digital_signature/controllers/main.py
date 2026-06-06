# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class DigitalSignatureVerificationController(http.Controller):

    @http.route('/digital_signature/verify/<int:request_id>/<string:token>',
                type='http', auth='public', website=True, csrf=False)
    def verify_digital_signature(self, request_id, token, **kwargs):
        """Endpoint para verificar la solicitud desde el correo"""
        try:
            # Obtener la solicitud
            signature_request = request.env['digital.signature.request'].sudo().browse(request_id)

            if not signature_request.exists():
                return request.render('digital_signature.verification_error', {
                    'error': 'Solicitud no encontrada.',
                    'request_id': request_id
                })

            # Verificar que la inscripción asociada existe
            if not signature_request.inscription_id.exists():
                return request.render('digital_signature.verification_error', {
                    'error': 'La inscripción asociada no existe.',
                    'request': signature_request
                })

            # Obtener IP del cliente
            ip_address = request.httprequest.environ.get('REMOTE_ADDR')

            # Verificar la solicitud
            result = signature_request.action_verify_by_email(token, ip_address)

            if result['success']:
                return request.render('digital_signature.verification_success', {
                    'request': signature_request,
                    'verification_date': result['verification_date'],
                    'request_name': result['request_name'],
                    'inscription': signature_request.inscription_id
                })
            else:
                return request.render('digital_signature.verification_error', {
                    'error': result['message'],
                    'request': signature_request,
                    'inscription': signature_request.inscription_id
                })

        except Exception as e:
            _logger.error("Error en verificación de firma digital: %s", str(e))
            return request.render('digital_signature.verification_error', {
                'error': f'Error del sistema: {str(e)}',
                'request_id': request_id
            })

    @http.route('/digital_signature/request/<int:request_id>/status',
                type='http', auth='public', website=True)
    def check_request_status(self, request_id, **kwargs):
        """Página para ver el estado de una solicitud"""
        signature_request = request.env['digital.signature.request'].sudo().browse(request_id)

        if not signature_request.exists():
            return request.render('digital_signature.verification_error', {
                'error': 'Solicitud no encontrada.'
            })

        # Verificar que la inscripción existe
        if not signature_request.inscription_id.exists():
            return request.render('digital_signature.verification_error', {
                'error': 'La inscripción asociada no existe.'
            })

        return request.render('digital_signature.request_status', {
            'signature_request': signature_request,
            'inscription': signature_request.inscription_id
        })

    @http.route('/digital_signature/inscription/<int:inscription_id>/requests',
                type='http', auth='public', website=True)
    def view_inscription_requests(self, inscription_id, **kwargs):
        """Página para ver todas las solicitudes de una inscripción"""
        inscription = request.env['professional_registers.inscription'].sudo().browse(inscription_id)

        if not inscription.exists():
            return request.render('digital_signature.verification_error', {
                'error': 'Inscripción no encontrada.'
            })

        # Filtrar solo solicitudes visibles para el usuario actual
        partner_id = request.env.user.partner_id.id if request.env.user else None
        requests = inscription.digital_signature_request_ids

        # Si no es admin, filtrar por partner
        if partner_id and not request.env.user.has_group('base.group_system'):
            requests = requests.filtered(
                lambda r: r.inscription_id.partner_id.id == partner_id
            )

        return request.render('digital_signature.inscription_requests', {
            'inscription': inscription,
            'requests': requests,
            'has_requests': len(requests) > 0
        })