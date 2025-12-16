"""
📦 Package: app.core
📝 Purpose: Core infrastructure modules for the application

🎯 What This Package Contains:
This package contains foundational infrastructure that's used throughout
the application. Think of it as the "engine room" of your application.

📁 Modules in this Package:
- config.py     - Application settings and configuration
- logging.py    - Structured logging setup
- database.py   - Database connection and session management
- health.py     - Health check endpoints
- middleware.py - Request/response middleware
- exceptions.py - Custom exception classes

💡 Why "Core"?
These modules are "core" because:
1. They're used by multiple features (shared infrastructure)
2. They need to be initialized early in the application lifecycle
3. They don't belong to any specific business feature

🔄 Import Pattern:
Other parts of the application import from here:
>>> from app.core.config import get_settings
>>> from app.core.logging import get_logger

📚 Learn More:
- Python Package Organization: https://docs.python.org/3/tutorial/modules.html
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
"""

from app.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
