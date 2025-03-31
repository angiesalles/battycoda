/*!
 * jQuery bootstrap 4 breakpoint check
 * Check the current visibility of bootstrap 4 breakpoints.
 *
 * Provides two sets of checks:
 *
 * Absolutely within the min and max sizes for the breakpoint:
 *
 * @example `$.isXs()` function alias for `$.isBreakpoint("xs")`
 * @example `$.isSm()` function alias for `$.isBreakpoint("sm")`
 * @example `$.isMd()` function alias for `$.isBreakpoint("md")`
 * @example `$.isLg()` function alias for `$.isBreakpoint("lg")`
 * @example `$.isXl()` function alias for `$.isBreakpoint("xl")`
 *
 * Within the min size for the breakpoint:
 *
 * @example `$.isXsUp()` function alias for `$.isBreakpointUp("xs")`
 * @example `$.isSmUp()` function alias for `$.isBreakpointUp("sm")`
 * @example `$.isMdUp()` function alias for `$.isBreakpointUp("md")`
 * @example `$.isLgUp()` function alias for `$.isBreakpointUp("lg")`
 * @example `$.isXlUp()` function alias for `$.isBreakpointUp("xl")`
 *
 * @version 1.2.0
 * @copyright Jens A. (cakebake) and other contributors
 * @license Released under the MIT license
 */

;(function ($) {

    /**
     * Private function for checking whether an element with a given class
     * is visible.
     * @param {string} utilCls
     * @return {boolean}
     */
    var isElementWithClassVisible = function (utilCls) {
        var element, visible;

        element = $("<div/>", {
            "class": utilCls
        }).appendTo("body");

        visible = element.is(":visible");
        element.remove();

        return visible;
    };

    /**
     * Base function to check whether the current viewport is exactly between
     * the minimum and maximum boundaries for the given bootstrap 4 breakpoint.
     *
     * This will only return true for ONE of the breakpoints at any one time.
     *
     * @param {string} breakPoint Something like xs|sm|md|lg|xl
     * @returns {boolean}
     */
    $.isBreakpoint = function (breakPoint) {
        var utilCls;

        switch(breakPoint) {
            case "xs":
                utilCls = "d-block d-sm-none";
                break;
            case "sm":
                utilCls = "d-none d-sm-block d-md-none";
                break;
            case "md":
                utilCls = "d-none d-md-block d-lg-none";
                break;
            case "lg":
                utilCls = "d-none d-lg-block d-xl-none";
                break;
            case "xl":
                utilCls = "d-none d-xl-block";
                break;
        }

        return isElementWithClassVisible(utilCls);
    };

    /**
     * Base function to check the current visibility of
     * @param {string} breakPoint Something like  xs|sm|md|lg
     * @return {boolean}
     */
    $.isBreakpointUp = function (breakPoint) {
        var utilCls;

        switch(breakPoint) {
            case "xs":
                return true; // XS is always visible at larger sizes
            case "sm":
                utilCls = "d-none d-sm-block";
                break;
            case "md":
                utilCls = "d-none d-md-block";
                break;
            case "lg":
                utilCls = "d-none d-lg-block";
                break;
            case "xl":
                utilCls = "d-none d-xl-block";
                break;
        }

        return isElementWithClassVisible(utilCls);
    };

    $.extend($, {

        /**
         * Check whether the current viewport width is smaller than the "sm" breakpoint.
         * Shorthand function alias for $.isBreakpoint("xs")
         *
         * @returns {boolean}
         */
        isXs: function () {
            return $.isBreakpoint("xs")
        },

        /**
         * Checks whether the current viewport width is between the "sm" and "md"
         * breakpoints (eg. is "sm" only).
         * Shorthand function alias for $.isBreakpoint("sm")
         *
         * @returns {boolean}
         */
        isSm: function () {
            return $.isBreakpoint("sm")
        },

        /**
         * Checks whether the current viewport width is between the "md" and "lg"
         * breakpoints (eg. is "md" only).
         *
         * @returns {boolean}
         */
        isMd: function () {
            return $.isBreakpoint("md")
        },

        /**
         * Checks whether the current viewport width is between the "lg" and "xl"
         * breakpoints (eg. is "lg" only).
         * Shorthand function alias for $.isBreakpoint("lg")
         *
         * @returns {boolean}
         */
        isLg: function () {
            return $.isBreakpoint("lg")
        },

        /**
         * Check whether the current viewport width is larger than the "xl" breakpoint.
         * Shorthand function alias for $.isBreakpoint("xl")
         *
         * @returns {boolean}
         */
        isXl: function () {
            return $.isBreakpoint("xl")
        },

        /**
         * Check whether the current viewport with is within the "xs" breakpoint,
         * or larger. This is always true, because the "xs" breakpoint is just
         * min-width:0 and upwards.
         * Shorthand function alias for $.isBreakpointUp("xs")
         *
         * @return {boolean}
         */
        isXsUp: function () {
            return $.isBreakpointUp("xs");
        },

        /**
         * Check whether the current viewport with is within the "sm" breakpoint,
         * or larger.
         * Shorthand function alias for $.isBreakpointUp("sm")
         *
         * @return {boolean}
         */
        isSmUp: function () {
            return $.isBreakpointUp("sm");
        },

        /**
         * Check whether the current viewport with is within the "md" breakpoint,
         * or larger.
         * Shorthand function alias for $.isBreakpointUp("md")
         *
         * @return {boolean}
         */
        isMdUp: function () {
            return $.isBreakpointUp("md");
        },

        /**
         * Check whether the current viewport with is within the "lg" breakpoint,
         * or larger.
         * Shorthand function alias for $.isBreakpointUp("lg")
         *
         * @return {boolean}
         */
        isLgUp: function () {
            return $.isBreakpointUp("lg");
        },

        /**
         * Check whether the current viewport with is within the "lg" breakpoint,
         * or larger.
         * Shorthand function alias for $.isBreakpointUp("lg")
         *
         * @return {boolean}
         */
        isXlUp: function () {
            return $.isBreakpointUp("xl");
        },

    });

})(jQuery);
