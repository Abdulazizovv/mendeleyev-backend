from __future__ import annotations

from typing import Iterable, Optional
from uuid import UUID

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission


def _parse_uuid(value: str) -> Optional[str]:
    try:
        UUID(str(value))
        return str(value)
    except Exception:
        return None


class IsSuperAdmin(BasePermission):
    message = _("Super admin permissions required.")

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_superuser)


class HasBranchRole(BasePermission):
    """
    Checks that the user has a membership in the specified branch with one of the allowed roles.
    
    Branch context resolution order:
    - HTTP header: X-Branch-Id (UUID)
    - Query param: branch_id
    - View.kwargs: 'branch_id'
    
    Configure allowed roles on a view via 'required_branch_roles = ("teacher", "branch_admin")'.
    """

    message = _("You don't have permission for this branch.")
    header_name = "HTTP_X_BRANCH_ID"
    param_name = "branch_id"
    kwarg_name = "branch_id"

    def _get_branch_id(self, request, view) -> Optional[str]:
        """Resolve branch from JWT 'br' claim first, then header, param, kwarg."""
        # JWT claim (if SimpleJWT payload attached on request.user or request.auth)
        try:
            if hasattr(request, "auth") and isinstance(request.auth, dict):
                br_claim = request.auth.get("br") or request.auth.get("branch_id")
                uid = _parse_uuid(br_claim) if br_claim else None
                if uid:
                    return uid
        except Exception:
            pass
        # Header takes precedence afterwards
        header_val = request.META.get(self.header_name)
        if header_val:
            uid = _parse_uuid(header_val)
            if uid:
                return uid
        # Query param next
        param_val = request.query_params.get(self.param_name)
        if param_val:
            uid = _parse_uuid(param_val)
            if uid:
                return uid
        # Kwarg last
        kw = getattr(view, "kwargs", {}) or {}
        kw_val = kw.get(self.kwarg_name)
        if kw_val:
            uid = _parse_uuid(kw_val)
            if uid:
                return uid
        return None

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        # Super admin bypasses branch checks
        if user.is_superuser:
            return True

        # Determine branch context
        branch_id = self._get_branch_id(request, view)
        if not branch_id:
            # If view doesn't require a branch (no required roles), allow
            roles: Optional[Iterable[str]] = getattr(view, "required_branch_roles", None)
            return roles in (None, (), [], set())

        # Evaluate membership and role
        try:
            from auth.users.models import UserBranch
            roles = getattr(view, "required_branch_roles", None)
            if roles:
                return UserBranch.has_role(user.id, branch_id, list(roles))
            # Any membership
            return UserBranch.has_role(user.id, branch_id, None)
        except Exception:
            return False
