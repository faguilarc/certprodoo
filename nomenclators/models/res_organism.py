from odoo import fields, models, api
import re
from lxml import etree
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date

class Organism(models.Model):
    _name = "res.organism"
    _description = "Organismo"
    _order = "code"
    _rec_name = 'siglas'

    name = fields.Char("Organismo")
    code = fields.Char("Código")
    siglas = fields.Char("Siglas")
    active = fields.Boolean("Activo", default=True)

    _sql_constraints = [
        ("unique0", "unique(name)", "El nombre del organismo no se puede repetir"),
        ("unique1", "unique(code)", "el código del organismo no se puede repetir"),
    ]

    @api.constrains("code")
    def _compute_validations(self):
        ciRegexp = "^([0-9]){1,3}$"
        for part in self:
            text = ""
            if part.code:
                if not re.match(ciRegexp, self.code):
                    err = "El campo Código de los organismo solo acepta número de 3 dígitos. \n"
                    text = text + " " + err
                elif len(part.code) > 3:
                    err = "El campo Código de los organismo solo tienen 3 dígitos. \n"
                    text = text + " " + err
                if text.__len__() > 0:
                    raise ValidationError(text)

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Organism, self).fields_get(fields, attributes=attributes)
        mfields = ["create_uid", "create_date", "write_uid", "write_date"]
        for f in mfields:
            res[f]["searchable"] = False
            res[f]["sortable"] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Organism, self).fields_view_get(view_id=view_id,
                                                   view_type=view_type,
                                                   toolbar=toolbar,
                                                   submenu=submenu)
        doc = etree.XML(res['arch'])

        if not self.env['res.users'].has_group('security.group_professional_superadmin') and not self.env[
            'res.users'].has_group('security.group_professional_managment') and not self.env['res.users'].has_group(
            'security.group_professional_editor_managment'):
            doc.set('create', '0')
            doc.set('edit', '0')
            doc.set('delete', '0')

        res['arch'] = etree.tostring(doc)

        return res

    @api.model
    def create(self, vals_list):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'res.organism')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de organismo satisfactoria.'
        })
        return super(Organism, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'res.organism')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de organismo satisfactoria.'
        })
        return super(Organism, self).write(vals)

    def unlink(self):
        try:
            count = 0
            for rec in self:
                work_history = self.env['professional_registers.work_history'].search(
                    [('city', '=', int(rec.id))])
                if work_history:
                    count = count + 1
            if count != 0:
                msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
                if count > 1:
                    msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'

                raise ValidationError(msg)

            # Add traces
            model = self.env['ir.model'].search([('model', '=', 'res.organism')])
            user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': 'Eliminación de organismo satisfactoria.'
            })

            return super(Organism, self).unlink()
        except Exception:
            raise ValidationError(msg)
