
from odoo import models, fields, api, exceptions


class ExpedientLoadIdentityWizard(models.TransientModel):
    _name = 'expedient.load.identity.wizard'
    _description = 'Wizard para cargar registros por identity'

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente', required=True)
    identity = fields.Char('Identity', required=True, help="Número de identidad del profesional")

    def action_load_records(self):
        """Carga los registros asociados al identity ingresado"""
        # Actualizar el identity en el expediente
        self.expedient_id.write({'identity': self.identity})

        # Ejecutar la carga de registros
        return self.expedient_id._execute_load_logic(profile_id=None, identity=self.identity)