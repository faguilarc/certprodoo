# -*- coding: utf-8 -*-
# from odoo import http


# class Security(http.Controller):
#     @http.route('/security/security/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/security/security/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('security.listing', {
#             'root': '/security/security',
#             'objects': http.request.env['security.security'].search([]),
#         })

#     @http.route('/security/security/objects/<model("security.security"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('security.object', {
#             'object': obj
#         })
