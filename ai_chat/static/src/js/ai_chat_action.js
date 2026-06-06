odoo.define('ai_chat.ai_chat_action', function (require) {
    "use strict";

    const core = require('web.core');
    const AiChatComponent = require('ai_chat.ai_chat_component');
    const AbstractAction = require('web.AbstractAction');

    // Wrapper para integrar el componente Owl con el sistema de acciones de Odoo 14
    const AiChatAction = AbstractAction.extend({
        template: 'ai_chat.AiChatComponent',  // Usará el template Owl

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.owlComponent = null;
        },

        async start() {
            await this._super.apply(this, arguments);

            // Inicializar el componente Owl dentro del elemento de la acción
            const { Component, env } = owl;

            // Crear entorno Owl compatible con Odoo 14
            const owlEnv = {
                ...env,
                qweb: core.qweb,
                rpc: require('web.rpc'),
            };

            // Montar el componente Owl
            this.owlComponent = new AiChatComponent(null, { env: owlEnv });
            await this.owlComponent.mount(this.$el[0]);

            return this.owlComponent;
        },

        willDestroy() {
            if (this.owlComponent) {
                this.owlComponent.destroy();
            }
            this._super.apply(this, arguments);
        },
    });

    // Registrar la acción con el tag que coincide con tu XML
    core.action_registry.add('ai_chat_wizzard', AiChatAction);

    return AiChatAction;
});