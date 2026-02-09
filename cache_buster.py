"""
Cache Busting Utility for Static Assets
Generates version hashes for CSS/JS files to prevent browser caching issues.
"""

import hashlib
import os
from pathlib import Path
from functools import lru_cache


class CacheBuster:
    """
    Manages cache-busting for static files using content-based hashing.
    
    Usage in templates:
        {{ url_for('static', filename='css/style.css') | cache_bust }}
        
    This will generate:
        /static/css/style.css?v=abc123def456
    """
    
    def __init__(self, static_folder='static'):
        self.static_folder = static_folder
        self._cache = {}
    
    @lru_cache(maxsize=128)
    def get_file_hash(self, filename):
        """
        Generate MD5 hash of file content for versioning.
        
        Args:
            filename: Path to file relative to static folder
            
        Returns:
            Short hash string (first 12 chars of MD5)
        """
        filepath = Path(self.static_folder) / filename
        
        if not filepath.exists():
            return 'missing'
        
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:12]
            return file_hash
        except Exception as e:
            print(f"Error hashing {filename}: {e}")
            return 'error'
    
    def bust_cache(self, filename):
        """
        Add version parameter to filename.
        
        Args:
            filename: Static file path (e.g., 'css/style.css')
            
        Returns:
            Versioned filename (e.g., 'css/style.css?v=abc123')
        """
        file_hash = self.get_file_hash(filename)
        return f"{filename}?v={file_hash}"
    
    def clear_cache(self):
        """Clear the internal hash cache (useful for development)."""
        self.get_file_hash.cache_clear()
        self._cache.clear()


# Global instance
_cache_buster = None


def init_cache_buster(app):
    """
    Initialize cache buster with Flask app.
    
    Args:
        app: Flask application instance
    """
    global _cache_buster
    _cache_buster = CacheBuster(app.static_folder)
    
    # Add template filter
    @app.template_filter('cache_bust')
    def cache_bust_filter(filename):
        """Jinja2 filter for cache busting in templates."""
        if _cache_buster:
            return _cache_buster.bust_cache(filename)
        return filename
    
    # Add template global function
    @app.context_processor
    def inject_cache_bust():
        """Make cache_bust available in all templates."""
        return {
            'cache_bust': lambda f: _cache_buster.bust_cache(f) if _cache_buster else f
        }
    
    # Clear cache in debug mode on each request
    if app.debug:
        @app.before_request
        def clear_cache_on_debug():
            if _cache_buster:
                _cache_buster.clear_cache()
    
    return _cache_buster


def get_cache_buster():
    """Get the global CacheBuster instance."""
    return _cache_buster


# CLI command for generating manifest
def generate_manifest(static_folder='static'):
    """
    Generate a manifest.json file with all static file hashes.
    Useful for production deployments.
    
    Args:
        static_folder: Path to static files directory
    """
    cache_buster = CacheBuster(static_folder)
    manifest = {}
    
    static_path = Path(static_folder)
    
    # Find all CSS and JS files
    for ext in ['css', 'js']:
        for filepath in static_path.rglob(f'*.{ext}'):
            relative_path = str(filepath.relative_to(static_path)).replace('\\', '/')
            file_hash = cache_buster.get_file_hash(relative_path)
            manifest[relative_path] = {
                'hash': file_hash,
                'versioned': f"{relative_path}?v={file_hash}"
            }
    
    return manifest


if __name__ == '__main__':
    # Generate and print manifest for inspection
    import json
    manifest = generate_manifest()
    print(json.dumps(manifest, indent=2))
