import random
import string

from odoo import fields, models, api, exceptions
from datetime import datetime

class Notificacion(models.Model):
    _name = "notifications.notifications"

    name = fields.Char("Nombre", required=True)
    type = fields.Selection(
        [
            ("1", "Mensaje interno"),
            ("2", "Mensaje de alerta"),
            ("3", "Mensaje de correo"),
        ],
        "Tipo",
        default="2",
        required=True,
    )
    to_create = fields.Boolean("Al crear", default=False)
    to_update = fields.Boolean("Al modificar", default=False)
    to_delete = fields.Boolean("Al eliminar", default=False)
    changest = fields.Boolean("Cambio de estado", default=False)
    notification = fields.Text("Notificación", required=True)
    persons = fields.Many2many("res.users", string="Usuarios")
    models = fields.Many2many(
        "ir.model", string="Modelos"
    )
    model_id = fields.Many2one(
        "ir.model", string="Modelo"
    )
    code = fields.Char("Código", store=True)

    state = fields.Many2one('security.state_configuration', string="Estados")

    _sql_constraints = [
        (
            "unique_prefijo",
            "unique (name)",
            "El nombre de la notificación no debe repetirse.",
        )
    ]

    @api.onchange("type")
    def _onchange_tipo(self):
        if not self.code:
            size = 6
            chars = string.ascii_uppercase + string.digits
            self.code = "".join(random.choice(chars) for x in range(size))

    @api.onchange('model_id')
    def load_states(self):
        states = self.env['security.state_configuration'].search([('model', '=', int(self.model_id))])
        return dict(
            value=dict(
                state=None,
            ),
            domain=dict(
                state=[('id', 'in', states.ids)],
            )
        )


    @api.model
    def create(self, vals):
        res = []
        if vals.get("to_create"):
            res.append("on_create")
        if vals.get("to_update"):
            res.append("on_write")
        if vals.get("to_delete"):
            res.append("on_unlink")
        cod = vals.get("code")
        if not res and not vals.get("changest"):
            raise exceptions.ValidationError("Debe seleccionar al menos un disparador")

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'notifications.notifications')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        user_name = 'system'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name if user else user_name,
            'model': model_conciliation.id,
            'description': 'Creación de notificación satisfactoria'
        })

        return super(Notificacion, self).create(vals)
    
    def write(self, vals):
        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'notifications.notifications')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        user_name = 'system'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name if user else user_name,
            'model': model_conciliation.id,
            'description': 'Edición de notificación satisfactoria'
        })
        return super(Notificacion, self).write(vals)

    def unlink(self):
        cantidad_registros = 0
        for rec in self:
            cantidad_registros = cantidad_registros + 1

        # Add traces
        model_conciliation = self.env['ir.model'].search([('model', '=', 'notifications.notifications')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        user_name = 'system'

        msg = 'Eliminación de notificación satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de notificaciones satisfactoria.'

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name if user else user_name,
            'model': model_conciliation.id,
            'description': msg
        })
        return super(Notificacion, self).unlink()