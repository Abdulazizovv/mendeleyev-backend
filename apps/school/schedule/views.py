"""Views for schedule module."""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Prefetch
from datetime import timedelta

from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import (
    TimetableTemplate, TimetableSlot, LessonInstance, 
    LessonTopic, DayOfWeek, LessonStatus
)
from .serializers import (
    TimetableTemplateSerializer, TimetableTemplateCreateSerializer,
    TimetableSlotSerializer, TimetableSlotCreateSerializer,
    TimetableSlotBulkCreateSerializer,
    LessonInstanceSerializer, LessonInstanceCreateSerializer,
    LessonInstanceUpdateSerializer,
    LessonTopicSerializer, LessonTopicCreateSerializer,
    LessonGenerationRequestSerializer, WeeklyScheduleSerializer
)
from .services import LessonGenerator, ScheduleConflictDetector


# ========== Timetable Template Views ==========

class TimetableTemplateListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create timetable templates.
    
    GET: List all templates for a branch
    POST: Create new template
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['effective_from', 'created_at', 'name']
    ordering = ['-effective_from']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return TimetableTemplate.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('branch', 'academic_year')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimetableTemplateCreateSerializer
        return TimetableTemplateSerializer
    
    @extend_schema(
        summary="List timetable templates",
        description="Get all timetable templates for a branch",
        responses={200: TimetableTemplateSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create timetable template",
        description="Create a new timetable template",
        request=TimetableTemplateCreateSerializer,
        responses={201: TimetableTemplateSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TimetableTemplateDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a timetable template.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    lookup_url_kwarg = 'template_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return TimetableTemplate.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('branch', 'academic_year')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TimetableTemplateCreateSerializer
        return TimetableTemplateSerializer
    
    @extend_schema(
        summary="Get timetable template details",
        responses={200: TimetableTemplateSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update timetable template",
        request=TimetableTemplateCreateSerializer,
        responses={200: TimetableTemplateSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete timetable template",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ========== Timetable Slot Views ==========

class TimetableSlotListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create timetable slots.
    
    GET: List all slots for a timetable
    POST: Create new slot
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['day_of_week', 'lesson_number', 'class_obj', 'room']
    ordering_fields = ['day_of_week', 'lesson_number', 'start_time']
    ordering = ['day_of_week', 'lesson_number']
    
    def get_queryset(self):
        template_id = self.kwargs.get('template_id')
        return TimetableSlot.objects.filter(
            timetable_id=template_id,
            deleted_at__isnull=True
        ).select_related(
            'class_obj', 'class_subject', 'class_subject__subject',
            'class_subject__teacher', 'room'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimetableSlotCreateSerializer
        return TimetableSlotSerializer
    
    @extend_schema(
        summary="List timetable slots",
        responses={200: TimetableSlotSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create timetable slot",
        request=TimetableSlotCreateSerializer,
        responses={201: TimetableSlotSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TimetableSlotDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a timetable slot.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    lookup_url_kwarg = 'slot_id'
    
    def get_queryset(self):
        template_id = self.kwargs.get('template_id')
        return TimetableSlot.objects.filter(
            timetable_id=template_id,
            deleted_at__isnull=True
        ).select_related('class_obj', 'class_subject', 'room')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TimetableSlotCreateSerializer
        return TimetableSlotSerializer


@extend_schema(
    summary="Bulk create timetable slots",
    request=TimetableSlotBulkCreateSerializer,
    responses={201: TimetableSlotSerializer(many=True)}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def bulk_create_slots(request, branch_id, template_id):
    """Bulk create timetable slots."""
    serializer = TimetableSlotBulkCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    slots = serializer.save()
    
    result_serializer = TimetableSlotSerializer(slots, many=True)
    return Response(result_serializer.data, status=status.HTTP_201_CREATED)


# ========== Lesson Topic Views ==========

class LessonTopicListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create lesson topics.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['subject', 'quarter']
    search_fields = ['title', 'description']
    ordering_fields = ['position', 'created_at']
    ordering = ['position']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonTopic.objects.filter(
            subject__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('subject', 'quarter')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonTopicCreateSerializer
        return LessonTopicSerializer
    
    def get_permissions(self):
        """Teachers can view, only admins can create/edit."""
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        else:
            self.required_branch_roles = ('branch_admin', 'super_admin')
        return super().get_permissions()


class LessonTopicDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a lesson topic.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    lookup_url_kwarg = 'topic_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonTopic.objects.filter(
            subject__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('subject', 'quarter')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LessonTopicCreateSerializer
        return LessonTopicSerializer
    
    def get_permissions(self):
        """Teachers can view, only admins can edit/delete."""
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        else:
            self.required_branch_roles = ('branch_admin', 'super_admin')
        return super().get_permissions()


# ========== Lesson Instance Views ==========

class LessonInstanceListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create lesson instances.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['class_subject', 'date', 'status', 'lesson_number']
    ordering_fields = ['date', 'lesson_number', 'start_time']
    ordering = ['date', 'lesson_number']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonInstance.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'class_subject', 'class_subject__class_obj',
            'class_subject__subject', 'class_subject__teacher',
            'room', 'topic'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonInstanceCreateSerializer
        return LessonInstanceSerializer
    
    def get_permissions(self):
        """Teachers and admins can view, admins can create."""
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        else:
            self.required_branch_roles = ('branch_admin', 'super_admin')
        return super().get_permissions()
    
    @extend_schema(
        summary="List lesson instances",
        parameters=[
            OpenApiParameter('date', type=str, description='Filter by date (YYYY-MM-DD)'),
            OpenApiParameter('class_subject', type=str, description='Filter by class subject ID'),
            OpenApiParameter('status', type=str, description='Filter by status'),
        ],
        responses={200: LessonInstanceSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LessonInstanceDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a lesson instance.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    lookup_url_kwarg = 'lesson_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonInstance.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('class_subject', 'room', 'topic')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LessonInstanceUpdateSerializer
        return LessonInstanceSerializer
    
    def get_permissions(self):
        """Teachers can view and update their lessons, admins can do everything."""
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        else:
            # For update/delete, check if teacher owns this lesson
            self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        return super().get_permissions()


# ========== Lesson Generation Views ==========

@extend_schema(
    summary="Generate lessons from timetable",
    description="Generate lesson instances from timetable template for a date range",
    request=LessonGenerationRequestSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'created_count': {'type': 'integer'},
                'skipped_count': {'type': 'integer'},
                'start_date': {'type': 'string'},
                'end_date': {'type': 'string'}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def generate_lessons(request, branch_id):
    """Generate lesson instances from timetable template."""
    # Only admins can generate lessons
    if not hasattr(request.user, 'branch_memberships'):
        return Response(
            {'error': 'User has no branch memberships'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    membership = request.user.branch_memberships.filter(
        branch_id=branch_id,
        role__in=['branch_admin', 'super_admin']
    ).first()
    
    if not membership:
        return Response(
            {'error': 'Permission denied. Admin role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = LessonGenerationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    data = serializer.validated_data
    timetable = TimetableTemplate.objects.get(id=data['timetable_id'])
    
    # Generate lessons
    created_count, skipped_count = LessonGenerator.generate_lessons_for_period(
        timetable=timetable,
        start_date=data['start_date'],
        end_date=data['end_date'],
        skip_existing=data['skip_existing']
    )
    
    return Response({
        'message': 'Darslar muvaffaqiyatli yaratildi',
        'created_count': created_count,
        'skipped_count': skipped_count,
        'start_date': str(data['start_date']),
        'end_date': str(data['end_date'])
    })


@extend_schema(
    summary="Get weekly schedule for a class",
    description="Get all lessons for a class for a specific week",
    parameters=[
        OpenApiParameter('class_id', type=str, required=True, description='Class UUID'),
        OpenApiParameter('week_start', type=str, required=True, description='Week start date (Monday, YYYY-MM-DD)'),
    ],
    responses={200: LessonInstanceSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBranchRole])
def weekly_schedule(request, branch_id):
    """Get weekly schedule for a class."""
    serializer = WeeklyScheduleSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    
    data = serializer.validated_data
    class_id = data['class_id']
    week_start = data['week_start']
    week_end = week_start + timedelta(days=6)
    
    # Get all lessons for the class for the week
    lessons = LessonInstance.objects.filter(
        class_subject__class_obj_id=class_id,
        class_subject__class_obj__branch_id=branch_id,
        date__gte=week_start,
        date__lte=week_end,
        deleted_at__isnull=True
    ).select_related(
        'class_subject', 'class_subject__subject',
        'class_subject__teacher', 'room', 'topic'
    ).order_by('date', 'lesson_number')
    
    result_serializer = LessonInstanceSerializer(lessons, many=True)
    return Response(result_serializer.data)


@extend_schema(
    summary="Check conflicts for a slot",
    description="Check if a timetable slot has conflicts",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'has_conflicts': {'type': 'boolean'},
                'conflicts': {'type': 'array'}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def check_slot_conflicts(request, branch_id, template_id, slot_id=None):
    """Check conflicts for a timetable slot."""
    # Get or create temporary slot
    if slot_id:
        slot = TimetableSlot.objects.get(id=slot_id)
    else:
        # Create temporary slot from request data
        serializer = TimetableSlotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = TimetableSlot(**serializer.validated_data)
    
    conflicts = ScheduleConflictDetector.check_slot_conflicts(
        slot, exclude_slot_id=slot_id
    )
    
    return Response({
        'has_conflicts': len(conflicts) > 0,
        'conflicts': [
            {
                'type': c['type'],
                'message': c['message'],
                'details': c.get('details', {})
            }
            for c in conflicts
        ]
    })
