from odoo import models, fields, api
import json


class FUCTest(models.TransientModel):
    _name = 'fuc.test'
    _description = 'Pruebas de Conexión a FUC'

    identity_number = fields.Char('Número de Identidad', required=True)
    use_simulation = fields.Boolean('Usar Simulación', default=False)
    test_result = fields.Html('Resultado de la Prueba', readonly=True)

    def action_test_connection(self):
        """Ejecuta la prueba de conexión a FUC"""
        config = self.env['fuc.config'].get_default_config()

        # Forzar el modo de simulación si se especifica
        original_use_simulation = config.use_simulation
        if self.use_simulation:
            config.write({'use_simulation': True})

        try:
            result = config.test_connection(self.identity_number)

            if result['status'] == 'success':
                # Mostrar los datos obtenidos
                data = result['data']
                result_html = f"""
                <div class="alert alert-success">
                    <h4>Consulta exitosa para CI: {self.identity_number}</h4>
                    <p><strong>Nombre:</strong> {data.get('primer_nombre')} {data.get('segundo_nombre', '')} {data.get('primer_apellido')} {data.get('segundo_apellido', '')}</p>
                    <p><strong>Sexo:</strong> {data.get('sexo')}</p>
                    <p><strong>Edad:</strong> {data.get('edad')}</p>
                    <p><strong>Dirección:</strong> {data.get('direccion')}</p>
                    <p><strong>Municipio:</strong> {data.get('municipio_residencia')}</p>
                    <p><strong>Provincia:</strong> {data.get('provincia_residencia')}</p>
                    <p><strong>Fecha de Nacimiento:</strong> {data.get('nacimiento_fecha')}</p>
                </div>
                """
                self.write({'test_result': result_html})
            else:
                error_html = f"""
                <div class="alert alert-danger">
                    <h4>Error en la consulta</h4>
                    <p>{result['message']}</p>
                </div>
                """
                self.write({'test_result': error_html})

        except Exception as e:
            error_html = f"""
            <div class="alert alert-danger">
                <h4>Excepción</h4>
                <p>Ocurrió un error al probar la conexión: {str(e)}</p>
            </div>
            """
            self.write({'test_result': error_html})
        finally:
            # Restaurar el modo de simulación original
            if self.use_simulation:
                config.write({'use_simulation': original_use_simulation})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fuc.test',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_token(self):
        """Genera un nuevo token"""
        config = self.env['fuc.config'].get_default_config()
        result = config.generate_token()

        if result['status'] == 'success':
            success_html = f"""
            <div class="alert alert-success">
                <h4>Token generado correctamente</h4>
                <p>{result['message']}</p>
            </div>
            """
            self.write({'test_result': success_html})
        else:
            error_html = f"""
            <div class="alert alert-danger">
                <h4>Error al generar token</h4>
                <p>{result['message']}</p>
            </div>
            """
            self.write({'test_result': error_html})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fuc.test',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }