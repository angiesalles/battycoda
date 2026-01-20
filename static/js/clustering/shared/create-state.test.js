/**
 * Tests for clustering/shared/create-state.js
 */

import { describe, it, expect } from 'vitest';
import { createState, createBooleanState, createStateModule } from './create-state.js';

describe('clustering/shared/create-state', () => {
  describe('createState', () => {
    it('should create state with initial value', () => {
      const state = createState(42);
      expect(state.get()).toBe(42);
    });

    it('should create state with null initial value', () => {
      const state = createState(null);
      expect(state.get()).toBe(null);
    });

    it('should update state with set', () => {
      const state = createState(1);
      state.set(2);
      expect(state.get()).toBe(2);
    });

    it('should reset to initial value', () => {
      const state = createState('initial');
      state.set('changed');
      expect(state.get()).toBe('changed');

      state.reset();
      expect(state.get()).toBe('initial');
    });

    it('should work with array values', () => {
      const state = createState([]);
      expect(state.get()).toEqual([]);

      state.set([1, 2, 3]);
      expect(state.get()).toEqual([1, 2, 3]);

      state.reset();
      expect(state.get()).toEqual([]);
    });

    it('should work with object values', () => {
      const initial = { a: 1 };
      const state = createState(initial);
      expect(state.get()).toBe(initial);

      const newObj = { b: 2 };
      state.set(newObj);
      expect(state.get()).toBe(newObj);
    });
  });

  describe('createBooleanState', () => {
    it('should default to false', () => {
      const state = createBooleanState();
      expect(state.get()).toBe(false);
    });

    it('should create state with true initial value', () => {
      const state = createBooleanState(true);
      expect(state.get()).toBe(true);
    });

    it('should coerce truthy values to true', () => {
      const state = createBooleanState(false);

      state.set(1);
      expect(state.get()).toBe(true);

      state.set('yes');
      expect(state.get()).toBe(true);

      state.set({});
      expect(state.get()).toBe(true);
    });

    it('should coerce falsy values to false', () => {
      const state = createBooleanState(true);

      state.set(0);
      expect(state.get()).toBe(false);

      state.set(true);
      state.set('');
      expect(state.get()).toBe(false);

      state.set(true);
      state.set(null);
      expect(state.get()).toBe(false);
    });

    it('should reset to initial boolean value', () => {
      const state = createBooleanState(true);
      state.set(false);
      expect(state.get()).toBe(false);

      state.reset();
      expect(state.get()).toBe(true);
    });
  });

  describe('createStateModule', () => {
    it('should create getters and setters for simple values', () => {
      const state = createStateModule({
        count: 0,
        name: 'test',
      });

      expect(state.getCount()).toBe(0);
      expect(state.getName()).toBe('test');

      state.setCount(5);
      state.setName('updated');

      expect(state.getCount()).toBe(5);
      expect(state.getName()).toBe('updated');
    });

    it('should create boolean state with config object', () => {
      const state = createStateModule({
        isLoading: { value: false, boolean: true },
      });

      expect(state.getIsLoading()).toBe(false);

      state.setIsLoading(1);
      expect(state.getIsLoading()).toBe(true);

      state.setIsLoading(0);
      expect(state.getIsLoading()).toBe(false);
    });

    it('should reset all state with resetAll', () => {
      const state = createStateModule({
        count: 0,
        items: [],
        isActive: { value: false, boolean: true },
      });

      state.setCount(10);
      state.setItems([1, 2, 3]);
      state.setIsActive(true);

      expect(state.getCount()).toBe(10);
      expect(state.getItems()).toEqual([1, 2, 3]);
      expect(state.getIsActive()).toBe(true);

      state.resetAll();

      expect(state.getCount()).toBe(0);
      expect(state.getItems()).toEqual([]);
      expect(state.getIsActive()).toBe(false);
    });

    it('should handle null initial values', () => {
      const state = createStateModule({
        selectedId: null,
      });

      expect(state.getSelectedId()).toBe(null);

      state.setSelectedId(42);
      expect(state.getSelectedId()).toBe(42);

      state.resetAll();
      expect(state.getSelectedId()).toBe(null);
    });
  });
});
