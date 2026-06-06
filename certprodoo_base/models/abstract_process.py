# -*- coding: utf-8 -*-
"""
BaseProcessRequest — Modelo abstracto base para todas las solicitudes.

Reemplaza professional_registers.base_process_request y sirve como
base para: professional_request, claim_request, update_request,
digital_signature_request y cualquier futuro tipo de solicitud.

Migración de Odoo 14 → 17:
- Hereda de mail.thread y mail.activity.mixin para chatter
- Hereda de AuditMixin para trazabilidad automática
- Hereda de StateMixin para máquina de estados configurable
- Hereda de SequenceMixin para secuencias nominadas
- Campos comunes centralizados en un solo lugar
- state y kanban_state declarados aquí para vistas base
- history_ids hacia certprodoo.base.process.history
"""

from odoo import models, fields, api, _

from .audit_mixin import AuditMixin
from .state_mixin import StateMixin
from .sequence_mixin import SequenceMixin


class BaseProcessRequest(models.AbstractModel):
    """Modelo abstracto base para todas las solicitudes del sistema.

    Proporciona:
    - Campos comunes: name, state, request_date, user_id, company_id
    - Historial de cambios de estado (history_ids)
    - Documentos adjuntos (attachment_ids)
    - Observaciones (observation)
    - Prioridad (priority)
    - Responsable asignado (user_on_charge)
    - kanban_state para vistas kanban

    Uso:
        class MiSolicitud(models.Model):
            _name = 'mi.solicitud'
            _inherit = ['certprodoo.base.process']

            # Opcionalmente override del campo state con más estados:
            state = fields.Selection(
                selection_add=[('custom', 'Custom State')],
            )
    """
    _name = "certprodoo.base.process"
    _description = "Base para Procesos de Solicitud"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "certprodoo.audit.mixin",
        "certprodoo.state.mixin",
        "certprodoo.sequence.mixin",
    ]
    _order = "request_date desc, id desc"

    # ─── Campos de Identificación ───────────────────────────────

    name = fields.Char(
        string="Referencia",
        readonly=True,
        default=lambda self: _("New"),
        copy=False,
        tracking=True,
    )

    state = fields.Selection(
        selection='_get_state_selection',
        string="Estado",
        default='_get_default_state',
        tracking=True,
        group_expand='_read_group_state',
        help="Estado actual de la solicitud. Se configura dinámicamente "
             "desde CertProdoo → Configuración → Estados.",
    )

    kanban_state = fields.Selection(
        [('normal', 'En Progreso'),
         ('done', 'Listo para el siguiente paso'),
         ('blocked', 'Bloqueado')],
        string="Estado Kanban",
        default='normal',
        tracking=True,
        help="Estado visual para la vista Kanban:\n"
             "- En Progreso: la solicitud está en curso\n"
             "- Listo para el siguiente paso: listo para avanzar de estado\n"
             "- Bloqueado: hay un impedimento que debe resolverse",
    )

    request_date = fields.Date(
        string="Fecha de Solicitud",
        default=fields.Date.context_today,
        tracking=True,
    )

    # ─── Campos de Responsabilidad ──────────────────────────────

    user_id = fields.Many2one(
        "res.users",
        string="Solicitante",
        default=lambda self: self.env.user,
        tracking=True,
    )

    user_on_charge = fields.Many2one(
        "res.users",
        string="Responsable",
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    # ─── Campos de Contenido ────────────────────────────────────

    observation = fields.Text(
        string="Observación",
    )

    priority = fields.Selection(
        [("0", "Baja"), ("1", "Normal"), ("2", "Alta")],
        string="Prioridad",
        default="1",
        tracking=True,
    )

    color = fields.Integer(
        string="Color",
        default=0,
        help="Color para la vista Kanban",
    )

    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    # ─── Historial de Estados ───────────────────────────────────

    history_ids = fields.One2many(
        "certprodoo.base.process.history",
        compute="_compute_history_ids",
        string="Historial de Estados",
        help="Registro de todos los cambios de estado de la solicitud.",
    )

    def _compute_history_ids(self):
        """Obtiene el historial de cambios de estado para este registro."""
        for record in self:
            histories = self.env["certprodoo.base.process.history"].search(
                [("model_name", "=", record._name), ("res_id", "=", record.id)],
                order="date desc",
            )
            record.history_ids = histories

    # ─── Documentos Adjuntos ────────────────────────────────────

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Documentos Adjuntos",
    )

    attachment_count = fields.Integer(
        string="Cantidad de Documentos",
        compute="_compute_attachment_count",
    )

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    # ─── Agrupación de Estados ──────────────────────────────────

    @api.model
    def _read_group_state(self, states, domain, order):
        """Permite agrupar por state en vistas list/kanban.

        Retorna todos los estados configurados para el modelo
        actual, no solo los que tienen registros.
        """
        model_name = self._get_state_model_name()
        state_configs = self.env["certprodoo.base.state.config"].search(
            [("model_name", "=", model_name)],
            order="priority asc",
        )
        return [s.code for s in state_configs] if state_configs else states

    # ─── Creación ──────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                template_id = self._get_sequence_template_id()
                if template_id:
                    vals["name"] = self._generate_sequence(template_id)
                else:
                    vals["name"] = self.env["ir.sequence"].next_by_code(
                        self._name
                    ) or _("New")
        return super().create(vals_list)

    # ─── Métodos de Acción ──────────────────────────────────────

    def action_toggle_active(self):
        """Alterna el estado activo/inactivo del registro."""
        for record in self:
            record.active = not record.active

    # ─── Métodos a Implementar ──────────────────────────────────

    def _get_sequence_template_id(self):
        """Retorna el ID de la plantilla de secuencia.
        Override en modelos concretos.
        """
        return False
