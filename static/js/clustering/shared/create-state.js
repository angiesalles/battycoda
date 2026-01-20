/**
 * State Factory Utilities
 *
 * Provides factory functions to reduce boilerplate when creating state modules.
 * Each clustering module can use these to create consistent getter/setter pairs.
 */

/**
 * Create a simple state variable with getter and setter
 * @param {*} initialValue - Initial value for the state
 * @returns {Object} Object with get, set functions
 */
export function createState(initialValue) {
  let value = initialValue;

  return {
    get: () => value,
    set: (newValue) => {
      value = newValue;
    },
    reset: () => {
      value = initialValue;
    },
  };
}

/**
 * Create a boolean state variable that coerces values
 * @param {boolean} initialValue - Initial boolean value
 * @returns {Object} Object with get, set functions
 */
export function createBooleanState(initialValue = false) {
  let value = !!initialValue;

  return {
    get: () => value,
    set: (newValue) => {
      value = !!newValue;
    },
    reset: () => {
      value = !!initialValue;
    },
  };
}

/**
 * Create a state module with multiple variables and a reset function
 * @param {Object} config - Configuration object mapping names to initial values
 * @returns {Object} Object with getters, setters, and resetAll function
 *
 * @example
 * const state = createStateModule({
 *   selectedId: null,
 *   items: [],
 *   isLoading: { value: false, boolean: true }
 * });
 * // Returns: { getSelectedId, setSelectedId, getItems, setItems, getIsLoading, setIsLoading, resetAll }
 */
export function createStateModule(config) {
  const states = {};
  const result = {};

  for (const [name, initialConfig] of Object.entries(config)) {
    // Support both simple values and config objects
    const isConfigObject =
      initialConfig !== null && typeof initialConfig === 'object' && 'value' in initialConfig;
    const initialValue = isConfigObject ? initialConfig.value : initialConfig;
    const isBoolean = isConfigObject && initialConfig.boolean;

    states[name] = isBoolean ? createBooleanState(initialValue) : createState(initialValue);

    // Create camelCase getter/setter names
    const capitalizedName = name.charAt(0).toUpperCase() + name.slice(1);
    result[`get${capitalizedName}`] = states[name].get;
    result[`set${capitalizedName}`] = states[name].set;
  }

  // Add resetAll function
  result.resetAll = () => {
    for (const state of Object.values(states)) {
      state.reset();
    }
  };

  return result;
}
