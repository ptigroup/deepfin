"""
📦 Package: app
📝 Purpose: Main application package for LLM Financial Pipeline v2.0

🎯 What This Package Contains:
This is the root package for the refactored application. It organizes code
using Vertical Slice Architecture, where each feature is self-contained.

📁 Package Structure:
- core/          - Core infrastructure (config, logging, database, health)
- shared/        - Shared models, schemas, and utilities
- detection/     - Table detection feature (vertical slice)
- statements/    - Financial statements feature (vertical slice)
- extraction/    - Data extraction feature (vertical slice)
- consolidation/ - Data consolidation feature (vertical slice)
- jobs/          - Background job processing
- auth/          - Authentication and authorization

💡 Architecture Principle:
Vertical Slice Architecture means each feature directory contains everything
it needs: models, schemas, routes, services, and tests. This makes features
independent and easy to understand.

🔗 Learn More:
- Vertical Slice Architecture: https://www.jimmybogard.com/vertical-slice-architecture/
- Python Packages: https://docs.python.org/3/tutorial/modules.html#packages
"""

__version__ = "2.0.0"
