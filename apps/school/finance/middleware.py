"""
Moliya tizimi middleware.
"""
from uuid import UUID
from apps.branch.models import BranchMembership, BranchRole


class BranchIsolationMiddleware:
    """
    Branch isolation middleware.
    
    Har bir request uchun branch_id ni aniqlaydi va requestga qo'shadi.
    Super admin barcha filiallarga kirishga ruxsat.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Request processing."""
        # Faqat authenticated userlar uchun
        if request.user and request.user.is_authenticated:
            branch_id = self._extract_branch_id(request)
            
            # Super admin check
            is_super_admin = False
            try:
                # Agar branch_id berilgan bo'lsa, o'sha filial membership
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
                
                if membership:
                    is_super_admin = membership.role == BranchRole.SUPER_ADMIN
                    
                    # Agar branch_id kiritilmagan bo'lsa va super admin bo'lmasa
                    # Default branch ni o'rnatish
                    if not branch_id and not is_super_admin:
                        branch_id = str(membership.branch_id)
            
            except Exception:
                pass
            
            # Request objectga qo'shish
            request.branch_id = branch_id
            request.is_super_admin = is_super_admin
        else:
            request.branch_id = None
            request.is_super_admin = False
        
        response = self.get_response(request)
        return response
    
    def _extract_branch_id(self, request):
        """Branch ID ni olish."""
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
        branch_id = request.GET.get("branch_id")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        return None
