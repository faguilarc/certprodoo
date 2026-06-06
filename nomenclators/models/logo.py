from lxml import etree

from odoo import fields, models, api

class Logo(models.Model):
    _name = 'nomenclators.logo'

    image = fields.Binary(string="Logo")
    name = fields.Char('Nombre del Logo')

    _sql_constraints = [('unique_name', 'unique (name)',
                         'Ya existe un logo registrado con ese nombre')]
