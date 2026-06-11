from odoo import models, fields, api


class BaseProcessRequest(models.AbstractModel):
    _name = 'professional_registers.base_process_request'
    _description = 'Base para Procesos de Solicitud'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    # Campos comunes para todos los procesos
    request_number = fields.Char('Nro. solicitud', readonly=True)
    date_request = fields.Date('Fecha solicitud', default=fields.Date.today)
    user_id = fields.Many2one('res.users', string="Usuario solicitante", default=lambda self: self.env.user)
    observation = fields.Text('Observación')
    states = fields.Many2one('security.state_configuration', string='Estados')
    priority = fields.Integer('Prioridad', default=1)
    user_on_charge = fields.Many2one('res.users', string="Responsable")
    # Historial de cambios
    history_ids = fields.One2many(
        'professional_registers.process_history',
        'process_id',
        string='Histórico de Cambios de Estado',
        # compute='_compute_history_ids',
    )

    # @api.depends('priority')
    # def _compute_history_ids(self):
    #     """Calcula los registros de historial de manera optimizada para múltiples registros"""
    #
    #
    #     # Obtener todos los IDs de los registros actuales
    #     record_ids = self.ids
    #     if not record_ids:
    #         return []
    #
    #     # Construir las referencias para todos los registros
    #     model_name = self._name
    #     references = [f'{model_name},{id}' for id in record_ids]
    #
    #     # Buscar todos los registros de historial de una sola vez
    #     history_records = self.env['professional_registers.process_history'].search([
    #         ('process_id', 'in', references)
    #     ], order='date desc')
    #     if not history_records:
    #         self.history_ids = []
    #
    #
    #     # Agrupar por referencia
    #     history_by_ref = {}
    #     for history in history_records:
    #         history_by_ref.setdefault(history.process_id, []).append(history.id)
    #
    #     # Asignar a cada registro
    #     for record in self:
    #         ref = f'{model_name},{record.id}'
    #         record.history_ids = history_by_ref.get(record, [])

    # Documentación
    attachment_ids = fields.Many2many('ir.attachment', string="Documentos adjuntos")

    # @api.model
    # def create(self, vals):
    #     # Generar número de solicitud si no existe
    #     if 'request_number' not in vals or not vals['request_number']:
    #         sequence_code = self._get_sequence_code()
    #         vals['request_number'] = self.env['ir.sequence'].next_by_code(sequence_code) or 'REQ00000'
    #     return super().create(vals)

    def _get_sequence_code(self):
        # Método a sobreescribir en cada modelo concreto
        raise NotImplementedError

    def _get_states_domain(self):
        # Método a sobreescribir en cada modelo concreto
        raise NotImplementedError

    def _get_default_state(self):
        # Método a sobreescribir en cada modelo concreto
        raise NotImplementedError

    def add_history(self,process,state_id, observation=None):
        """Añadir entrada al historial"""
        for record in self:

            self.env['professional_registers.process_history'].create({
                'process_id': process,
                'state_id': state_id,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'observation': observation or f"Cambio de estado"
            })

    def generate_notifications(self, state_priority):
        # Método a implementar en cada modelo concreto
        raise NotImplementedError