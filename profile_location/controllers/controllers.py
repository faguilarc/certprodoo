# -*- coding: utf-8 -*-
# from odoo import http


# class ProfileLocation(http.Controller):
#     @http.route('/profile_location/profile_location/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/profile_location/profile_location/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('profile_location.listing', {
#             'root': '/profile_location/profile_location',
#             'objects': http.request.env['profile_location.profile_location'].search([]),
#         })

#     @http.route('/profile_location/profile_location/objects/<model("profile_location.profile_location"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('profile_location.object', {
#             'object': obj
#         })
