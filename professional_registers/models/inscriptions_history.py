# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json
from unidecode import unidecode

from lxml import etree
import passlib.context

from odoo.exceptions import ValidationError
from odoo.tools import profile

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'plaintext'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['plaintext'],
)

class ProfessionalInscriptionHistory(models.Model):
    _name = 'professional_registers.inscription_history'
    _description = 'Historial de la inscripción del profesional'


    inscription_id = fields.Many2one('professional_registers.inscriptions', string='Solicitud', required=True, ondelete='cascade')
    inscription_help_id = fields.Many2one('professional_registers.inscriptions_help', string='Detalles' )
    state_id = fields.Many2one('security.state_configuration', string='Estado', required=True)
    date = fields.Datetime(string='Fecha del Cambio', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user, required=True)
    observation = fields.Text('Observación')



