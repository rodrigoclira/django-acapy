"""
Django integration for the TractionAPI library.
This file provides utilities for using TractionAPI within a Django application.
"""

from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy

from .traction_api import TractionAPI, TractionAPIError


class TractionDjangoClient:
    """Django-specific wrapper for TractionAPI"""

    _instance = None

    @classmethod
    def get_client(cls):
        """
        Get or create a singleton TractionAPI client instance

        Returns:
            TractionAPI: Configured API client
        """
        if cls._instance is None:
            # Get settings from Django settings
            api_key = getattr(settings, "TRACTION_API_KEY", None)
            base_url = getattr(
                settings, "TRACTION_API_BASE_URL", "https://api.traction.io/v1"
            )
            timeout = getattr(settings, "TRACTION_API_TIMEOUT", 30)

            if not api_key:
                raise ValueError("TRACTION_API_KEY is required in Django settings")

            cls._instance = TractionAPI(
                api_key=api_key, base_url=base_url, timeout=timeout
            )

        return cls._instance

    @classmethod
    def reset_client(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None


def get_traction_client():
    """
    Helper function to get the TractionAPI client

    Returns:
        TractionAPI: Configured API client
    """
    return TractionDjangoClient.get_client()


# Cache decorators for common operations
def cache_traction_data(func):
    """
    Decorator to cache Traction API responses

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with caching
    """
    cache_timeout = getattr(
        settings, "TRACTION_CACHE_TIMEOUT", 300
    )  # 5 minutes default

    def wrapper(*args, **kwargs):
        # Create a cache key based on function name and arguments
        cache_key = (
            f"traction_{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
        )
        result = cache.get(cache_key)

        if result is None:
            result = func(*args, **kwargs)
            cache.set(cache_key, result, cache_timeout)

        return result

    return wrapper
