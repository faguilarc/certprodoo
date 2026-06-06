from odoo import fields, models, api, exceptions
import re
from datetime import datetime

class ConectionTest(models.Model):
    _name = 'conection.conection'
    _description = 'Conection to DB'

    name = fields.Char('Conexión')
    script_type = fields.Selection([('update_request', 'Actualizar provincias'),
                                    ('sell_tickets', 'Actualizar estado del pago')], default='update_request', string="Script")

    date_inscription = fields.Date('Fecha de inscripción')

    def extraer_datos(self):
        if self.script_type == 'update_request':
            self.update_request()
        else:
             self.update_tickets()

    def update_request(self):
        request = self.env['professional_registers.professional_request'].search([('request_number', 'in',
                                                                                   ('8', '11',
                                                                                    '12', '13', '14', '15',
                                                                                    '16', '17', '18', '19',
                                                                                    '23', '27', '35'))])
        for r in request:
            country_state = False
            if r.request_number == '3':
                country_state = self.env['res.country.state'].search([('name', '=', 'Holguín')])
            elif r.request_number == '5' or r.request_number == '19':
                country_state = self.env['res.country.state'].search([('name', '=', 'Pinar del Río')])
            elif r.request_number == '8':
                country_state = self.env['res.country.state'].search([('name', '=', 'Camagϋey')])
            elif r.request_number == '23' or r.request_number == '27':
                country_state = self.env['res.country.state'].search([('name', '=', 'Santi Spíritus')])
            else:
                country_state = self.env['res.country.state'].search([('name', '=', 'Ciego de Ávila')])

            r.country_states = country_state.id

    def update_tickets(self):
        date = self.date_inscription
        inscriptions = self.env['professional_registers.inscription'].search([('date', '=', str(date))])
        for insc in inscriptions:
            insc.write({
                'payment_type': 'exonerado'
            })

    @api.model
    def create(self, vals_list):
        str_str = ''
        if vals_list.get('script_type') == 'update_request':
            str_str = 'actualizar provincias'
        else:
            str_str = 'actualizar estados de pago'
        vals_list['name'] = 'Script para ' + str(str_str)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'conection.conection')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de script para : ' + str(str_str)
        })

        return super(ConectionTest, self).create(vals_list)

    def write(self, vals):
        str_str = self.name
        if vals.get('script_type') == 'update_request':
            str_str = 'actualizar provincias'
            vals['name'] = 'Script para ' + str(str_str)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'conection.conection')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de script para : ' + str(str_str)
        })
        return super(ConectionTest, self).write(vals)

