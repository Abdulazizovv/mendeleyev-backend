"""
Filtering, search va ordering uchun filter classes.
"""
import django_filters
from django.db import models
from auth.profiles.models import StudentProfile, Gender, StudentStatus
from apps.branch.models import BranchRole


class StudentProfileFilter(django_filters.FilterSet):
    """O'quvchilar uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (shaxsiy raqam, ism, telefon)')
    personal_number = django_filters.CharFilter(field_name='personal_number', lookup_expr='icontains', help_text='Shaxsiy raqam bo\'yicha qidirish')
    
    # Filter fields
    gender = django_filters.ChoiceFilter(
        field_name='gender',
        choices=Gender.choices,
        help_text='Jinsi bo\'yicha filter (male, female, other, unspecified)'
    )
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=StudentStatus.choices,
        help_text='O\'quvchi holati bo\'yicha filter (active, archived, suspended, graduated, transferred)'
    )
    date_of_birth = django_filters.DateFilter(field_name='date_of_birth', help_text='Tu\'gilgan sana bo\'yicha filter')
    date_of_birth__gte = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='gte', help_text='Tu\'gilgan sana (dan)')
    date_of_birth__lte = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='lte', help_text='Tu\'gilgan sana (gacha)')
    
    # User fields
    first_name = django_filters.CharFilter(field_name='user_branch__user__first_name', lookup_expr='icontains', help_text='Ism bo\'yicha qidirish')
    last_name = django_filters.CharFilter(field_name='user_branch__user__last_name', lookup_expr='icontains', help_text='Familiya bo\'yicha qidirish')
    phone_number = django_filters.CharFilter(field_name='user_branch__user__phone_number', lookup_expr='icontains', help_text='Telefon raqam bo\'yicha qidirish')
    email = django_filters.CharFilter(field_name='user_branch__user__email', lookup_expr='icontains', help_text='Email bo\'yicha qidirish')
    
    # Branch fields
    branch_id = django_filters.UUIDFilter(field_name='user_branch__branch_id', help_text='Filial ID bo\'yicha filter')
    
    # Class fields (through ClassStudent)
    class_id = django_filters.UUIDFilter(method='filter_by_class', help_text='Sinf ID bo\'yicha filter')
    grade_level = django_filters.NumberFilter(method='filter_by_grade_level', help_text='Sinf darajasi bo\'yicha filter')
    
    # Date filters
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text='Yaratilgan sana (dan)')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text='Yaratilgan sana (gacha)')
    
    class Meta:
        model = StudentProfile
        fields = [
            'search',
            'personal_number',
            'gender',
            'status',
            'date_of_birth',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'branch_id',
            'class_id',
            'grade_level',
            'created_at__gte',
            'created_at__lte',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (shaxsiy raqam, ism, telefon)."""
        if not value:
            return queryset
        
        return queryset.filter(
            models.Q(personal_number__icontains=value) |
            models.Q(user_branch__user__first_name__icontains=value) |
            models.Q(user_branch__user__last_name__icontains=value) |
            models.Q(middle_name__icontains=value) |
            models.Q(user_branch__user__phone_number__icontains=value)
        )
    
    def filter_by_class(self, queryset, name, value):
        """Sinf bo'yicha filter."""
        if not value:
            return queryset
        
        from apps.school.classes.models import ClassStudent
        class_student_ids = ClassStudent.objects.filter(
            class_obj_id=value,
            deleted_at__isnull=True,
            is_active=True
        ).values_list('membership_id', flat=True)
        
        return queryset.filter(user_branch_id__in=class_student_ids)
    
    def filter_by_grade_level(self, queryset, name, value):
        """Sinf darajasi bo'yicha filter."""
        if not value:
            return queryset
        
        from apps.school.classes.models import ClassStudent, Class
        class_ids = Class.objects.filter(
            grade_level=value,
            deleted_at__isnull=True,
            is_active=True
        ).values_list('id', flat=True)
        
        class_student_ids = ClassStudent.objects.filter(
            class_obj_id__in=class_ids,
            deleted_at__isnull=True,
            is_active=True
        ).values_list('membership_id', flat=True)
        
        return queryset.filter(user_branch_id__in=class_student_ids)

