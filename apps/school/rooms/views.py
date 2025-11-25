from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404

from apps.branch.models import Branch
from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import Building, Room
from .serializers import (
    BuildingSerializer,
    BuildingCreateSerializer,
    RoomSerializer,
    RoomCreateSerializer,
)


class BuildingListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Binolar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    
    def get_queryset(self):
        """Filial bo'yicha binolarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Building.objects.filter(branch=branch).prefetch_related('rooms')
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BuildingCreateSerializer
        return BuildingSerializer
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Binolar ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi bino yaratish",
        request=BuildingCreateSerializer,
        responses={201: BuildingSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BuildingDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Bino detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = BuildingSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return Building.objects.filter(branch=branch).prefetch_related('rooms')
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Bino detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Binoni yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Binoni o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class RoomListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Xonalar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    
    def get_queryset(self):
        """Filial bo'yicha xonalarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Room.objects.filter(branch=branch).select_related('building')
        
        # Filter by building if provided
        building_id = self.request.query_params.get('building_id')
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        
        # Filter by room_type if provided
        room_type = self.request.query_params.get('room_type')
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoomCreateSerializer
        return RoomSerializer
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Xonalar ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('building_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('room_type', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi xona yaratish",
        request=RoomCreateSerializer,
        responses={201: RoomSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RoomDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Xona detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = RoomSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return Room.objects.filter(branch=branch).select_related('building')
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Xona detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Xonani yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Xonani o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

