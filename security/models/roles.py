# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class Roles(models.Model):
    _name = "security.roles"
    _description = "Roles de empleados"
    _rec_name = "name"

    name = fields.Char(string="Rol")
    description = fields.Text(string="Descripción")

    user = fields.Many2one("res.users", string="Usuario", required=True)

    company = fields.Many2one(
        "res.company",
        string="Compañía",
    )

    is_default = fields.Boolean(string="Por Defecto", default=False)

    _sql_constraints = [("name_uniq", "unique (name)", "El rol debe ser único!")]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Roles, self).fields_get(fields, attributes=attributes)
        mfields = ["create_uid", "create_date", "write_uid", "write_date"]
        for f in mfields:
            res[f]["searchable"] = False
            res[f]["sortable"] = False
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(Roles, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        doc = etree.XML(res["arch"])

        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )
        rol = self.env["security.roles"].search([("name", "=", "Administrador")])
        roles = self.env["security.roles"].search(
            [
                "|",
                ("company", "in", company_access.company_ids.ids),
                ("id", "=", int(rol.id)),
            ]
        )

        permits = self.env["security.permits_option"].search(
            [("user", "=", int(user.id))]
        )
        permits_roles = self.env["security.permits_roles"].search(
            [("rol", "in", roles.ids)]
        )
        model_rol = self.env["ir.model"].search([("model", "=", "security.roles")])

        if not self.env["res.users"].has_group("base.group_erp_manager"):

            if not self.env["res.users"].has_group("security.generales_access"):
                raise exceptions.ValidationError(
                    "Usted no tiene permisos para visualizar roles!"
                )

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
                .search([("model", "=", "security.roles")])
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
            #     ['|', ('company', 'in', company_access.company_ids.ids), ('id', '=', int(rol.id))])

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

            aux = [
                # "|",
                ("company", "in", company_access.company_ids.ids),
                # ("id", "=", int(rol.id)),
            ]
            for a in aux:
                domain.append(a)

            if options:
                if options.perm_show == "propias":
                    aux = [("user", "=", user.id)]
                    for a in aux:
                        domain.append(a)
            elif option_roles:
                if option_roles.perm_show == "propias":
                    aux = [("user", "=", user.id)]
                    for a in aux:
                        domain.append(a)

        res = super(Roles, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, values):
        user_id = self.env.user

        user_login = self.env["res.users"].search([("id", "=", int(user_id))])
        if user_login:
            values["company"] = user_login.company_id.id

        values["user"] = self.env.uid

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Creación de roles satisfactoria'
        })


        result = super(Roles, self).create(values)
        return result

    def write(self, vals):
        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        user_name = 'System'
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name if user else user_name,
            'model': model_conciliation.id,
            'description': 'Edición de roles satisfactoria'
        })

        return super(Roles, self).write(vals)

    def unlink(self):
        cantidad_registros = 0
        for rec in self:
            cantidad_registros = cantidad_registros + 1
            if rec.is_default:
                raise exceptions.ValidationError(
                    "No se puede eliminar un rol por defecto del sistema"
                )

        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de rol satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de roles satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': msg
        })
        res = super(Roles, self).unlink()

        return res
