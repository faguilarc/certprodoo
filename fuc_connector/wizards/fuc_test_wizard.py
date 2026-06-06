from odoo import models, fields, api, exceptions
import json


class FUCTestWizard(models.TransientModel):
    _name = 'fuc.test.wizard'
    _description = 'Asistente para probar la conexión a FUC'

    identity_number = fields.Char('Número de Identidad', required=True)
    use_simulation = fields.Boolean('Usar Simulación', default=False)

    def action_test(self):
        config = self.env['fuc.config'].get_default_config()

        # Forzar el modo de simulación si se especifica
        original_use_simulation = config.use_simulation
        if self.use_simulation:
            config.write({'use_simulation': True})

        try:
            result = config.test_connection(self.identity_number)

            if result['status'] == 'success':
                # Mostrar los datos obtenidos
                for data in result['data']:

                    message = f"""
                    <b>Consulta exitosa para CI: {self.identity_number}</b><br/>
                    <b>Nombre:</b> {data.get('primer_nombre')} {data.get('segundo_nombre', '')} {data.get('primer_apellido')} {data.get('segundo_apellido', '')}<br/>
                    <b>Sexo:</b> {data.get('sexo')}<br/>
                    <b>Edad:</b> {data.get('edad')}<br/>
                    <b>Dirección:</b> {data.get('direccion')}<br/>
                    <b>Municipio:</b> {data.get('municipio_residencia')}<br/>
                    <b>Provincia:</b> {data.get('provincia_residencia')}<br/>
                    <b>Fallecido:</b> {data.get('fallecido')}<br/>
                    """
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Resultado de la Prueba',
                        'res_model': 'fuc.result.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_message': message,
                        }
                    }
            else:
                raise exceptions.ValidationError(result['message'])
        finally:
            # Restaurar el modo de simulación original
            if self.use_simulation:
                config.write({'use_simulation': original_use_simulation})


class FUCResultWizard(models.TransientModel):
    _name = 'fuc.result.wizard'
    _description = 'Resultado de la prueba de conexión a FUC'

    message = fields.Html('Mensaje', readonly=True)