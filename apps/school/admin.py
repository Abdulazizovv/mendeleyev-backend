"""
School module admin configuration.

This file imports all admin configurations from submodules
to ensure they are registered with Django admin.
"""

# Import academic admin to register models
from apps.school.academic import admin as academic_admin
# Import classes admin to register models
from apps.school.classes import admin as classes_admin
# Import subjects admin to register models
from apps.school.subjects import admin as subjects_admin
# Import rooms admin to register models
from apps.school.rooms import admin as rooms_admin

__all__ = ['academic_admin', 'classes_admin', 'subjects_admin', 'rooms_admin']

