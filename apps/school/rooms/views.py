from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
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
from .filters import BuildingFilter, RoomFilter


class BuildingListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Binolar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BuildingFilter
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filial bo'yicha binolarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Building.objects.filter(branch=branch, deleted_at__isnull=True).prefetch_related('rooms')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BuildingCreateSerializer
        return BuildingSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        branch_id = self.kwargs.get('branch_id')
        if branch_id:
            branch = get_object_or_404(Branch, id=branch_id)
            context['branch'] = branch
        return context
    
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
        return Building.objects.filter(branch=branch, deleted_at__isnull=True).prefetch_related('rooms')
    
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    search_fields = ['name', 'number']
    ordering_fields = ['name', 'number', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filial bo'yicha xonalarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Room.objects.filter(branch=branch, deleted_at__isnull=True).select_related('building')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoomCreateSerializer
        return RoomSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        branch_id = self.kwargs.get('branch_id')
        if branch_id:
            branch = get_object_or_404(Branch, id=branch_id)
            context['branch'] = branch
        return context
    
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
        return Room.objects.filter(branch=branch, deleted_at__isnull=True).select_related('building')
    
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

