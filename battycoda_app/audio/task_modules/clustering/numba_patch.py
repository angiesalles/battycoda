"""
Numba and librosa environment configuration.

This module MUST be imported before any modules that might import numba or librosa.
It disables JIT compilation to prevent memory issues in the Celery worker environment.
"""

import importlib.util
import os

# Environment setup for Numba and librosa
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["LIBROSA_CACHE_LEVEL"] = "0"
os.environ["LIBROSA_CACHE_DIR"] = "/tmp/librosa_cache"

# Patch Numba before any imports that might use it
if importlib.util.find_spec("numba"):
    import numba
    import numba.core.registry

    def no_jit(*args, **kwargs):
        """No-op JIT decorator that just returns the function unchanged."""

        def decorator(func):
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    numba.jit = no_jit
    numba.njit = no_jit
    numba.vectorize = no_jit
    numba.guvectorize = no_jit
    numba.cfunc = no_jit
    numba.generated_jit = no_jit
    numba.core.registry.CPUDispatcher = no_jit

    if hasattr(numba, "np") and hasattr(numba.np, "vectorize"):
        numba.np.vectorize = no_jit
