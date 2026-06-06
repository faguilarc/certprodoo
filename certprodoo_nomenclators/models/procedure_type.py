# -*- coding: utf-8 -*-
"""
ProcedureType — Nomenclador de Tipos de Trámite.

En O14 era nomenclators.procedure_types.
Mejoras O17:
- Fix SQL constraint rota: procedure_comodel → comodel_name
- Suspension history como One2many
- comodel_name renombrado a model_ref para mayor claridad
"""

from odoo import models, fields, api, _


class ProcedureType(models.Model):
    """Tipo de trámite del sistema de registro profesional."""
    _name = "certprodoo.procedure.type"
    _description = "Tipo de Trámite"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    model_ref = fields.Char(
        string="Identificador de Modelo",
        tracking=True,
        help="Nombre técnico del modelo asociado a este tipo de trámite "
             "(ej. certprodoo.inscription, certprodoo.claim).",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
        tracking=True,
    )

    # ─── Relaciones ────────────────────────────────────────────

    document_ids = fields.One2many(
        "certprodoo.document.required",
        "procedure_type_id",
        string="Documentos Requeridos",
    )
    document_count = fields.Integer(
        string="Documentos",
        compute="_compute_document_count",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "Ya existe un tipo de trámite con ese nombre en esta compañía!",
        ),
        (
            "model_ref_uniq",
            "unique(model_ref, company_id)",
            "Ya existe un tipo de trámite con ese identificador en esta compañía!",
        ),
    ]

    # ─── Computes ──────────────────────────────────────────────

    @api.depends("document_ids")
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    # ─── Métodos ──────────────────────────────────────────────

    def action_view_documents(self):
        """Abre la vista de documentos requeridos para este trámite."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documentos para %s") % self.name,
            "res_model": "certprodoo.document.required",
            "view_mode": "tree,form",
            "domain": [("procedure_type_id", "=", self.id)],
        }
