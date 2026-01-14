/**
 * Audio API mock helpers for testing
 */

import { vi } from 'vitest';

/**
 * Create a mock AudioContext
 */
export function createMockAudioContext() {
  return {
    currentTime: 0,
    sampleRate: 44100,
    state: 'running',
    destination: {},
    createGain: vi.fn(() => ({
      gain: { value: 1, setValueAtTime: vi.fn() },
      connect: vi.fn(),
      disconnect: vi.fn(),
    })),
    createBufferSource: vi.fn(() => ({
      buffer: null,
      connect: vi.fn(),
      disconnect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
      onended: null,
    })),
    createAnalyser: vi.fn(() => ({
      fftSize: 2048,
      frequencyBinCount: 1024,
      getByteFrequencyData: vi.fn(),
      getByteTimeDomainData: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
    })),
    decodeAudioData: vi.fn(() =>
      Promise.resolve({
        duration: 5.0,
        numberOfChannels: 1,
        sampleRate: 44100,
        length: 220500,
        getChannelData: vi.fn(() => new Float32Array(220500)),
      })
    ),
    resume: vi.fn(() => Promise.resolve()),
    suspend: vi.fn(() => Promise.resolve()),
    close: vi.fn(() => Promise.resolve()),
  };
}

/**
 * Create a mock HTMLAudioElement
 */
export function createMockAudioElement() {
  return {
    src: '',
    currentTime: 0,
    duration: 0,
    paused: true,
    volume: 1,
    muted: false,
    playbackRate: 1,
    play: vi.fn(() => Promise.resolve()),
    pause: vi.fn(),
    load: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
}

/**
 * Mock the global Audio constructor
 */
export function mockAudioConstructor() {
  const mockAudio = createMockAudioElement();
  global.Audio = vi.fn(() => mockAudio);
  return mockAudio;
}

/**
 * Mock the AudioContext constructor
 */
export function mockAudioContextConstructor() {
  const mockContext = createMockAudioContext();
  global.AudioContext = vi.fn(() => mockContext);
  global.webkitAudioContext = global.AudioContext;
  return mockContext;
}
