/** @odoo-module **/
/*
 * Dashboard de Seguridad - CertProdoo (OWL Component for Odoo 17+)
 *
 * Componente OWL que muestra estadísticas del módulo de seguridad.
 * Reemplaza el AbstractAction legacy de O14.
 *
 * Se registra como client action con tag 'certprodoo_security_dashboard'.
 */
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { usePager } from "@web/search/kanban_model";

const actionRegistry = registry.category("actions");

class SecurityDashboard extends Component {
    static template = "certprodoo_security.Dashboard";
    static props = {
        action: Object,
        actionId: { type: Number, optional: true },
        className: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.user = useService("user");

        this.state = {
            total_users: 0,
            active_users: 0,
            users_by_type: {},
            companies: 0,
            roles: 0,
            options: 0,
            permissions: {},
            loading: true,
        };
        this._loadData();
    }

    async _loadData() {
        try {
            const data = await this.orm.call(
                "certprodoo.security.dashboard",
                "get_full_data",
                []
            );
            Object.assign(this.state, data, { loading: false });
            this.render(true);
        } catch (error) {
            console.error("Error loading security dashboard data:", error);
            this.state.loading = false;
            this.render(true);
        }
    }
}

actionRegistry.add("certprodoo_security_dashboard", SecurityDashboard);

export default SecurityDashboard;
