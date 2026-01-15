"""Views for schedule module."""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from apps.common.permissions import HasBranchRole, get_branch_id_from_jwt
from apps.common.mixins import AuditTrailMixin
from apps.school.academic.models import AcademicYear, Quarter
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
        queryset = LessonInstance.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'class_subject', 'class_subject__class_obj',
            'class_subject__subject', 'class_subject__teacher',
            'room', 'topic'
        )
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset
    
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
            OpenApiParameter('date', type=str, description='Filter by exact date (YYYY-MM-DD)'),
            OpenApiParameter('date_from', type=str, description='Filter by start date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', type=str, description='Filter by end date (YYYY-MM-DD)'),
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


# ========== Current Timetable View ==========

@extend_schema(
    summary="Get or create current timetable template",
    description="""
    Joriy aktiv chorak uchun timetable template olish yoki yaratish.
    
    GET: Joriy aktiv chorak uchun aktiv template qaytaradi. Agar yo'q bo'lsa 404.
    POST: Joriy aktiv chorak uchun template yaratadi (agar mavjud bo'lsa, mavjud templateni qaytaradi).
    
    Branch ID JWT tokendan olinadi (br claim).
    """,
    responses={
        200: TimetableTemplateSerializer,
        201: TimetableTemplateSerializer,
        404: {'description': 'Aktiv akademik yil yoki chorak topilmadi'},
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def get_or_create_current_timetable(request):
    """
    Get or create current timetable template for current active quarter.
    Branch ID is extracted from JWT token.
    """
    # Get branch_id from JWT token
    
    branch_id = get_branch_id_from_jwt(request)

    if not branch_id:
        return Response({
            "error": "Branch id not found"
        })
    
    # Check if user has permission (admin for POST, read for GET)
    if request.method == 'POST':
        if not hasattr(request.user, 'branch_memberships'):
            return Response(
                {'error': 'Foydalanuvchi filialga a\'zo emas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        membership = request.user.branch_memberships.filter(
            branch_id=branch_id,
            role__in=['branch_admin', 'super_admin']
        ).first()
        
        if not membership:
            return Response(
                {'error': 'Faqat adminlar yangi template yaratishi mumkin.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Get active academic year
    academic_year = AcademicYear.objects.filter(
        branch_id=branch_id,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not academic_year:
        return Response(
            {'error': 'Aktiv akademik yil topilmadi. Iltimos, avval akademik yil yarating.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get current active quarter
    quarter = Quarter.objects.filter(
        academic_year=academic_year,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    # If no active quarter, try to find quarter by current date
    if not quarter:
        today = timezone.now().date()
        quarter = Quarter.objects.filter(
            academic_year=academic_year,
            start_date__lte=today,
            end_date__gte=today,
            deleted_at__isnull=True
        ).first()
    
    if not quarter:
        return Response(
            {'error': 'Joriy chorak topilmadi. Iltimos, choraklar sozlamalarini tekshiring.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Try to get existing template for this quarter
    template = TimetableTemplate.objects.filter(
        branch_id=branch_id,
        academic_year=academic_year,
        is_active=True,
        effective_from__lte=quarter.end_date,
        deleted_at__isnull=True
    ).filter(
        Q(effective_until__gte=quarter.start_date) | Q(effective_until__isnull=True)
    ).first()
    
    if request.method == 'GET':
        if not template:
            return Response(
                {
                    'error': 'Joriy chorak uchun aktiv template topilmadi.',
                    'quarter': {
                        'id': str(quarter.id),
                        'name': quarter.name,
                        'number': quarter.number,
                        'start_date': quarter.start_date.isoformat(),
                        'end_date': quarter.end_date.isoformat(),
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TimetableTemplateSerializer(template)
        return Response(serializer.data)
    
    # POST - create if not exists
    if template:
        # Template already exists, return it
        serializer = TimetableTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Create new template
    template_name = f"{quarter.name} - {academic_year.name}"
    template = TimetableTemplate.objects.create(
        branch_id=branch_id,
        academic_year=academic_year,
        name=template_name,
        description=f"Avtomatik yaratilgan jadval - {quarter.name}",
        is_active=True,
        effective_from=quarter.start_date,
        effective_until=quarter.end_date,
        created_by=request.user
    )
    
    serializer = TimetableTemplateSerializer(template)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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


# ========== Schedule Availability View ==========

class ScheduleAvailabilityView(generics.GenericAPIView):
    """
    Check available subjects and rooms for scheduling a lesson.
    
    Returns available subjects (assigned to the class) and rooms 
    that don't have conflicts at the specified date and time.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin', 'teacher')
    
    @extend_schema(
        summary="Check schedule availability",
        description="""
        Berilgan sinf, sana va vaqt uchun mavjud fanlar va xonalarni tekshiradi.
        
        Query parameters:
        - class_id: Sinf ID (required)
        - date: Sana (YYYY-MM-DD format, required)  
        - start_time: Boshlanish vaqti (HH:MM format, required)
        - end_time: Tugash vaqti (HH:MM format, required)
        
        Qaytaradi:
        - available_subjects: Ushbu sinfga biriktirilgan va konflikt bo'lmagan fanlar
        - available_rooms: Filialdagi va konflikt bo'lmagan xonalar
        - conflicts: Topilgan konfliktlar (agar bo'lsa)
        """,
        parameters=[
            OpenApiParameter('class_id', type=str, required=True, description='Sinf UUID'),
            OpenApiParameter('date', type=str, required=True, description='Sana (YYYY-MM-DD)'),
            OpenApiParameter('start_time', type=str, required=True, description='Boshlanish vaqti (HH:MM)'),
            OpenApiParameter('end_time', type=str, required=True, description='Tugash vaqti (HH:MM)'),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'available_subjects': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'subject_name': {'type': 'string'},
                                'teacher_name': {'type': 'string'},
                                'teacher_id': {'type': 'string'}
                            }
                        }
                    },
                    'available_rooms': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'name': {'type': 'string'},
                                'capacity': {'type': 'integer'}
                            }
                        }
                    },
                    'conflicts': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'type': {'type': 'string'},
                                'message': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request, branch_id):
        """Check availability for scheduling a lesson."""
        from apps.school.subjects.models import ClassSubject
        from apps.school.rooms.models import Room
        
        # Validate required parameters
        class_id = request.query_params.get('class_id')
        date_str = request.query_params.get('date')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        
        if not all([class_id, date_str, start_time_str, end_time_str]):
            return Response(
                {'error': 'class_id, date, start_time, end_time parametrlari majburiy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date and times
        try:
            from datetime import datetime, date, time
            check_date = date.fromisoformat(date_str)
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)
        except ValueError as e:
            return Response(
                {'error': f'Sana yoki vaqt formati noto\'g\'ri: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get class
        from apps.school.classes.models import Class
        try:
            class_obj = Class.objects.get(
                id=class_id,
                branch_id=branch_id,
                deleted_at__isnull=True
            )
        except (Class.DoesNotExist, ValidationError):
            return Response(
                {'error': 'Sinf topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all subjects assigned to this class
        class_subjects = ClassSubject.objects.filter(
            class_obj=class_obj,
            deleted_at__isnull=True
        ).select_related('subject', 'teacher')
        
        # Get all rooms in the branch
        rooms = Room.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        )
        
        available_subjects = []
        available_rooms = []
        all_conflicts = []
        
        # Check subject availability (teacher conflicts)
        for class_subject in class_subjects:
            # Create a mock lesson instance to check conflicts
            mock_lesson = LessonInstance(
                class_subject=class_subject,
                date=check_date,
                start_time=start_time,
                end_time=end_time,
                status=LessonStatus.PLANNED
            )
            
            conflicts = ScheduleConflictDetector.check_lesson_conflicts(mock_lesson)
            
            if not conflicts:
                available_subjects.append({
                    'id': str(class_subject.id),
                    'subject_name': class_subject.subject.name,
                    'teacher_name': class_subject.teacher.user.get_full_name() or class_subject.teacher.user.phone_number,
                    'teacher_id': str(class_subject.teacher.id)
                })
            else:
                all_conflicts.extend(conflicts)
        
        # Check room availability
        for room in rooms:
            # Create a mock lesson instance to check conflicts
            # Use first class_subject for room conflict check (doesn't matter which)
            if class_subjects.exists():
                mock_lesson = LessonInstance(
                    class_subject=class_subjects.first(),
                    date=check_date,
                    start_time=start_time,
                    end_time=end_time,
                    room=room,
                    status=LessonStatus.PLANNED
                )
                
                conflicts = ScheduleConflictDetector.check_lesson_conflicts(mock_lesson)
                room_conflicts = [c for c in conflicts if c['type'] == 'room']
                
                if not room_conflicts:
                    available_rooms.append({
                        'id': str(room.id),
                        'name': room.name,
                        'capacity': room.capacity
                    })
                else:
                    all_conflicts.extend(room_conflicts)
        
        return Response({
            'available_subjects': available_subjects,
            'available_rooms': available_rooms,
            'conflicts': [
                {
                    'type': c['type'],
                    'message': c['message'],
                    'details': c.get('details', {})
                } for c in all_conflicts
            ]
        })
