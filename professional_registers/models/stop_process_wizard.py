# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime


class StopProcessWizard(models.TransientModel):
    _name = 'stop.process.wizard'
    _description = 'Wizard para Suspender/Reanudar Trámites'

    procedure_type_id = fields.Many2one(
        'nomenclators.procedure_types',
        string="Tipo de Trámite",
        required=True
    )
    action_type = fields.Selection(
        [('suspend', 'Suspender'), ('resume', 'Reanudar')],
        string='Acción',
        required=True
    )
    reason_ids = fields.Many2many(
        'nomenclators.detention_causes',
        string='Causas de Detención',
        required=True,

    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.user.company_id.id
    )

    state_message = fields.Html(
        string="Estado del Trámite",
        compute='_compute_state_message'
    )

    suspended_procedures_ids = fields.One2many('procedure.suspension.history', compute='_compute_suspended_procedures')

    @api.depends('procedure_type_id')
    def _compute_suspended_procedures(self):
        for record in self:
            record.suspended_procedures_ids = self.env['procedure.suspension.history'].search([
                ('resume_date', '=', False),
                ('state', '=', 'stopped')
            ])

    @api.depends('procedure_type_id')
    def _compute_action_type(self):
        for record in self:
            if record.procedure_type_id:
                if record.procedure_type_id.current_suspension_id:
                    record.action_type = 'resume'
                else:
                    record.action_type = 'suspend'

    @api.depends('procedure_type_id')
    def _compute_state_message(self):
        for record in self:
            if record.procedure_type_id:
                status = 'Detenido' if record.procedure_type_id.current_suspension_id else 'En proceso'
                color = 'red' if status == 'Detenido' else 'green'
                record.state_message = f"""
                    <div style="margin-top: 10px;">
                        <b style="color: {color};">
                            {status}
                        </b>
                    </div>
                """
            else:
                record.state_message = False

    @api.onchange('procedure_type_id')
    def _onchange_procedure_type(self):
        self._compute_action_type()
        self._compute_state_message()

    def action_confirm(self):
        self.ensure_one()
        History = self.env['procedure.suspension.history']

        if self.action_type == 'suspend':


            # Create suspension history record
            History.create({
                'procedure_type_id': self.procedure_type_id.id,
                'stop_date': fields.Datetime.now(),
                'stop_reasons': self.reason_ids,
                'stopped_by': self.env.uid
            })

            message = _('Trámite suspendido correctamente.')
        else:

            # Update suspension history record
            suspension = History.search([
                ('procedure_type_id', '=', self.procedure_type_id.id),
                ('resume_date', '=', False)
            ], limit=1)

            if suspension:
                suspension.write({
                    'resume_date': fields.Datetime.now(),
                    'resumed_by': self.env.uid
                })

            message = _('Trámite reanudado correctamente.')

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'title': _('Éxito'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_reasons_text(self):
        """Generate a text representation of the selected reasons"""
        reasons = []
        if self.reason_ids:
            reasons.extend(self.reason_ids.mapped('name'))

        return '\n'.join(reasons)

    def action_save(self):
        """Save the public field configuration and close the modal"""
        return {
            'type': 'ir.actions.act_window_close'
        }
