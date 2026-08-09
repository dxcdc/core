/*
 *  Document   : helpers.js
 *  Author     : pixelcave
 *  Description: Various jQuery plugins inits as well as custom helpers
 *
 */

// Import global dependencies
import './../bootstrap';

// Import required modules
import Tools from './tools';

// Helpers
export default class Helpers {
   /*
    * Run helpers
    *
    */
   static run(helpers, options = {}) {
       let helperList = {
           'core-bootstrap-tooltip': () => this.coreBootstrapTooltip(),
           'core-bootstrap-popover': () => this.coreBootstrapPopover(),
           'core-bootstrap-tabs': () => this.coreBootstrapTabs(),
           'core-toggle-class': () => this.coreToggleClass(),
           'core-scroll-to': () => this.coreScrollTo(),
           'core-year-copy': () => this.coreYearCopy(),
           'core-appear': () => this.coreAppear(),
           'print': () => this.print(),
           'table-tools-sections': () => this.tableToolsSections(),
           'table-tools-checkable': () => this.tableToolsCheckable(),
           'highlightjs': () => this.highlightjs()
       };

       if (helpers instanceof Array) {
           for (let index in helpers) {
               if (helperList[helpers[index]]) {
                   helperList[helpers[index]](options);
               }
           }
       } else {
           if (helperList[helpers]) {
               helperList[helpers](options);
           }
       }
   }

    /*
     ********************************************************************************************
     *
     * CORE HELPERS
     *
     * Third party plugin inits or various custom user interface helpers to extend functionality
     * They are called by default and can be used right away
     *
     *********************************************************************************************
     */

    /*
     * Bootstrap Tooltip, for more examples you can check out https://getbootstrap.com/docs/4.0/components/tooltips/
     *
     * Helpers.run('core-bootstrap-tooltip');
     *
     * Example usage:
     *
     * <button type="button" class="btn btn-primary" data-toggle="tooltip" title="Tooltip Text">Example</button> or
     * <button type="button" class="btn btn-primary js-tooltip" title="Tooltip Text">Example</button>
     *
     */
    static coreBootstrapTooltip() {
        jQuery('[data-toggle="tooltip"]:not(.js-tooltip-enabled)').add('.js-tooltip:not(.js-tooltip-enabled)').each((index, element) => {
            let el = jQuery(element);

            // Add .js-tooltip-enabled class to tag it as activated and init it
            jQuery(element).addClass('js-tooltip-enabled').tooltip({
                container: el.data('container') || 'body',
                animation: el.data('animation') || false
            });
        });
    }

    /*
     * Bootstrap Popover, for more examples you can check outhttps://getbootstrap.com/docs/4.0/components/popovers/
     *
     * Helpers.run('core-bootstrap-popover');
     *
     * Example usage:
     *
     * <button type="button" class="btn btn-primary" data-toggle="popover" title="Popover Title" data-content="This is the content of the Popover">Example</button> or
     * <button type="button" class="btn btn-primary js-popover" title="Popover Title" data-content="This is the content of the Popover">Example</button>
     *
     */
    static coreBootstrapPopover() {
        jQuery('[data-toggle="popover"]:not(.js-popover-enabled)').add('.js-popover:not(.js-popover-enabled)').each((index, element) => {
            let el = jQuery(element);

            // Add .js-popover-enabled class to tag it as activated and init it
            el.addClass('js-popover-enabled').popover({
                container: el.data('container') || 'body',
                animation: el.data('animation') || false,
                trigger: el.data('trigger') || 'hover focus'
            });
        });
    }

    /*
     * Bootstrap Tab, for examples you can check out http://getbootstrap.com/docs/4.0/components/navs/#tabs
     *
     * Helpers.run('core-bootstrap-tabs');
     *
     * Example usage:
     *
     * Please check out the Tabs page for complete markup examples
     *
     */
    static coreBootstrapTabs() {
        jQuery('[data-toggle="tabs"]:not(.js-tabs-enabled)').add('.js-tabs:not(.js-tabs-enabled)').each((index, element) => {
            // Add .js-tabs-enabled class to tag it as activated and init it
            jQuery(element).addClass('js-tabs-enabled').find('a').on('click.pixelcave.helpers.core', (e) => {
                e.preventDefault();
                jQuery(e.currentTarget).tab('show');
            });
        });
    }

