# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class UserInherit(models.Model):
    _inherit = "res.users"




    def _get_domain_rol(self):
        arra_ids = []
        user_id = self.env.user
        access_company = (
            self.env["res.users"].sudo().search([("id", "=", int(user_id.id))])
        )

        if access_company:
            roles = self.env["security.roles"].search(
                [("company", "in", access_company.company_ids.ids)]
            )
            for r in roles:
                arra_ids.append(r.id)

        rol = self.env["security.roles"].search([("name", "=", "Administrador")])
        arra_ids.append(rol.id)
        return [("id", "in", arra_ids)]

    rol = fields.Many2one(
        "security.roles",
        string="Rol",
        domain=_get_domain_rol,
    )

    user_type = fields.Selection([('client', 'Cliente'),
                                  ('client_online', 'Cliente_Online'),
                                  ('system', 'Sistema')], string="Tipo de usuario")

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(UserInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        doc = etree.XML(res["arch"])

        access_company = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )
        rol = self.env["security.roles"].search([("name", "=", "Administrador")])
        roles = self.env["security.roles"].search(
            [
                "|",
                ("company", "in", access_company.company_ids.ids),
                ("id", "=", int(rol.id)),
            ]
        )

        permits = self.env["security.permits_option"].search(
            [("user", "=", int(user.id))]
        )
        permits_roles = self.env["security.permits_roles"].search(
            [("rol", "in", roles.ids)]
        )
        model_rol = self.env["ir.model"].search([("model", "=", "res.users")])

        if not self.env["res.users"].has_group("base.group_erp_manager"):
            # if not self.env["res.users"].has_group("security.generales_access") and not self.env["res.users"].has_group("security.generales_access"):
            #     raise exceptions.ValidationError(
            #         "Usted no tiene permisos para visualizar usuarios!"
            #     )

            if permits:
                is_permits = False
                for p in permits:
                    option = self.env["security.options"].search(
                        [
                            ("id", "=", int(p.options.id)),
                            ("model", "=", int(model_rol.id)),
                        ]
                    )
                    if option:
                        is_permits = True
                        if not p.field_write:
                            doc.set("create", "0")
                            doc.set("edit", "0")
                            doc.set("delete", "0")
                        else:
                            doc.set("create", "1")
                            doc.set("edit", "1")
                            doc.set("delete", "1")
                if not is_permits:
                    doc.set("create", "0")
                    doc.set("edit", "0")
                    doc.set("delete", "0")
            elif permits_roles:
                is_permits = False
                for p in permits_roles:
                    option = self.env["security.options"].search(
                        [
                            ("id", "=", int(p.options.id)),
                            ("model", "=", int(model_rol.id)),
                        ]
                    )
                    if option:
                        if user.rol:
                            if user.rol.id == rol.id:
                                is_permits = True
                                if not p.field_write:
                                    doc.set("create", "0")
                                    doc.set("edit", "0")
                                    doc.set("delete", "0")
                                else:
                                    doc.set("create", "1")
                                    doc.set("edit", "1")
                                    doc.set("delete", "1")
                if not is_permits:
                    doc.set("create", "0")
                    doc.set("edit", "0")
                    doc.set("delete", "0")
            else:
                doc.set("create", "0")
                doc.set("edit", "0")
                doc.set("delete", "0")

        res["arch"] = etree.tostring(doc)

        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not self.env["res.users"].has_group("base.group_erp_manager"):
            user = self.env.user

            option = (
                self.env["security.options"]
                .sudo()
                .search([("model", "=", "res.users")])
            )

            options = (
                self.env["security.permits_option"]
                .sudo()
                .search([("user", "=", int(user.id)), ("options", "=", int(option.id))])
            )

            company_access = (
                self.env["res.users"].sudo().search([("id", "=", int(user.id))])
            )

            # rol = self.env['security.roles'].search([('name', '=', 'Administrador')])
            # roles = self.env['security.permits_roles'].search(
            #     ['|', ('company', 'in', company_access.company_ids.ids), ('rol', '=', int(rol.id))])

            option_roles = False
            if company_access.rol:
                option_rol = (
                    self.env["security.permits_roles"]
                    .sudo()
                    .search(
                        # [('rol', 'in', roles.ids), ('options', '=', int(option.id))])
                        [
                            ("rol", "in", company_access.rol.ids),
                            ("options", "=", int(option.id)),
                        ]
                    )
                )
                for opr in option_rol:
                    if company_access.rol.id == opr.rol.id:
                        option_roles = opr

            aux = [("company_id", "in", company_access.company_ids.ids)]
            for a in aux:
                domain.append(a)

            if options:
                if options.perm_show == "propias":
                    aux = [("id", "=", user.id)]
                    for a in aux:
                        domain.append(a)
            elif option_roles:
                if option_roles.perm_show == "propias":
                    aux = [("id", "=", user.id)]
                    for a in aux:
                        domain.append(a)

        res = super(UserInherit, self).search_read(domain, fields, offset, limit, order)
        return res


    @api.model
    def create(self, vals_list):
        # Add traces
        model_conciliation = self.env['ir.model'].sudo().search([('model', '=', 'res.users')])
        user = self.env['res.users'].sudo().search([('id', '=', int(self.env.uid))])

        self.env['security.traces'].sudo().create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Creación de usuario satisfactoria'
        })

        return super(UserInherit, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model_conciliation = self.env['ir.model'].sudo().search([('model', '=', 'res.users')])
        user = self.env['res.users'].sudo().search([('id', '=', int(self.env.uid))])
        user_name = 'System'
        self.env['security.traces'].sudo().create({
            'register_time': datetime.now(),
            'user': user.name if user else user_name,
            'model': model_conciliation.id,
            'description': 'Edición de usuario satisfactoria'
        })

        return super(UserInherit, self).write(vals)

    def unlink(self):
        cantidad_registros = len(self)

        model_conciliation = self.env['ir.model'].sudo().search([('model', '=', 'res.users')])
        user = self.env['res.users'].sudo().search([('id', '=', int(self.env.uid))])

        msg = 'Eliminación de usuario satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de usuarios satisfactoria.'
        self.env['security.traces'].sudo().create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': msg
        })
        return super(UserInherit, self).unlink()
