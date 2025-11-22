"""
School module admin configuration.

This file imports all admin configurations from submodules
to ensure they are registered with Django admin.
"""

# Import academic admin to register models
from apps.school.academic import admin as academic_admin

__all__ = ['academic_admin']

