from datetime import datetime

from odoo import models, fields


class ProfileProfessions(models.Model):
    _name = 'professional_registers.profile_professions'
    _description = 'Profesiones del Perfil'

    professions = fields.Many2one('nomenclators.professions', string="Profesión",)

    others_professions = fields.Many2one('professional_registers.others_professions',
                                         string="Otras profesiones")
    profile = fields.Many2one('professional_registers.profile', string="Perfil",)


