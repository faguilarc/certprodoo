# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from lxml import etree
import json
from datetime import datetime

class PermitsRole(models.Model):
    _name = "security.permits_roles"
    _description = "Permisos por Roles"
    _rec_name = "rol"

    def _get_domain_rol(self):
        arra_ids = []
        user_id = self.env.user
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user_id.id))])
        )

        if company_access:
            roles = self.env["security.roles"].search(
                [("company", "in", company_access.company_ids.ids)]
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

    company = fields.Many2one(
        "res.company",
        string="Compañía",
    )

    def _get_domain_options(self):
        arra_ids = []
        user_id = self.env.user
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user_id.id))])
        )

        if company_access:
            options = self.env["security.options"].search(
                [("company", "in", company_access.company_ids.ids)]
            )
            for r in options:
                arra_ids.append(r.id)
        return [('id', 'in', arra_ids)]
    options = fields.Many2one(
        "security.options", "Opciones",
        required=True,
        domain=_get_domain_options,
    )

    perm_show = fields.Selection(
        [("propias", "Propias"), ("todas", "Todas")], "Visualizar", default="propias"
    )

    field_write = fields.Boolean("Permisos de Escritura", default=False)

    is_default = fields.Boolean(string="Por defecto", default=False)

    user = fields.Many2one("res.users", string="Usuario", required=True)

    _sql_constraints = [
        (
            "rol_opt_uniq",
            "unique (rol, options)",
            "El rol y la opción no se pueden repetir!",
        )
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(PermitsRole, self).fields_get(fields, attributes=attributes)
        mfields = ["create_uid", "create_date", "write_uid", "write_date"]
        for f in mfields:
            res[f]["searchable"] = False
            res[f]["sortable"] = False
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(PermitsRole, self).fields_view_get(
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
        model_rol = self.env["ir.model"].search(
            [("model", "=", "security.permits_roles")]
        )

        if not self.env["res.users"].has_group("base.group_erp_manager"):

            if not self.env["res.users"].has_group("security.permits_access"):
                raise exceptions.ValidationError(
                    "Usted no tiene permisos para visualizar permisos por roles!"
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
                .search([("model", "=", "security.permits_roles")])
            )

            options = (
                self.env["security.permits_option"]
                .sudo()
                .search([("user", "=", int(user.id)), ("options", "=", int(option.id))])
            )

            company_access = (
                self.env["res.users"].sudo().search([("id", "=", int(user.id))])
            )

            option_roles = False
            if company_access.rol:
                option_rol = (
                    self.env["security.permits_roles"]
                    .sudo()
                    .search(
                        # [('rol', 'in', roles.ids)])
                        [("rol", "in", company_access.rol.ids)]
                    )
                )
                for opr in option_rol:
                    if company_access.rol.id == opr.rol.id and int(
                        opr.options.id
                    ) == int(option.id):
                        option_roles = opr

                aux = [
                    "|",
                    ("company", "in", company_access.company_ids.ids),
                    ("id", "in", option_rol.ids),
                ]
                for a in aux:
                    domain.append(a)
            else:
                aux = [("company", "in", company_access.company_ids.ids)]
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

        res = super(PermitsRole, self).search_read(domain, fields, offset, limit, order)
        return res

    @api.model
    def create(self, vals_list):

        user_id = self.env.user
        user_login = self.env["res.users"].search([("id", "=", int(user_id))])
        vals_list["user"] = self.env.uid
        if user_login:
            vals_list["company"] = user_login.company_id.id

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.permits_roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Creación de permisos por roles satisfactoria'
        })

        return super(PermitsRole, self).create(vals_list)

    def write(self, vals):

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.permits_roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': 'Edición de permisos por roles satisfactoria'
        })

        return super(PermitsRole, self).write(vals)

    def unlink(self):
        model_conciliation = self.env['ir.model'].search([('model', '=', 'security.permits_roles')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de permisos por roles satisfactoria.'

        self.env['security.traces'].create({
            'register_time': datetime.now(),
            'user': user.name,
            'model': model_conciliation.id,
            'description': msg
        })
        return super(PermitsRole, self).unlink()