import gettext
import os

"""
Internationalization (i18n) utilities for language switching and translation management.

This module provides functions to install and manage gettext-based translations for the application.
"""

_current_translation = None

def install_language(lang_code):
    """
    Install the specified language for gettext translations.

    Args:
        lang_code (str): Language code to install (e.g., 'en', 'ua').

    Side Effects:
        Sets the global translation for the application. Installs the '_' function in the builtins for runtime translation.
        Falls back to English if the specified translation is not found.
    """
    global _current_translation
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locales_dir = os.path.join(base_dir, 'locales')
    
    try:
        language = gettext.translation('messages', localedir=locales_dir, languages=[lang_code])
        language.install()
        _current_translation = language
    except FileNotFoundError:
        # Fallback to null translation (English/default) if file not found
        print(f"Translation for '{lang_code}' not found. Falling back to default.")
        gettext.install('messages', localedir=locales_dir, languages=['en'])
        _current_translation = gettext.NullTranslations()

def get_current_translation():
    """
    Get the currently active gettext translation object.

    Returns:
        gettext.GNUTranslations | gettext.NullTranslations | None: The current translation object, or None if not set.
    """
    return _current_translation
