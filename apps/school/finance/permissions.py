"""
Moliya tizimi uchun permissions.
"""
from rest_framework.permissions import BasePermission
from apps.branch.models import BranchMembership, BranchRole


class FinancePermissions:
    """Moliya bo'yicha ruxsatlar ro'yxati."""
    
    VIEW_FINANCE = 'view_finance'
    MANAGE_FINANCE = 'manage_finance'
    CREATE_TRANSACTIONS = 'create_transactions'
    EDIT_TRANSACTIONS = 'edit_transactions'
    DELETE_TRANSACTIONS = 'delete_transactions'
    VIEW_REPORTS = 'view_reports'
    EXPORT_DATA = 'export_data'
    MANAGE_CATEGORIES = 'manage_categories'
    MANAGE_CASH_REGISTERS = 'manage_cash_registers'


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
        
        try:
            # Agar branch_id berilgan bo'lsa, o'sha filial uchun membership
            if branch_id:
                membership = BranchMembership.objects.filter(
                    user=request.user,
                    branch_id=branch_id,
                    deleted_at__isnull=True
                ).first()
            else:
                # Aks holda birinchi faol membership
                membership = BranchMembership.objects.filter(
                    user=request.user,
                    deleted_at__isnull=True
                ).first()
            
            if not membership:
                return False
            
            # Super admin barcha filiallarga kirishga ruxsat
            if membership.role == BranchRole.SUPER_ADMIN:
                return True
            
            # Branch admin o'z filialiga ruxsat
            if membership.role == BranchRole.BRANCH_ADMIN:
                if branch_id and str(membership.branch_id) == str(branch_id):
                    return True
                # Branch ID yo'q bo'lsa ham ruxsat (o'z filialini oladi)
                if not branch_id:
                    return True
            
            # Role orqali moliya ruxsatini tekshirish
            if hasattr(membership, 'role_model') and membership.role_model:
                permissions = membership.role_model.permissions or {}
                
                # Read operatsiyalari uchun
                if request.method in ['GET', 'HEAD', 'OPTIONS']:
                    if permissions.get(FinancePermissions.VIEW_FINANCE):
                        return True
                
                # Write operatsiyalari uchun
                if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    if permissions.get(FinancePermissions.MANAGE_FINANCE):
                        return True
                    
                    # Granular permissions
                    if request.method == 'POST' and permissions.get(FinancePermissions.CREATE_TRANSACTIONS):
                        return True
                    if request.method in ['PUT', 'PATCH'] and permissions.get(FinancePermissions.EDIT_TRANSACTIONS):
                        return True
                    if request.method == 'DELETE' and permissions.get(FinancePermissions.DELETE_TRANSACTIONS):
                        return True
            
        except BranchMembership.DoesNotExist:
            pass
        
        return False


class CanViewFinanceReports(BasePermission):
    """Moliya hisobotlarini ko'rish ruxsati."""
    
    def has_permission(self, request, view):
        """Ruxsat tekshiruvi."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            membership = BranchMembership.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()
            
            if not membership:
                return False
            
            # Super admin va branch admin har doim ko'ra oladi
            if membership.role in [BranchRole.SUPER_ADMIN, BranchRole.BRANCH_ADMIN]:
                return True
            
            # Role orqali tekshirish
            if membership.role_model:
                permissions = membership.role_model.permissions or {}
                return permissions.get(FinancePermissions.VIEW_REPORTS, False)
        
        except BranchMembership.DoesNotExist:
            pass
        
        return False


class CanManageCategories(BasePermission):
    """Kategoriyalarni boshqarish ruxsati."""
    
    def has_permission(self, request, view):
        """Ruxsat tekshiruvi."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # GET uchun CanManageFinance ishlatiladi
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        try:
            membership = BranchMembership.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()
            
            if not membership:
                return False
            
            # Super admin va branch admin boshqara oladi
            if membership.role in [BranchRole.SUPER_ADMIN, BranchRole.BRANCH_ADMIN]:
                return True
            
            # Role orqali tekshirish
            if membership.role_model:
                permissions = membership.role_model.permissions or {}
                return permissions.get(FinancePermissions.MANAGE_CATEGORIES, False)
        
        except BranchMembership.DoesNotExist:
            pass
        
        return False