    /*
     * Toggle class on element click
     *
     * Helpers.run('core-toggle-class');
     *
     * Example usage (on button click, "exampleClass" class is toggled on the element with id "elementID"):
     *
     * <button type="button" class="btn btn-primary" data-toggle="class-toggle" data-target="#elementID" data-class="exampleClass">Toggle</button>
     *
     */
    static coreToggleClass() {
        jQuery('[data-toggle="class-toggle"]:not(.js-class-toggle-enabled)').on('click.pixelcave.helpers.core', (e) => {
            let el = jQuery(e.currentTarget);

            // Add .js-class-toggle-enabled class to tag it as activated and then blur it
            el.addClass('js-class-toggle-enabled').blur();

            // Toggle class
            jQuery(el.data('target').toString()).toggleClass(el.data('class').toString());
        });
    }

    /*
     * Scroll to element with animation
     *
     * Helpers.run('core-scroll-to');
     *
     * Example usage (on click, the page will scroll to element with id "elementID" in "500" ms):
     *
     * <a href="#elementID" data-toggle="scroll-to" data-speed="500">Go</a> or
     * <button type="button" class="btn btn-primary" data-toggle="scroll-to" data-speed="500" data-target="#elementID">Go</button>
     *
     */
    static coreScrollTo() {
        jQuery('[data-toggle="scroll-to"]:not(.js-scroll-to-enabled)').on('click.pixelcave.helpers.core', (e) => {
            e.stopPropagation();

            // Set variables
            let lHeader         = jQuery('#page-header');
            let el              = jQuery(e.currentTarget);
            let elTarget        = el.data('target') || el.attr('href');
            let elSpeed         = el.data('speed') || 500;
            let elOffset        = el.data('offset') || 0;

            // Add .js-scroll-to-enabled class to tag it as activated
            el.addClass('js-scroll-to-enabled');

            // Scroll to element
            jQuery('html, body').animate({
                scrollTop: jQuery(elTarget).offset().top - elOffset
            }, elSpeed);
        });
    }

    /*
     * Add the correct copyright year to an element
     *
     * Helpers.run('core-year-copy');
     *
     * Example usage (it will get populated with current year if empty or will append it to specified year if needed):
     *
     * <span data-toggle="year-copy"></span> or
     * <span data-toggle="year-copy">2018</span>
     *
     */
    static coreYearCopy() {
        let el = jQuery('[data-toggle="year-copy"]:not(.js-year-copy-enabled)');

        if (el.length > 0) {
            let date        = new Date();
            let curYear     = date.getFullYear();
            let baseYear    = (el.html().length > 0) ? el.html() : curYear;

            // Add .js-scroll-to-enabled class to tag it as activated and set the correct year
            el.addClass('js-year-copy-enabled').html(
                (parseInt(baseYear) >= curYear) ? curYear : baseYear + '-' + curYear.toString().substr(2, 2)
            );
        }
    }

    /*
     * jQuery Appear, for more examples you can check out https://github.com/bas2k/jquery.appear
     *
     * Helpers.run('core-appear');
     *
     * Example usage (the following div will appear on scrolling, remember to add the invisible class):
     *
     * <div class="invisible" data-toggle="appear">...</div>
     *
     */
    static coreAppear() {
        // Add a specific class on elements (when they become visible on scrolling)
        jQuery('[data-toggle="appear"]:not(.js-appear-enabled)').each((index, element) => {
            let windowW     = Tools.getWidth();
            let el          = jQuery(element);
            let elCssClass  = el.data('class') || 'animated fadeIn';
            let elOffset    = el.data('offset') || 0;
            let elTimeout   = (windowW < 992) ? 0 : (el.data('timeout') ? el.data('timeout') : 0);

            // Add .js-appear-enabled class to tag it as activated and init it
            el.addClass('js-appear-enabled').appear(() => {
                setTimeout(() => {
                    el.removeClass('invisible').addClass(elCssClass);
                }, elTimeout);
            }, {accY: elOffset});
        });
    }

    /*
     ********************************************************************************************
     *
     * UI HELPERS (ON DEMAND)
     *
     * Third party plugin inits or various custom user interface helpers to extend functionality
     * They need to be called in a page to be initialized. They are included to be easy to
     * init them on demand on multiple pages (usually repeated init code in common components)
     *
     ********************************************************************************************
     */

    /*
      * Print Page functionality
      *
      * Helpers.run('print');
      *
      */
    static print() {
        // Store all #page-container classes
        let lPage = jQuery('#page-container');
        let pageCls = lPage.prop('class');

        // Remove all classes from #page-container
        lPage.prop('class', '');

        // Print the page
        window.print();

        // Restore all #page-container classes
        lPage.prop('class', pageCls);
    }

