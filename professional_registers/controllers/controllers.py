# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


#
# class ProfessionalRegisters(http.Controller):
#     @http.route('/professional_registers/professional_registers/', auth='public')
#     def index(self, **kw):
#         print(kw)
#         # requests.post('https://apis-fuc.xutil.cu/pn-api-consulta/2.0.210111/api/v1/nivel0'
#         return "Hello, world"
#
# @http.route('/show_modal', auth='public', type='http', website=True)
# def show_modal(self, **kw):
#     modal_title = kw.get('modal_title', '')
#     message = kw.get('message', '')
#     return request.render('your_module.modal_template', {
#         'modal_title': modal_title,
#         'message': message,
#     })

#     @http.route('/professional_registers/professional_registers/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('professional_registers.listing', {
#             'root': '/professional_registers/professional_registers',
#             'objects': http.request.env['professional_registers.professional_registers'].search([]),
#         })

#     @http.route('/professional_registers/professional_registers/objects/<model("professional_registers.professional_registers"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('professional_registers.object', {
#             'object': obj
#         })


class PublicFieldsController(http.Controller):
    @http.route('/public_fields', type='json', auth='public')
    def get_public_fields(self):
        public_fields = request.env['public.field'].search([('is_public', '=', True)])
        data = []
        for field in public_fields:
            data.append({
                'name': field.field_id.field_description,
                'value': field.file_content if field.file_content else field.field_id.name,
            })
        return data
