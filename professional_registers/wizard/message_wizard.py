from odoo import models, fields


class MessageWizard(models.TransientModel):
    _name = 'professional_registers.message_wizard'
    _description = 'Reusable Message Wizard'

    title = fields.Char(string="Title", required=True, default="Confirmation")
    message = fields.Html(string="Message", required=True, default="Are you sure?")
    action_name = fields.Char(string="Action Name", default="Confirm")  # Texto del botón de acción
    no_action = fields.Boolean('Execute action')




    def action_confirm(self):
        # Recupera el nombre del modelo, la función y los argumentos del contexto
        target_model = self.env.context.get('target_model')
        target_function = self.env.context.get('target_function')
        target_function_args = self.env.context.get('target_function_args', {})  # Parámetros opcionales
        no_action = self.env.context.get('no_action')

        if target_model and target_function and not no_action:
            # Obtiene la instancia del modelo deseado
            model_instance = self.env[target_model]

            # Verifica que el modelo tenga la función y que sea ejecutable
            if hasattr(model_instance, target_function):
                func = getattr(model_instance, target_function)
                if callable(func):
                    # Llama a la función del modelo objetivo y pasa los argumentos
                    return func(**target_function_args) if target_function_args else func()  # Pasar los parámetros como kwargs
                else:
                    raise ValueError(f"{target_function} no es una función ejecutable.")
            else:
                raise ValueError(f"El modelo {target_model} no tiene una función llamada {target_function}.")
        else:
            if no_action:
                pass
            else:
                raise ValueError("El nombre del modelo o de la función no fueron especificados.")

    def move_to_tree(self,res_model,name,target,view_mode='tree',context={},domain=[]):
        return {
            'type': 'ir.actions.act_window',
            'res_model': res_model,  # El modelo al que deseas redirigir
            'name': name,  # Título de la ventana
            'view_mode': view_mode,  # Modo de vista: tree (lista)

            'target': target,  # Abre en la misma pestaña
            'context': context,  # Contexto adicional (opcional)
            # 'domain': domain,  # Filtros adicionales (opcional)
        }
    def move_to_form(self,res_model,name,target,res_id, view_mode='form',context={},domain=[]):
        return {
            'type': 'ir.actions.act_window',
            'res_model': res_model,  # El modelo al que deseas redirigir
            'name': name,  # Título de la ventana
            'view_mode': view_mode,  # Modo de vista: tree (lista)
            'res_id': res_id,
            'target': target,  # Abre en la misma pestaña
            'context': context,  # Contexto adicional (opcional)
            # 'domain': domain,  # Filtros adicionales (opcional)
        }

    def move_to_act(self, ref, context={}, domain=[]):
        """
        Redirige a la vista de lista (tree) usando la acción definida en el ir.actions.act_window.
        """
        # Obtener la acción de la vista
        action = self.env.ref(ref).sudo()

        # Actualizar el contexto y el dominio si es necesario
        if context:
            action.context = context
        if domain:
            action.domain = domain

        # Retornar la acción
        return action.read()[0]

# def action_confirm(self):
    #     # Recupera el nombre del modelo y la función del contexto
    #     target_model = self.env.context.get('target_model')
    #     target_function = self.env.context.get('target_function')
    #     no_action = self.env.context.get('no_action')
    #
    #     if target_model and target_function and not no_action:
    #         # Obtiene la instancia del modelo deseado
    #         model_instance = self.env[target_model]
    #
    #         # Verifica que el modelo tenga la función y que sea ejecutable
    #         if hasattr(model_instance, target_function):
    #             func = getattr(model_instance, target_function)
    #             if callable(func):
    #                 func()  # Llama a la función del modelo objetivo
    #             else:
    #                 raise ValueError(f"{target_function} no es una función ejecutable.")
    #         else:
    #             raise ValueError(f"El modelo {target_model} no tiene una función llamada {target_function}.")
    #     else:
    #         if no_action:
    #             pass
    #         else:
    #             raise ValueError("El nombre del modelo o de la función no fueron especificados.")