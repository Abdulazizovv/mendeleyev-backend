from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _
from apps.branch.models import BranchMembership, BranchRole
from apps.school.classes.models import Class


class CanCreateStudent(BasePermission):
    """O'quvchi yaratish huquqini tekshirish.
    
    Quyidagi rollarga ega foydalanuvchilar o'quvchi yaratishi mumkin:
    - super_admin
    - branch_admin (faqat o'z filialida)
    - teacher (faqat o'z sinfida sinf rahbar bo'lsa)
    """
    
    message = _("O'quvchi yaratish uchun ruxsat yo'q.")
    
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        
        # Super admin har doim yaratishi mumkin
        if user.is_superuser:
            return True
        
        # Branch ID ni olish
        branch_id = self._get_branch_id(request, view)
        if not branch_id:
            return False
        
        # Branch admin tekshirish
        if BranchMembership.has_role(user.id, branch_id, [BranchRole.BRANCH_ADMIN]):
            return True
        
        # Sinf rahbar tekshirish (agar class_id berilgan bo'lsa)
        class_id = request.data.get('class_id') or view.kwargs.get('class_id')
        if class_id:
            try:
                class_obj = Class.objects.get(id=class_id, deleted_at__isnull=True)
                # Sinf rahbar tekshirish
                if class_obj.class_teacher and class_obj.class_teacher.user_id == user.id:
                    # Sinf va branch bir xil bo'lishi kerak
                    if str(class_obj.branch_id) == str(branch_id):
                        return True
            except Class.DoesNotExist:
                pass
        
        return False
    
    def _get_branch_id(self, request, view):
        """Branch ID ni olish."""
        from uuid import UUID
        
        # JWT claim
        if hasattr(request, "auth") and isinstance(request.auth, dict):
            br_claim = request.auth.get("br") or request.auth.get("branch_id")
            if br_claim:
                try:
                    return str(UUID(str(br_claim)))
                except:
                    pass
        
        # Header
        branch_id = request.META.get("HTTP_X_BRANCH_ID")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        # Query param
        branch_id = request.query_params.get("branch_id")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        # Request data
        branch_id = request.data.get("branch_id")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        # View kwargs
        branch_id = view.kwargs.get("branch_id")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        return None

