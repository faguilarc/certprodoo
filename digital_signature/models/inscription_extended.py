# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProfessionalRegistersInscription(models.Model):
    _inherit = 'professional_registers.inscription'

    # Relación con las solicitudes de firma digital
    digital_signature_request_ids = fields.One2many(
        'digital.signature.request',
        'inscription_id',
        string='Solicitudes de Firma Digital'
    )
    digital_signature_request_count = fields.Integer(
        string='Nº Solicitudes',
        compute='_compute_digital_signature_request_count'
    )

    # Campos útiles para la firma digital
    has_active_signature = fields.Boolean(
        string='Tiene Firma Activa',
        compute='_compute_has_active_signature'
    )
    last_signature_request = fields.Many2one(
        'digital.signature.request',
        string='Última Solicitud',
        compute='_compute_last_signature_request'
    )

    @api.depends('digital_signature_request_ids')
    def _compute_digital_signature_request_count(self):
        for rec in self:
            rec.digital_signature_request_count = len(rec.digital_signature_request_ids)

    @api.depends('digital_signature_request_ids')
    def _compute_has_active_signature(self):
        for rec in self:
            # Verificar si tiene alguna solicitud aprobada y no expirada
            approved_requests = rec.digital_signature_request_ids.filtered(
                lambda r: r.state == 'approved' and
                          (not r.expiry_date or r.expiry_date > fields.Date.today())
            )
            rec.has_active_signature = bool(approved_requests)

    @api.depends('digital_signature_request_ids')
    def _compute_last_signature_request(self):
        for rec in self:
            if rec.digital_signature_request_ids:
                rec.last_signature_request = rec.digital_signature_request_ids.sorted(
                    key=lambda r: r.create_date, reverse=True
                )[0]
            else:
                rec.last_signature_request = False

    def action_view_digital_signature_requests(self):
        """Acción para ver las solicitudes de firma digital de esta inscripción"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitudes de Firma Digital',
            'res_model': 'digital.signature.request',
            'view_mode': 'tree,form',
            'domain': [('inscription_id', '=', self.id)],
            'context': {'default_inscription_id': self.id},
        }

    def action_request_digital_signature(self):
        """Abrir wizard para solicitar firma digital"""
        self.ensure_one()

        # Verificar que la inscripción esté aprobada
        if self.priority != 1:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Inscripción no Aprobada',
                    'message': 'La inscripción debe estar aprobada para solicitar firma digital.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitar Firma Digital',
            'res_model': 'digital.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_inscription_id': self.id,
                'default_config_id': self.env['digital.signature.config'].get_active_config().id,
            },
        }