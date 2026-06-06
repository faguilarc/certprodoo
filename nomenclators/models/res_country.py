from odoo import fields, models, api, exceptions
from datetime import datetime, timedelta, date
from lxml import etree

class ResCountry(models.Model):
    _inherit = 'res.country'
    _description = 'País'

    country_code = fields.Char("Código del país")
    _sql_constraints = [('codigo_uniq', 'unique (country_code)', "Ya existe un país con ese código!")]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(ResCountry, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'code']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResCountry, self).fields_view_get(view_id=view_id,
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
        model = self.env['ir.model'].search([('model', '=', 'res.country')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de país satisfactoria.'
        })
        return super(ResCountry, self).create(vals_list)

    def write(self, vals):
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'res.country')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de país satisfactoria.'
        })
        return super(ResCountry, self).write(vals)

    def unlink(self):
        try:
            count = 0
            for rec in self:
                profesional_request = self.env['professional_registers.professional_request'].search(
                    [('city', '=', int(rec.id))])
                profile = self.env['professional_registers.profile'].search([('city', '=', int(rec.id))])
                if profesional_request or profile:
                    count = count + 1
            if count != 0:
                msg = 'No es posible eliminar el registro seleccionado. Está relacionado con otros elementos del sistema.'
                if count > 1:
                    msg = 'No es posible eliminar los registros seleccionados. Están relacionados con otros elementos del sistema.'

                raise exceptions.ValidationError(msg)

            # Add traces
            model = self.env['ir.model'].search([('model', '=', 'res.country')])
            user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
            self.env['security.traces'].create({
                'register_time': datetime.utcnow(),
                'user': user.name,
                'model': model.id,
                'description': 'Eliminación de país satisfactoria.'
            })

            return super(ResCountry, self).unlink()
        except Exception:
            raise exceptions.ValidationError(msg)