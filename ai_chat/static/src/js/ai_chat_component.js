odoo.define('ai_chat.ai_chat_component', function (require) {
    "use strict";

    // Importar dependencias con require() - compatible con Odoo 14
    const { Component, useState, useRef, onMounted, onPatched } = owl;
    const rpc = require('web.rpc');

    class AiChatComponent extends Component {
        static template = "ai_chat.AiChatComponent";
        
        setup() {
            // Estado reactivo
            this.state = useState({
                chatId: null,
                messages: [],
                inputMessage: "",
                isThinking: false,
            });
            
            // Referencias al DOM
            this.messagesRef = useRef("messagesContainer");
            this.inputRef = useRef("input");
            
            // Auto-scroll cuando se actualizan los mensajes
            onPatched(() => {
                this.scrollToBottom();
            });
            
            // Focus en el input al montar
            onMounted(() => {
                this.initializeChat();
                if (this.inputRef.el) {
                    this.inputRef.el.focus();
                }
            });
        }

        // ─────────────────────────────────────────────
        // Inicialización del chat
        // ─────────────────────────────────────────────
        initializeChat() {
            const self = this;
            return rpc.query({
                model: 'ai.chat',
                method: 'create',
                args: [{}],
            }).then(function (chatId) {
                self.state.chatId = chatId;
                console.log("✅ Chat session created:", chatId);
            }).catch(function (error) {
                console.error("❌ Error creating chat:", error);
                self.addMessage('assistant', 'Error al iniciar la sesión de chat.', true);
            });
        }

        onNewChat() {
            const self = this;
            this.state.messages = [];
            return this.initializeChat().then(function () {
                if (self.inputRef.el) {
                    self.inputRef.el.focus();
                }
            });
        }

        // ─────────────────────────────────────────────
        // Manejo de envío de mensajes
        // ─────────────────────────────────────────────
        onKeyPress(ev) {
            if (ev.key === 'Enter' && !ev.shiftKey) {
                ev.preventDefault();
                this.onSendMessage();
            }
        }

        onSendMessage() {
            const message = this.state.inputMessage.trim();
            if (!message || !this.state.chatId || this.state.isThinking) {
                return;
            }

            // Limpiar input y agregar mensaje del usuario
            this.state.inputMessage = "";
            this.addMessage('user', this.escapeHtml(message));

            // Mostrar indicador de "pensando"
            this.state.isThinking = true;
            this.scrollToBottom();

            const self = this;
            return rpc.query({
                route: '/ai_chat/send_message',
                params: {
                    chat_id: this.state.chatId,
                    message_content: message,
                },
            }).then(function (result) {
                self.state.isThinking = false;
                
                if (result.error) {
                    self.addMessage('assistant', `Error: ${self.escapeHtml(result.error)}`, true);
                } else {
                    const formattedResponse = self.formatResponse(result.response || result.status);
                    self.addMessage('assistant', formattedResponse, false, true);
                }
            }).catch(function (error) {
                self.state.isThinking = false;
                console.error("RPC failed:", error);
                self.addMessage('assistant', 'Error de conexión con el servidor.', true);
            });
        }

        // ─────────────────────────────────────────────
        // Utilidades de mensajes
        // ─────────────────────────────────────────────
        addMessage(role, content, isError = false, allowHtml = false) {
            const message = {
                id: Date.now() + Math.random(),
                role: role,
                content: allowHtml ? content : this.escapeHtml(content),
                isError: isError,
                timestamp: new Date(),
            };
            this.state.messages.push(message);
            this.scrollToBottom();
        }

        escapeHtml(text) {
            if (!text) return '';
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;',
            };
            return text.replace(/[&<>"']/g, function (m) { return map[m]; }).replace(/\n/g, '<br>');
        }

        formatResponse(text) {
            if (!text) return '';
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/`(.*?)`/g, '<code class="bg-light px-1 rounded">$1</code>')
                .replace(/\n/g, '<br>');
        }

        scrollToBottom() {
            const container = this.messagesRef.el;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }

    // Exportar el componente para que pueda ser importado por ai_chat_action.js
    return AiChatComponent;
});