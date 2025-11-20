"""
Common mixins for views and models.
"""

from rest_framework import status
from rest_framework.response import Response


class AuditTrailMixin:
	"""Mixin to automatically set created_by and updated_by fields.
	
	Usage in views:
		class MyView(AuditTrailMixin, CreateAPIView):
			...
	
	This mixin automatically sets created_by and updated_by when saving models.
	"""
	
	def perform_create(self, serializer):
		"""Set created_by and updated_by on create."""
		if hasattr(serializer, 'save'):
			serializer.save(
				created_by=self.request.user if hasattr(self.request, 'user') else None,
				updated_by=self.request.user if hasattr(self.request, 'user') else None,
			)
		else:
			super().perform_create(serializer)
	
	def perform_update(self, serializer):
		"""Set updated_by on update."""
		if hasattr(serializer, 'save'):
			serializer.save(
				updated_by=self.request.user if hasattr(self.request, 'user') else None,
			)
		else:
			super().perform_update(serializer)

