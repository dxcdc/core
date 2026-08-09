/*
 *  Document   : app.js
 *  Author     : pixelcave
 *  Description: Main entry point
 *
 */

// Import global dependencies
import './bootstrap';

// Import required modules
import Tools from './modules/tools';
import Helpers from './modules/helpers';
import Template from './modules/template';

// App extends Template
export default class App extends Template {
    /*
     * Auto called when creating a new instance
     *
     */
    constructor() {
        super();
    }

    /*
     * Init all vital functionality
     *
     */
    _uiInit() {
        super._uiInit();

        // Additional Helpers Init
        this.helpers([
            'table-tools-sections',
            'highlightjs'
        ]);
    }
}

// Once everything is loaded
jQuery(() => {
    // Create a new instance of App
   window.Docs = new App();
});