    /*
     * Table sections functionality
     *
     * Helpers.run('table-tools-sections');
     *
     * Example usage:
     *
     * Please check out the Table Helpers page for complete markup examples
     *
     */
    static tableToolsSections() {
        // For each table
        jQuery('.js-table-sections:not(.js-table-sections-enabled)').each((index, element) => {
            let table = jQuery(element);

            // Add .js-table-sections-enabled class to tag it as activated
            table.addClass('js-table-sections-enabled');

            // When a row is clicked in tbody.js-table-sections-header
            jQuery('.js-table-sections-header > tr', table).on('click.pixelcave.helpers', (e) => {
                if (e.target.type !== 'checkbox'
                        && e.target.type !== 'button'
                        && e.target.tagName.toLowerCase() !== 'a'
                        && !jQuery(e.target).parent('a').length
                        && !jQuery(e.target).parent('button').length
                        && !jQuery(e.target).parent('.custom-control').length
                        && !jQuery(e.target).parent('label').length) {
                    let row    = jQuery(e.currentTarget);
                    let tbody  = row.parent('tbody');

                    if (!tbody.hasClass('show')) {
                        jQuery('tbody', table).removeClass('show');
                    }

                    tbody.toggleClass('show');
                }
            });
        });
    }

    /*
     * Checkable table functionality
     *
     * Helpers.run('table-tools-checkable');
     *
     * Example usage:
     *
     * Please check out the Table Helpers page for complete markup examples
     *
     */
    static tableToolsCheckable() {
        // For each table
        jQuery('.js-table-checkable:not(.js-table-checkable-enabled)').each((index, element) => {
            let table = jQuery(element);

            // Add .js-table-checkable-enabled class to tag it as activated
            table.addClass('js-table-checkable-enabled');

            // When a checkbox is clicked in thead
            jQuery('thead input:checkbox', table).on('click.pixelcave.helpers', (e) => {
                let checkedStatus = jQuery(e.currentTarget).prop('checked');

                // Check or uncheck all checkboxes in tbody
                jQuery('tbody input:checkbox', table).each((index, element) => {
                    let checkbox = jQuery(element);

                    checkbox.prop('checked', checkedStatus);
                    this.tableToolscheckRow(checkbox, checkedStatus);
                });
            });

            // When a checkbox is clicked in tbody
            jQuery('tbody input:checkbox, tbody input + label', table).on('click.pixelcave.helpers', (e) => {
                console.log(e.target.type);
                let checkbox = jQuery(e.currentTarget);

                this.tableToolscheckRow(checkbox, checkbox.prop('checked'));
            });

            // When a row is clicked in tbody
            jQuery('tbody > tr', table).on('click.pixelcave.helpers', (e) => {
                if (e.target.type !== 'checkbox'
                        && e.target.type !== 'button'
                        && e.target.tagName.toLowerCase() !== 'a'
                        && !jQuery(e.target).parent('a').length
                        && !jQuery(e.target).parent('button').length
                        && !jQuery(e.target).parent('.custom-control').length
                        && !jQuery(e.target).parent('label').length) {
                    let checkbox       = jQuery('input:checkbox', e.currentTarget);
                    let checkedStatus  = checkbox.prop('checked');

                    checkbox.prop('checked', !checkedStatus);
                    this.tableToolscheckRow(checkbox, !checkedStatus);
                }
            });
        });
    }

    // Checkable table functionality helper - Checks or unchecks table row
    static tableToolscheckRow(checkbox, checkedStatus) {
        if (checkedStatus) {
            checkbox.closest('tr').addClass('table-active');
        } else {
            checkbox.closest('tr').removeClass('table-active');
        }
    }

    /*
     ********************************************************************************************
     *
     * All the following helpers require each plugin's resources (JS, CSS) to be included in order to work
     *
     ********************************************************************************************
     */

    /*
     * Highlight.js, for more examples you can check out https://highlightjs.org/usage/
     *
     * Helpers.run('highlightjs');
     *
     * Example usage:
     *
     * Please check out the Syntax Highlighting page in Components for complete markup examples
     *
     */
    static highlightjs() {
        // Init Highlight.js
        if ( ! hljs.isHighlighted) {
            hljs.initHighlighting();
        }
    }
}
