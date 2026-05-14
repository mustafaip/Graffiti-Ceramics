/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

class CustomHomeMenuController {
    constructor() {
        this.overlayId = 'custom_home_menu_overlay_container';
        this.btnSelector = '.o_frontend_to_backend_apps_btn';
        this.init();
    }

    init() {
        // Capture click event at document level to intercept before Bootstrap
        this._onClickCapture = this._onGlobalClick.bind(this);
        document.addEventListener('click', this._onClickCapture, true);

        this._cleanUpButton();
    }

    _cleanUpButton() {
        const btn = document.querySelector(this.btnSelector);
        if (btn) {
            btn.removeAttribute('data-bs-toggle');
        }
    }

    _onGlobalClick(ev) {
        if (!ev.target.closest) return;
        const btn = ev.target.closest(this.btnSelector);
        if (btn) {
            ev.preventDefault();
            ev.stopPropagation();
            ev.stopImmediatePropagation();
            this._openMenu(ev);
        }
    }

    async _openMenu(ev) {
        let overlay = document.getElementById(this.overlayId);

        if (!overlay) {
            await this._createOverlay();
            overlay = document.getElementById(this.overlayId);
        }

        if (overlay) {
            document.body.appendChild(overlay);
            document.body.style.overflow = 'hidden';

            // Close any open dropdowns explicitly
            const dropdowns = document.querySelectorAll('.dropdown-menu.show');
            dropdowns.forEach(d => d.classList.remove('show'));
        }
    }

    async _createOverlay() {
        try {
            // Use load_menus to get the exact same structure as the backend
            const result = await rpc('/web/dataset/call_kw/ir.ui.menu/load_menus', {
                model: 'ir.ui.menu',
                method: 'load_menus',
                args: [false], // debug=false
                kwargs: {}
            });

            // In Odoo 19, root menu IDs are usually under result.root.children
            const rootIds = (result.root && result.root.children) || result.children || [];

            // Map root IDs to menu objects
            const apps = rootIds.map(id => {
                const menu = result[id];
                if (!menu) return null;

                let actionStr = menu.action;
                if (!actionStr && menu.action_model && menu.action_id) {
                    actionStr = `${menu.action_model},${menu.action_id}`;
                }

                return {
                    id: menu.id,
                    name: menu.name,
                    iconUrl: `/web/image/ir.ui.menu/${menu.id}/web_icon_data`,
                    action: actionStr,
                    xmlid: menu.xmlid
                };
            }).filter(Boolean);

            const appCardsHtml = apps.map(app => {
                const iconHtml = `<img src="${app.iconUrl}" alt="${app.name}"/>`;

                let href = '#';
                if (app.action && app.action !== 'false') {
                    const parts = app.action.split(',');
                    if (parts.length === 2) {
                        href = `/odoo/action-${parts[1]}`;
                    }
                } else {
                    href = `/web#menu_id=${app.id}`;
                }

                return `
                    <a href="${href}" 
                       class="custom_home_menu_app_card">
                      <div class="custom_home_menu_app_icon">
                        ${iconHtml}
                      </div>
                      <div class="custom_home_menu_app_name">${app.name}</div>
                    </a>
                `;
            }).join('');

            const overlayHtml = `
                <div class="custom_home_menu_overlay">
                  <div class="custom_home_menu_container">
                    <div class="custom_home_menu_grid">
                      ${appCardsHtml}
                    </div>
                  </div>
                </div>
            `;

            const overlayContainer = document.createElement('div');
            overlayContainer.id = this.overlayId;
            overlayContainer.innerHTML = overlayHtml;
            document.body.appendChild(overlayContainer);

            const overlay = overlayContainer.querySelector('.custom_home_menu_overlay');
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this._closeMenu();
                }
            });

        } catch (error) {
            console.error('[WebsiteCustomHomeMenu] Error creating overlay:', error);
        }
    }

    _closeMenu() {
        const overlayContainer = document.getElementById(this.overlayId);
        if (overlayContainer) {
            overlayContainer.remove();
            document.body.style.overflow = '';
        }
    }
}

new CustomHomeMenuController();
