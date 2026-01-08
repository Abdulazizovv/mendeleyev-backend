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
    

def get_branch_id_from_jwt(request):
    """Extract branch_id from JWT token (supports multiple token formats)."""
    try:
        if hasattr(request, "auth") and request.auth:
            br_claim = None
            # Token obyekti bo'lsa (AccessToken, UntypedToken) - .payload ishlatamiz
            if hasattr(request.auth, "payload") and isinstance(request.auth.payload, dict):
                br_claim = request.auth.payload.get("br") or request.auth.payload.get("branch_id")
            # Dict bo'lsa (test yoki force_authenticate)
            elif isinstance(request.auth, dict):
                br_claim = request.auth.get("br") or request.auth.get("branch_id")
            # Token mapping interface
            elif hasattr(request.auth, "get"):
                br_claim = request.auth.get("br") or request.auth.get("branch_id")
            # Last resort: direct indexing
            else:
                try:
                    br_claim = request.auth["br"]
                except:
                    pass
                    
            uid = _parse_uuid(br_claim) if br_claim else None
            if uid:
                return uid
    except Exception:
        pass
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
        """Resolve branch context preferring explicit request scope over token claims.

        Order: kwarg 'branch_id' -> header X-Branch-Id -> query param branch_id -> JWT 'br' claim.
        """
        # URL kwarg has the highest priority (most explicit)
        kw = getattr(view, "kwargs", {}) or {}
        kw_val = kw.get(self.kwarg_name)
        if kw_val:
            uid = _parse_uuid(kw_val)
            if uid:
                return uid
        # Header next
        header_val = request.META.get(self.header_name)
        if header_val:
            uid = _parse_uuid(header_val)
            if uid:
                return uid
        # Query param next
        param_val = getattr(request, "query_params", {}).get(self.param_name) if hasattr(request, "query_params") else None
        if param_val:
            uid = _parse_uuid(param_val)
            if uid:
                return uid
        # Infer from other route params (e.g., class_id -> Class.branch_id)
        try:
            kw_all = getattr(view, "kwargs", {}) or {}
            class_id = kw_all.get("class_id")
            if class_id:
                # Local import to avoid circular
                from apps.school.classes.models import Class  # type: ignore
                uid = _parse_uuid(class_id)
                if uid:
                    cls = Class.objects.filter(id=uid).only("branch_id").first()
                    if cls:
                        return str(cls.branch_id)
        except Exception:
            pass
        # JWT claim as fallback (least explicit but convenient default)
        try:
            if hasattr(request, "auth") and request.auth:
                br_claim = None
                # Token obyekti bo'lsa (AccessToken, UntypedToken)
                if hasattr(request.auth, "payload") and isinstance(request.auth.payload, dict):
                    br_claim = request.auth.payload.get("br") or request.auth.payload.get("branch_id")
                # Dict bo'lsa (test yoki force_authenticate)
                elif isinstance(request.auth, dict):
                    br_claim = request.auth.get("br") or request.auth.get("branch_id")
                # Token mapping interface
                elif hasattr(request.auth, "get"):
                    br_claim = request.auth.get("br") or request.auth.get("branch_id")
                # Last resort: direct indexing
                else:
                    try:
                        br_claim = request.auth["br"]
                    except:
                        pass
                        
                uid = _parse_uuid(br_claim) if br_claim else None
                if uid:
                    return uid
        except Exception:
            pass
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
            # If neither permission nor view declares required roles, allow
            roles: Optional[Iterable[str]] = getattr(self, "required_branch_roles", None)
            if roles is None:
                roles = getattr(view, "required_branch_roles", None)
            return roles in (None, (), [], set())

        # Evaluate membership and role
        try:
            from apps.branch.models import BranchMembership
            # Prefer permission's intrinsic roles (wrappers) over view-level roles
            roles = getattr(self, "required_branch_roles", None)
            if roles is None:
                roles = getattr(view, "required_branch_roles", None)
            if roles:
                return BranchMembership.has_role(user.id, branch_id, list(roles))
            # Any membership
            return BranchMembership.has_role(user.id, branch_id, None)
        except Exception:
            return False


class IsTeacher(HasBranchRole):
    """Allows access if the user has the 'teacher' role for the resolved branch."""
    required_branch_roles = ("teacher",)


class IsStudent(HasBranchRole):
    """Allows access if the user has the 'student' role for the resolved branch."""
    required_branch_roles = ("student",)


class IsBranchAdmin(HasBranchRole):
    """Allows access if the user has the 'branch_admin' role for the resolved branch."""
    required_branch_roles = ("branch_admin",)
