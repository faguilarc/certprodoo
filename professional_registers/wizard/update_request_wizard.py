from odoo import models, fields, api
from odoo.exceptions import UserError


class ProfessionalUpdateRequestWizard(models.TransientModel):
    _name = 'professional.update.request.wizard'
    _description = 'Wizard para crear solicitud de actualización'

    profile_id = fields.Many2one('professional_registers.profile', string='Perfil')
    update_type = fields.Selection([
        ('profile', 'Actualizar Perfil'),
        ('request', 'Actualizar Solicitud de Inscripción'),
    ], string='Tipo de Actualización', required=True, default='profile')

    # Campo para seleccionar la solicitud - DOMINIO CORREGIDO
    selected_request_id = fields.Many2one(
        'professional_registers.professional_request',
        string='Solicitud a Actualizar',
        domain="[('states', 'in', [3, 6]), ('identity', '=', identity_filter)]"
    )
    # Campo para filtrar por identidad (no visible en la vista)
    identity_filter = fields.Char(
        string='CI o Pasaporte',
        compute='_compute_identity_filter',
        store=False
    )

    @api.depends('profile_id')
    def _compute_identity_filter(self):
        for record in self:
            if record.profile_id:
                record.identity_filter = record.profile_id.identity
            else:
                record.identity_filter = False

    @api.model
    def default_get(self, fields_list):
        """Obtener valores por defecto desde el contexto"""
        result = super(ProfessionalUpdateRequestWizard, self).default_get(fields_list)

        # Obtener el contexto
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')

        if active_model == 'professional_registers.profile' and active_id:
            result['profile_id'] = active_id
            result['update_type'] = 'profile'
        elif active_model == 'professional_registers.professional_request' and active_id:
            request = self.env['professional_registers.professional_request'].browse(active_id)
            result['profile_id'] = request.profile_id.id
            result['update_type'] = 'request'
            # Preseleccionar la solicitud actual si es válida
            if request.state in [3, 6]:
                result['selected_request_id'] = active_id

        return result

    @api.onchange('update_type')
    def _onchange_update_type(self):
        """Limpiar selección si cambia a actualizar perfil"""
        if self.update_type == 'profile':
            self.selected_request_id = False

    def create_update_request(self):
        """Crear la solicitud de actualización"""
        self.ensure_one()

        # Validaciones
        if not self.selected_request_id:
            raise UserError("Debe seleccionar una solicitud para actualizar")


        # Crear la solicitud de actualización
        update_request = self.env['professional_registers.professional_request_update'].create({
            'profile_id': self.profile_id.id,
            'original_request_id': self.selected_request_id.id

        })

        # Abrir la vista de formulario
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request_update',
            'res_id': update_request.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'}
        }
