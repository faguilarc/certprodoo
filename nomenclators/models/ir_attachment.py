# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
#
# class IrAttachment(models.Model):
#     _inherit = 'ir.attachment'
#
#     @api.model
#     def create(self, vals):
#         # Validar el tamaño del archivo antes de crear el registro
#         if 'datas' in vals:
#             archivo = vals['datas']
#             tamaño_maximo = 5 * 1024 * 1024  # 5 MB en bytes
#             if len(archivo) > tamaño_maximo:
#                 # raise ValidationError("El archivo no puede exceder los 5 MB.")
#                 self._validar_tamano_archivo(archivo)
#
#         return super(IrAttachment, self).write(vals)
#
#     def write(self, vals):
#         # Validar el tamaño del archivo antes de actualizar el registro
#         if 'datas' in vals:
#             archivo = vals['datas']
#             tamaño_maximo = 5 * 1024 * 1024  # 5 MB en bytes
#             if len(archivo) > tamaño_maximo:
#                 raise ValidationError("El archivo no puede exceder los 5 MB.")
#         return super(IrAttachment, self).write(vals)
#
#     def _validar_tamano_archivo(self, archivo):
#
#         title = 'Error de subida de archivos!!!'
#         message = "El archivo no puede exceder los 5 MB."
#
#         wizard = self.env['professional_registers.message_wizard'].sudo().create({
#             'title': title,
#             'message': message,  # Aquí se pasa el mensaje HTML construido
#         })
#
#         return {
#             'name': title,
#             'type': 'ir.actions.act_window',
#             'res_model': 'professional_registers.message_wizard',
#             'view_mode': 'form',
#             'res_id': wizard.id,
#             'target': 'new',
#             'context': {
#                 'target_model': 'professional_registers.message_wizard',  # El modelo que contiene la función
#                 'target_function': None,  # La función que deseas ejecutar
#                 'target_function_args': None,  # Parámetros para la función
#                 'profile': self.id,  # Pasar el ID del perfil
#             },
#         }
