/**
 * Global type declarations for BattyCoda
 *
 * This file declares types for global objects and external dependencies
 * that are loaded via CDN rather than bundled by Vite.
 */

/// <reference types="vite/client" />

// jQuery is loaded via CDN
declare const $: JQueryStatic;
declare const jQuery: JQueryStatic;

// Bootstrap is loaded via CDN
declare namespace bootstrap {
  class Modal {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    toggle(): void;
    dispose(): void;
    static getInstance(element: Element): Modal | null;
    static getOrCreateInstance(element: Element): Modal;
  }

  class Tooltip {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    toggle(): void;
    dispose(): void;
    static getInstance(element: Element): Tooltip | null;
  }

  class Popover {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    toggle(): void;
    dispose(): void;
    static getInstance(element: Element): Popover | null;
  }

  class Dropdown {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    toggle(): void;
    dispose(): void;
    static getInstance(element: Element): Dropdown | null;
  }

  class Collapse {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    hide(): void;
    toggle(): void;
    dispose(): void;
    static getInstance(element: Element): Collapse | null;
  }

  class Tab {
    constructor(element: Element, options?: Record<string, unknown>);
    show(): void;
    dispose(): void;
    static getInstance(element: Element): Tab | null;
  }
}

// Toastr notification library
declare namespace toastr {
  interface ToastrOptions {
    closeButton?: boolean;
    debug?: boolean;
    newestOnTop?: boolean;
    progressBar?: boolean;
    positionClass?: string;
    preventDuplicates?: boolean;
    onclick?: (() => void) | null;
    showDuration?: number;
    hideDuration?: number;
    timeOut?: number;
    extendedTimeOut?: number;
    showEasing?: string;
    hideEasing?: string;
    showMethod?: string;
    hideMethod?: string;
  }

  function success(message: string, title?: string, options?: ToastrOptions): void;
  function info(message: string, title?: string, options?: ToastrOptions): void;
  function warning(message: string, title?: string, options?: ToastrOptions): void;
  function error(message: string, title?: string, options?: ToastrOptions): void;
  function clear(): void;
  function remove(): void;

  let options: ToastrOptions;
}

// Window extensions for BattyCoda
interface Window {
  jQuery: JQueryStatic;
  $: JQueryStatic;
  bootstrap: typeof bootstrap;
  toastr: typeof toastr;

  // Theme URL mapping for dynamic theme loading
  __VITE_THEME_URLS__?: Record<string, string>;

  // Cluster mapping globals
  existingMappings?: unknown[];
  initClusterMapping?: (options: unknown) => void;
  createMapping?: (clusterId: number) => void;
  filterClusters?: (filter: string) => void;
  sortClusters?: (sortBy: string) => void;
  filterSpecies?: (speciesId: string) => void;
  ClusterMapping?: Record<string, (...args: unknown[]) => unknown>;

  // Profile page
  copyApiKey?: () => void;

  // App initialization
  activateManagementFeatures?: () => void;

  // Security utilities
  escapeHtml?: (text: string) => string;
  validateUrl?: (url: string, allowedProtocols?: string[]) => boolean;

  // Player instances (for audio player)
  players?: Record<string, unknown>;
}
