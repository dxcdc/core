/*
 *  Document   : template.js
 *  Author     : pixelcave
 *  Description: UI Framework custom functionality
 *
 */

// Import global dependencies
import './../bootstrap';

// Import required modules
import Tools from './tools';
import Helpers from './helpers';

// Template
export default class Template {
    /*
     * Auto called when creating a new instance
     *
     */
    constructor() {
        this._uiInit();
    }

    /*
     * Init all vital functionality
     *
     */
    _uiInit() {
        // Layout variables
        this._lHtml                 = jQuery('html');
        this._lBody                 = jQuery('body');
        this._lPage                 = jQuery('#page-container');
        this._lSidebar              = jQuery('#sidebar');
        this._lMain                 = jQuery('#main-container');
        this._lFooter               = jQuery('#page-footer');

        // Helper variables
        this._lSidebarScroll        = false;
        this._windowW               = Tools.getWidth();

        // Base UI Init
        this._uiHandleSidebar('init');
        this._uiHandleNav();

        // API Init
        this._uiApiLayout();

        // Core Helpers Init
        this.helpers([
            'core-bootstrap-tooltip',
            'core-bootstrap-popover',
            'core-bootstrap-tabs',
            'core-toggle-class',
            'core-scroll-to',
            'core-year-copy',
            'core-appear'
        ]);
    }

    /*
     * Handles sidebar scrolling functionality/styles
     *
     */
    _uiHandleSidebar(mode) {
        let self = this;

        if (mode === 'init') {
            // Add 'side-trans-enabled' class to #page-container (enables sidebar and side overlay transition on open/close)
            // Fixes IE10, IE11 and Edge bug in which animation was executed on each page load - really annoying!
            self._lPage.addClass('side-trans-enabled');

            // Init custom scrolling
            self._uiHandleSidebar();
        } else {
            // If .side-scroll is added to #page-container enable custom scrolling
            if (self._lPage.hasClass('side-scroll')) {
                // Init custom scrolling on Sidebar
                if (!self._lSidebarScroll) {
                    self._lSidebarScroll = new SimpleBar(self._lSidebar[0]);

                    // Enable scrolling lock
                    jQuery('.simplebar-scroll-content', self._lSidebar).scrollLock('enable');
                }
            } else {
                // If custom scrolling exists on Sidebar remove it
                if (self._lSidebarScroll) {
                    // Disable scrolling lock
                    jQuery('.simplebar-scroll-content', self._lSidebar).scrollLock('disable');

                    // Unmount Simplebar
                    self._lSidebarScroll.unMount();
                    self._lSidebarScroll = null;

                    // Remove Simplebar leftovers
                    self._lSidebar.removeAttr('data-simplebar')
                            .html(jQuery('.simplebar-content', self._lSidebar).html());
                }
            }
        }
    }

    /*
     * Main navigation functionality
     *
     */
    _uiHandleNav() {
        let self = this;
        let mainLinks = jQuery('#sidebar a.nav-main-link');

        // Unbind events in case they are already enabled
        mainLinks.off('click.pixelcave.menu');

        // When a main link is clicked
        mainLinks.on('click.pixelcave.menu', (e) => {
            self._lPage.removeClass('sidebar-o-xs');
            mainLinks.removeClass('active');
            jQuery(e.currentTarget).addClass('active');
        });
    }

    /*
     * Layout API
     *
     */
    _uiApiLayout(mode = 'init') {
        let self = this;

        // Get current window width
        self._windowW = Tools.getWidth();

        // API with object literals
        let layoutAPI = {
            init: () => {
                // Unbind event in case it is already enabled
                self._lPage.off('click.pixelcave.layout');

                // Call layout API on button click
                self._lPage.on('click.pixelcave.layout', '[data-toggle="layout"]', (e) => {
                    let el = jQuery(e.currentTarget);

                    self._uiApiLayout(el.data('action'));

                    el.blur();
                });
            },
            sidebar_toggle: () => {
                if (self._windowW > 991) {
                    self._lPage.toggleClass('sidebar-o');
                } else {
                    self._lPage.toggleClass('sidebar-o-xs');
                }
            },
            sidebar_open: () => {
                if (self._windowW > 991) {
                    self._lPage.addClass('sidebar-o');
                } else {
                    self._lPage.addClass('sidebar-o-xs');
                }
            },
            sidebar_close: () => {
                if (self._windowW > 991) {
                    self._lPage.removeClass('sidebar-o');
                } else {
                    self._lPage.removeClass('sidebar-o-xs');
                }
            }
        };

        // Call layout API
        if (layoutAPI[mode]) {
            layoutAPI[mode]();
        }
    }

    /*
     ********************************************************************************************
     *
     * Create aliases for easier/quicker access to vital methods
     *
     *********************************************************************************************
     */

    /*
     * Init base functionality
     *
     */
    init() {
        this._uiInit();
    }

    /*
     * Run Helpers
     *
     */
    helpers(helpers, options = {}) {
        Helpers.run(helpers, options);
    }
}
