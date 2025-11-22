"""
Expose BranchMembership at package level without importing models during app
registry population to avoid AppRegistryNotReady. Accessing
`apps.branch.BranchMembership` will lazily import from `.models`.
"""

from typing import TYPE_CHECKING

__all__ = ["BranchMembership"]

if TYPE_CHECKING:  # type-hint friendly import
	from .models import BranchMembership as BranchMembership
else:
	def __getattr__(name: str):
		if name == "BranchMembership":
			from .models import BranchMembership as _BranchMembership
			return _BranchMembership
		raise AttributeError(name)
