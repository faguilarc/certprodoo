odoo.define('ai_chat.ai_chat_simple', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var AiChatSimple = AbstractAction.extend({
        template: null,

        events: {
            'click .o_ai_send': '_onSendClick',
            'keypress .o_ai_input': '_onKeyPress',
            'click .o_new_chat': '_onNewChat',
            'click .o_chat_list_item': '_onChatSelect',
            'click .o_delete_chat': '_onDeleteChat',
            'change .o_provider_select': '_onProviderChange',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.chatId = null;
            this.chats = [];
            this.providers = [];
            this.selectedProviderId = null;
            this.userId = this.getSession().uid;
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Cargar proveedores disponibles
                return rpc.query({
                    route: '/ai_chat/get_providers',
                    params: {},
                }).then(function (providers) {
                    self.providers = providers;
                    console.log("✅ Proveedores cargados:", providers.length);

                    // Seleccionar el primer proveedor por defecto
                    if (providers.length > 0) {
                        self.selectedProviderId = providers[0].id;
                    }
                });
            }).then(function () {
                // Cargar lista de chats del usuario
                return rpc.query({
                    model: 'ai.chat',
                    method: 'search_read',
                    domain: [['user_id', '=', self.userId]],
                    fields: ['name', 'create_date', 'message_ids', 'provider_id'],
                    order: 'create_date DESC',
                    limit: 50,
                }).then(function (chats) {
                    self.chats = chats;
                    console.log("✅ Chats cargados:", chats.length);
                });
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderUI();

                // Si hay chats, cargar el más reciente
                if (self.chats.length > 0) {
                    self._loadChat(self.chats[0].id);
                } else {
                    self._createNewChat();
                }
            });
        },

        // ─────────────────────────────────────────────
        // Renderizado de la interfaz
        // ─────────────────────────────────────────────
        _renderUI: function () {
            var self = this;

            // Generar opciones del selector de proveedores
            var providerOptions = this.providers.map(function (p) {
                var selected = p.id === self.selectedProviderId ? 'selected' : '';
                return `<option value="${p.id}" ${selected}>${_.escape(p.name)} (${_.escape(p.model)})</option>`;
            }).join('');

            // Generar HTML de la lista de chats
            var chatListHtml = this.chats.map(function (chat) {
                var isActive = chat.id === self.chatId ? 'o_chat_active' : '';
                var date = new Date(chat.create_date).toLocaleDateString('es-ES');
                var providerName = chat.provider_id ? chat.provider_id[1] : 'Sin proveedor';
                return `
                    <div class="o_chat_list_item ${isActive}" data-chat-id="${chat.id}">
                        <div class="o_chat_item_name">
                            <span class="o_icon o_icon_comments"></span>${_.escape(chat.name)}
                        </div>
                        <div class="o_chat_item_provider text-muted small">
                            <i class="fa fa-robot"/> ${_.escape(providerName)}
                        </div>
                        <div class="o_chat_item_date">${date}</div>
                        <button class="o_delete_chat" title="Eliminar">
                            <span class="o_icon o_icon_trash"></span>
                        </button>
                    </div>
                `;
            }).join('');

            // HTML principal
            var html = `
                <div class="o_ai_chat_wrapper">
                    <!-- SIDEBAR IZQUIERDO -->
                    <div class="o_chat_sidebar">
                        <div class="o_chat_sidebar_header">
                            <h5><span class="o_icon o_icon_history"></span>Chats</h5>
                            <button class="o_new_chat btn btn-sm btn-primary" title="Nuevo Chat">
                                <span class="o_icon o_icon_plus"></span>
                            </button>
                        </div>
                        
                        <div class="o_chat_list">
                            ${chatListHtml || '<div class="o_text_muted o_text_center o_mt_5">Sin chats</div>'}
                        </div>
                        
                        <div class="o_chat_sidebar_footer">
                            <span class="o_icon o_icon_robot"></span>AI Chat v1.0
                        </div>
                    </div>
                    
                    <!-- ÁREA PRINCIPAL -->
                    <div class="o_chat_main">
                        <div class="o_chat_header">
                            <div class="d-flex align-items-center">
                                <h4 class="o_mb_0"><span class="o_icon o_icon_robot"></span>AI Chat Assistant</h4>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <!-- SELECTOR DE PROVEEDOR/MODELO -->
                                <select class="o_provider_select form-control form-control-sm" style="width: 250px;">
                                    ${providerOptions}
                                </select>
                                <span class="o_small o_text_muted" id="o_current_chat_info"></span>
                            </div>
                        </div>
                        
                        <div class="o_ai_messages">
                            <div class="o_text_muted o_text_center o_mt_5">
                                <div style="font-size: 48px; margin-bottom: 10px;">💬</div>
                                <div>¡Hola! Escribe tu primer mensaje 👇</div>
                            </div>
                        </div>
                        
                        <div class="o_chat_input_area">
                            <input type="text" class="o_ai_input" placeholder="Escribe aquí..."/>
                            <button class="o_ai_send">
                                <span class="o_icon o_icon_send"></span>
                            </button>
                        </div>
                    </div>
                </div>
            `;

            this.$el.html(html);

            // Focus en el input
            setTimeout(function () {
                self.$('.o_ai_input').focus();
            }, 100);
        },

        // ─────────────────────────────────────────────
        // Selector de Proveedor
        // ─────────────────────────────────────────────
        _onProviderChange: function (e) {
            var newProviderId = parseInt($(e.currentTarget).val());
            this.selectedProviderId = newProviderId;
            console.log("🔄 Proveedor cambiado a:", newProviderId);

            // Si hay un chat activo, actualizar su proveedor
            if (this.chatId) {
                var self = this;
                rpc.query({
                    model: 'ai.chat',
                    method: 'write',
                    args: [this.chatId, {
                        'provider_id': newProviderId,
                    }],
                }).then(function () {
                    console.log("✅ Proveedor actualizado en el chat");
                    self._refreshChatList();
                });
            }
        },

        // ─────────────────────────────────────────────
        // Actualizar lista de chats en el sidebar
        // ─────────────────────────────────────────────
        _refreshChatList: function () {
            var self = this;

            // Guarda los mensajes antes de actualizar
            var $messagesBackup = this.$('.o_ai_messages').html();

            return rpc.query({
                model: 'ai.chat',
                method: 'search_read',
                domain: [['user_id', '=', this.userId]],
                fields: ['name', 'create_date', 'provider_id'],
                order: 'create_date DESC',
                limit: 50,
            }).then(function (chats) {
                self.chats = chats;
                self._updateChatListSidebar();

                // Restaura los mensajes
                if ($messagesBackup) {
                    self.$('.o_ai_messages').html($messagesBackup);
                    self.$('.o_ai_messages').scrollTop(self.$('.o_ai_messages')[0].scrollHeight);
                }
            });
        },

        _updateChatListSidebar: function () {
            var self = this;
            var chatListHtml = this.chats.map(function (chat) {
                var isActive = chat.id === self.chatId ? 'o_chat_active' : '';
                var date = new Date(chat.create_date).toLocaleDateString('es-ES');
                var providerName = chat.provider_id ? chat.provider_id[1] : 'Sin proveedor';
                return `
                    <div class="o_chat_list_item ${isActive}" data-chat-id="${chat.id}">
                        <div class="o_chat_item_name">
                            <span class="o_icon o_icon_comments"></span>${_.escape(chat.name)}
                        </div>
                        <div class="o_chat_item_provider text-muted small">
                            <i class="fa fa-robot"/> ${_.escape(providerName)}
                        </div>
                        <div class="o_chat_item_date">${date}</div>
                        <button class="o_delete_chat" title="Eliminar">
                            <span class="o_icon o_icon_trash"></span>
                        </button>
                    </div>
                `;
            }).join('');

            this.$('.o_chat_list').html(chatListHtml || '<div class="o_text_muted o_text_center o_mt_5">Sin chats</div>');

            // Re-bind events
            this.$('.o_chat_list_item').on('click', function (e) {
                if (!$(e.target).closest('.o_delete_chat').length) {
                    var chatId = parseInt($(this).data('chat-id'));
                    if (chatId && chatId !== self.chatId) {
                        self._loadChat(chatId);
                    }
                }
            });

            this.$('.o_delete_chat').on('click', function (e) {
                e.stopPropagation();
                var $item = $(this).closest('.o_chat_list_item');
                var chatId = parseInt($item.data('chat-id'));
                if (chatId) {
                    self._onDeleteChatItem($item, chatId);
                }
            });
        },


        // ─────────────────────────────────────────────
        // Crear nuevo chat
        // ─────────────────────────────────────────────
        _createNewChat: function () {
            var self = this;
            return rpc.query({
                model: 'ai.chat',
                method: 'create',
                args: [{
                    'provider_id': this.selectedProviderId,
                }],
            }).then(function (chatId) {
                self.chatId = chatId;
                self.$('.o_ai_messages').html(`
                    <div class="o_text_muted o_text_center o_mt_5">
                        <div style="font-size: 48px; margin-bottom: 10px;">💬</div>
                        <div>¡Nuevo chat! Escribe tu mensaje 👇</div>
                    </div>
                `);
                self._updateChatInfo();
                self._refreshChatList();
                console.log("✅ Nuevo chat creado:", chatId);
            });
        },


        _onNewChat: function (e) {
            e.stopPropagation();
            this._createNewChat();
        },

        // ─────────────────────────────────────────────
        // Cargar chat existente
        // ─────────────────────────────────────────────
        _loadChat: function (chatId) {
            var self = this;
            this.chatId = chatId;

            return rpc.query({
                model: 'ai.chat',
                method: 'read',
                args: [chatId, ['message_ids', 'provider_id']],
            }).then(function (result) {
                var chat = result[0];

                // Actualizar selector de proveedor
                if (chat.provider_id) {
                    self.selectedProviderId = chat.provider_id[0];
                    self.$('.o_provider_select').val(self.selectedProviderId);
                }

                var $messages = self.$('.o_ai_messages');
                $messages.empty();

                if (!chat.message_ids || chat.message_ids.length === 0) {
                    $messages.html(`
                        <div class="o_text_muted o_text_center o_mt_5">
                            <div style="font-size: 48px; margin-bottom: 10px;">💬</div>
                            <div>Chat vacío. Escribe el primer mensaje 👇</div>
                        </div>
                    `);
                } else {
                    // Cargar mensajes del chat
                    return rpc.query({
                        model: 'ai.chat.message',
                        method: 'search_read',
                        domain: [['chat_id', '=', chatId]],
                        fields: ['role', 'content', 'create_date'],
                        order: 'create_date ASC',
                    }).then(function (messages) {
                        messages.forEach(function (msg) {
                            var role = msg.role === 'user' ? 'user' : 'ai';
                            var text = msg.content
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br>');
                            $messages.append(self._renderMessage(role, text, false, true));
                        });
                        $messages.scrollTop($messages[0].scrollHeight);
                        self._updateChatInfo();
                    });
                }
                self._updateChatInfo();
            });
        },

        _onChatSelect: function (e) {
            var $item = $(e.currentTarget);
            var chatId = parseInt($item.data('chat-id'));
            if (chatId && chatId !== this.chatId) {
                this._loadChat(chatId);
                this._refreshChatList();
            }
        },

        // ─────────────────────────────────────────────
        // Eliminar chat
        // ─────────────────────────────────────────────

        _onDeleteChat: function (e) {
            e.stopPropagation();
            var $item = $(e.currentTarget).closest('.o_chat_list_item');
            var chatId = parseInt($item.data('chat-id'));
            if (chatId) {
                this._onDeleteChatItem($item, chatId);
            }
        },

        _onDeleteChatItem: function ($item, chatId) {
            var self = this;

            if (!confirm('¿Estás seguro de eliminar este chat?')) {
                return;
            }

            rpc.query({
                model: 'ai.chat',
                method: 'unlink',
                args: [[chatId]],
            }).then(function () {
                console.log("✅ Chat eliminado:", chatId);
                if (chatId === self.chatId) {
                    self._createNewChat();
                }
                self._refreshChatList();
            }).catch(function (err) {
                console.error("❌ Error eliminando chat:", err);
                alert('Error al eliminar el chat');
            });
        },
        // ─────────────────────────────────────────────
        // Enviar mensaje
        // ─────────────────────────────────────────────
        _onKeyPress: function (ev) {
            if (ev.which === 13) {
                ev.preventDefault();
                this._onSendClick();
            }
        },

        _onSendClick: function () {
            var self = this;
            var $input = this.$('.o_ai_input');
            var $messages = this.$('.o_ai_messages');
            var message = $input.val().trim();

            if (!message || !this.chatId) {
                return;
            }

            $input.val('');
            $messages.append(this._renderMessage('user', message));
            $messages.scrollTop($messages[0].scrollHeight);

            var $thinking = $('<div class="o_msg o_msg_ai"><strong>IA:</strong> <i class="o_text_muted">escribiendo...</i></div>');
            $messages.append($thinking);
            $messages.scrollTop($messages[0].scrollHeight);

            rpc.query({
                route: '/ai_chat/send_message',
                params: {
                    chat_id: this.chatId,
                    message_content: message,
                },
            }).then(function (result) {
                $thinking.remove();
                if (result.error) {
                    $messages.append(self._renderMessage('ai', 'Error: ' + result.error, true));
                } else {
                    var response = result.response || result.status || '(sin respuesta)';
                    response = response
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br>');
                    $messages.append(self._renderMessage('ai', response));

                    // Mostrar qué modelo se usó
                    if (result.provider_name) {
                        var modelInfo = result.model ? ` (${result.model})` : '';
                        console.log(`✅ Respuesta de: ${result.provider_name}${modelInfo}`);
                    }
                }
                $messages.scrollTop($messages[0].scrollHeight);
                self._refreshChatList();
            }).catch(function (err) {
                $thinking.remove();
                $messages.append(self._renderMessage('ai', '❌ Error de conexión', true));
                console.error("RPC error:", err);
            });
        },

        // ─────────────────────────────────────────────
        // Helpers
        // ─────────────────────────────────────────────

        _renderMessage: function (role, text, isError, allowHtml) {
            var safeText = allowHtml ? text : _.escape(text).replace(/\n/g, '<br>');
            var classes = 'o_msg ' +
                (role === 'user' ? 'o_msg_user' : (isError ? 'o_msg_error' : 'o_msg_ai'));
            var label = role === 'user' ? 'Tú' : 'IA';
            return `<div class="${classes}"><strong>${label}:</strong> ${safeText}</div>`;
        },

        _updateChatInfo: function () {
            var chat = this.chats.find(function (c) {
                return c.id === this.chatId;
            }.bind(this));
            if (chat) {
                this.$('#o_current_chat_info').text(_.escape(chat.name));
            } else {
                this.$('#o_current_chat_info').text('');
            }
        },

        _preserveMessages: function () {
            // Guarda el contenido actual de los mensajes
            this.$messagesBackup = this.$('.o_ai_messages').html();
        },

        _restoreMessages: function () {
            // Restaura los mensajes si existen
            if (this.$messagesBackup) {
                this.$('.o_ai_messages').html(this.$messagesBackup);
                this.$('.o_ai_messages').scrollTop(this.$('.o_ai_messages')[0].scrollHeight);
            }
        },
    });

    core.action_registry.add('ai_chat_wizzard', AiChatSimple);

    return AiChatSimple;
});