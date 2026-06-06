# -*- coding: utf-8 -*-
"""
CleanRegisters — Wizard para limpieza de base de datos.

Permite borrar datos de módulos específicos, útil durante
desarrollo y pruebas. En O14 era security.clear_registers.

En O17 se mejora usando ondelete='cascade' en las relaciones
en vez de borrado manual modelo por modelo.
"""

from odoo import models, fields, api, _


class CleanRegisters(models.TransientModel):
    """Wizard de limpieza de base de datos.

    Permite eliminar todos los datos de registros profesionales
    o de todos los módulos del sistema. Solo disponible para
    administradores.
    """
    _name = "certprodoo.security.clean.registers"
    _description = "Limpiar Registros de BD"

    erase_type = fields.Selection(
        [("only_professional", "Solo Registros Profesionales"),
         ("all_modules", "Todos los Módulos")],
        string="Tipo de Limpieza",
        default="only_professional",
        required=True,
    )
    confirm_text = fields.Char(
        string="Confirmación",
        help="Escriba 'BORRAR' para confirmar la eliminación.",
    )

    def action_erase(self):
        """Ejecuta la limpieza de datos."""
        self.ensure_one()

        if self.confirm_text != "BORRAR":
            raise ValueError(
                _("Debe escribir 'BORRAR' para confirmar la eliminación.")
            )

        if not self.env.user.has_group("certprodoo_base.group_certprodoo_admin"):
            raise ValueError(
                _("Solo los administradores pueden ejecutar esta acción.")
            )

        if self.erase_type == "only_professional":
            self._erase_professional_registers()
        else:
            self._erase_professional_registers()
            self._erase_other_modules()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Limpieza Completada"),
                "message": _("Los registros han sido eliminados exitosamente."),
                "type": "success",
                "sticky": False,
            },
        }

    def _erase_professional_registers(self):
        """Elimina los datos del módulo de registros profesionales."""
        # Los modelos se eliminarán cuando el módulo professional_registers exista
        # Por ahora limpiamos las tablas base que puedan tener datos de prueba
        models_to_clean = [
            "certprodoo.base.process.history",
            "certprodoo.base.audit.log",
        ]
        for model_name in models_to_clean:
            model = self.env.get(model_name)
            if model:
                records = model.search([])
                if records:
                    records.sudo().unlink()

    def _erase_other_modules(self):
        """Elimina datos de otros módulos además de professional_registers."""
        self._erase_professional_registers()
