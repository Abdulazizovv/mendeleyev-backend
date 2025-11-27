"""
Moliya tizimi uchun permissions.
"""
from rest_framework.permissions import BasePermission
from apps.branch.models import BranchMembership, BranchRole


class CanManageFinance(BasePermission):
    """Moliya tizimini boshqarish ruxsati.
    
    Super admin, branch admin yoki moliya bo'yicha ruxsati bo'lgan xodimlar
    moliya tizimini boshqarishi mumkin.
    """
    
    def has_permission(self, request, view):
        """Umumiy ruxsat tekshiruvi."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin har doim ruxsatga ega
        if request.user.is_superuser:
            return True
        
        # Branch ID ni olish
        branch_id = view._get_branch_id() if hasattr(view, '_get_branch_id') else None
        if not branch_id:
            return False
        
        # Branch admin yoki moliya bo'yicha ruxsati bo'lgan xodim
        has_role = BranchMembership.has_role(
            request.user.id,
            branch_id,
            [BranchRole.BRANCH_ADMIN, BranchRole.SUPER_ADMIN]
        )
        
        if has_role:
            return True
        
        # TODO: Role model orqali moliya ruxsatini tekshirish
        # Hozircha branch admin va super admin uchun ruxsat beramiz
        
        return False

