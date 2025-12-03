import gettext
import os
import sys

_current_translation = None

def install_language(lang_code):
    """
    Installs the specified language for gettext.
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
    return _current_translation
