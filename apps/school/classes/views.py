from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404

from apps.branch.models import Branch, BranchMembership
from apps.school.academic.models import AcademicYear
from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import Class, ClassStudent
from .serializers import (
    ClassSerializer,
    ClassCreateSerializer,
    ClassStudentSerializer,
    ClassStudentCreateSerializer,
    ClassStudentTransferSerializer,
)
from .filters import ClassFilter, ClassStudentFilter


class ClassListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinflar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClassFilter
    search_fields = ['name', 'class_teacher__user__first_name', 'class_teacher__user__last_name']
    ordering_fields = ['name', 'grade_level', 'created_at', 'academic_year__start_date']
    ordering = ['grade_level']
    
    def get_queryset(self):
        """Filial va akademik yil bo'yicha sinflarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Class.objects.filter(branch=branch, deleted_at__isnull=True).select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user',
            'room'
        ).prefetch_related('class_students__membership__user').order_by('grade_level', 'section', 'name')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassCreateSerializer
        return ClassSerializer
    
    def create(self, request, *args, **kwargs):
        """Create with ClassCreateSerializer, return with ClassSerializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return response using ClassSerializer
        instance = serializer.instance
        output_serializer = ClassSerializer(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Sinflar ro'yxati",
        description="""
        Sinflar ro'yxati (paginatsiya, qidiruv, filter va ordering bilan).
        
        Query parameters:
        - page: Sahifa raqami (default: 1)
        - page_size: Sahifadagi elementlar soni (default: 20, max: 100)
        - search: Qidirish (nomi, sinf rahbari)
        - ordering: Tartiblash (masalan: name, -name, grade_level, -grade_level)
        - academic_year_id: Akademik yil ID bo'yicha filter
        - grade_level: Sinf darajasi bo'yicha filter
        - section: Bo'lim bo'yicha filter
        - is_active: Faol sinflar bo'yicha filter
        - class_teacher_id: Sinf rahbari ID bo'yicha filter
        - room_id: Xona ID bo'yicha filter
        """,
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('academic_year_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('grade_level', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi sinf yaratish",
        request=ClassCreateSerializer,
        responses={201: ClassSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ClassDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Sinf detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return Class.objects.filter(branch=branch, deleted_at__isnull=True).select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user'
        ).prefetch_related('class_students__membership__user')
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Sinf detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfni yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfni o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ClassAvailableStudentsView(generics.ListAPIView):
    """Berilgan sinf uchun mavjud (hali hech qaysi sinfga biriktirilmagan) o'quvchilar ro'yxati.

    Filial va sinf beriladi, natijada shu filialdagi student roli bo'lgan
    a'zoliklar ichidan hech qaysi sinfga kiritilmaganlar qaytariladi.
    """

    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = ClassStudentSerializer  # we will return membership info via this serializer's nested fields
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__phone_number',
        'title',
    ]
    ordering_fields = ['created_at', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']

    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        class_id = self.kwargs.get('class_id')
        branch = get_object_or_404(Branch, id=branch_id)
        class_obj = get_object_or_404(Class, id=class_id, branch=branch, deleted_at__isnull=True)

        # All student memberships in branch
        students_qs = BranchMembership.objects.filter(
            branch=branch,
            role='student',
            deleted_at__isnull=True
        ).select_related('user', 'branch')

        # Exclude those already enrolled in any class in the branch
        enrolled_ids = ClassStudent.objects.filter(
            class_obj__branch=branch,
            deleted_at__isnull=True
        ).values_list('membership_id', flat=True)

        available = students_qs.exclude(id__in=enrolled_ids)
        # We need to return items that the serializer can handle; reuse BranchMembership via a lightweight serializer
        return available

    def get_serializer_class(self):
        # Use BranchMembershipDetailSerializer to represent student candidates cleanly
        from apps.branch.serializers import BranchMembershipDetailSerializer
        return BranchMembershipDetailSerializer

    @extend_schema(
        summary="Sinfga qo'shish uchun mavjud o'quvchilar",
        description="Berilgan filial va sinf uchun hali sinfga kiritilmagan student a'zoliklari ro'yxati.",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ClassStudentListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinf o'quvchilari ro'yxati va qo'shish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = ClassStudentSerializer
    filterset_class = ClassStudentFilter
    search_fields = [
        'membership__user__first_name',
        'membership__user__last_name',
        'membership__user__phone_number',
    ]
    ordering_fields = ['created_at', 'membership__user__first_name', 'membership__user__last_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Sinf o'quvchilarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id, deleted_at__isnull=True)
        
        queryset = ClassStudent.objects.filter(
            class_obj=class_obj,
            deleted_at__isnull=True
        ).select_related(
            'membership',
            'membership__user',
            'class_obj'
        )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassStudentCreateSerializer
        return ClassStudentSerializer
    
    def get_serializer_context(self):
        """Add class_obj to serializer context."""
        context = super().get_serializer_context()
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        context['class_obj'] = class_obj
        return context
    
    def perform_create(self, serializer):
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        serializer.save(class_obj=class_obj, created_by=self.request.user)
    
    @extend_schema(
        summary="Sinf o'quvchilari ro'yxati",
        description="""
        Sinf o'quvchilari ro'yxati (paginatsiya, qidiruv, filter va ordering bilan).
        
        Query parameters:
        - page: Sahifa raqami (default: 1)
        - page_size: Sahifadagi elementlar soni (default: 20, max: 100)
        - search: Qidirish (ism, telefon)
        - ordering: Tartiblash (masalan: created_at, -created_at)
        - is_active: Faol o'quvchilar bo'yicha filter
        """,
        parameters=[
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchi qo'shish",
        request=ClassStudentCreateSerializer,
        responses={201: ClassStudentSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ClassStudentDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Sinf o'quvchisi detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassStudentSerializer
    lookup_url_kwarg = 'student_id'
    
    def get_queryset(self):
        """Sinf o'quvchilarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id, deleted_at__isnull=True)
        return ClassStudent.objects.filter(class_obj=class_obj, deleted_at__isnull=True).select_related(
            'membership',
            'membership__user',
            'class_obj'
        )
    
    def get_object(self):
        """O'quvchini URLdagi ID orqali topadi.

        URLdagi `{student_id}` quyidagilardan biri bo'lishi mumkin:
        - `membership_id` (afzal va aniq identifikator)
        - `user_id` (o'quvchi foydalanuvchi ID)

        Avval membership_id bo'yicha qidiradi, topilmasa user_id bo'yicha urinadi.
        """
        queryset = self.get_queryset()
        student_id = self.kwargs.get('student_id')
        # Try membership_id first
        obj = queryset.filter(membership_id=student_id).first()
        if obj:
            return obj
        # Fallback: try user_id
        obj = queryset.filter(membership__user_id=student_id).first()
        if obj:
            return obj
        # Not found
        raise get_object_or_404(queryset, membership_id=student_id)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="O'quvchi detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchini yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchini olib tashlash",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ClassStudentTransferView(AuditTrailMixin, generics.GenericAPIView):
    """O'quvchini bir sinfdan boshqasiga transfer qilish."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassStudentTransferSerializer

    def post(self, request, *args, **kwargs):
        from_class_id = self.kwargs.get('class_id')
        student_membership_id = self.kwargs.get('student_id')

        from_class = get_object_or_404(Class, id=from_class_id, deleted_at__isnull=True)
        class_student = get_object_or_404(
            ClassStudent,
            class_obj_id=from_class_id,
            membership_id=student_membership_id,
            deleted_at__isnull=True,
        )

        serializer = self.get_serializer(data=request.data, context={
            'request': request,
            'from_class': from_class,
            'class_student': class_student,
        })
        serializer.is_valid(raise_exception=True)
        target_class = serializer.validated_data['target_class']
        enrollment_date = serializer.validated_data.get('enrollment_date')
        notes = serializer.validated_data.get('notes')

        # Soft-delete old enrollment and create new enrollment
        class_student.delete()  # AuditTrailMixin handles soft-delete

        new_enrollment = ClassStudent.objects.create(
            class_obj=target_class,
            membership=class_student.membership,
            enrollment_date=enrollment_date or class_student.enrollment_date,
            is_active=class_student.is_active,
            notes=notes or class_student.notes,
            created_by=request.user,
        )

        output = ClassStudentSerializer(new_enrollment)
        return Response(output.data, status=status.HTTP_201_CREATED)

