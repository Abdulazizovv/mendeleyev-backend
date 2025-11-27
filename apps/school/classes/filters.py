"""
Filtering, search va ordering uchun filter classes.
"""
import django_filters
from .models import Class, ClassStudent


class ClassFilter(django_filters.FilterSet):
    """Sinflar uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (nomi, sinf rahbari)')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', help_text='Sinf nomi bo\'yicha qidirish')
    
    # Filter fields
    academic_year_id = django_filters.UUIDFilter(field_name='academic_year_id', help_text='Akademik yil ID bo\'yicha filter')
    grade_level = django_filters.NumberFilter(field_name='grade_level', help_text='Sinf darajasi bo\'yicha filter')
    section = django_filters.CharFilter(field_name='section', lookup_expr='iexact', help_text='Bo\'lim bo\'yicha filter')
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol sinflar bo\'yicha filter')
    class_teacher_id = django_filters.UUIDFilter(field_name='class_teacher_id', help_text='Sinf rahbari ID bo\'yicha filter')
    room_id = django_filters.UUIDFilter(field_name='room_id', help_text='Xona ID bo\'yicha filter')
    
    class Meta:
        model = Class
        fields = [
            'search',
            'name',
            'academic_year_id',
            'grade_level',
            'section',
            'is_active',
            'class_teacher_id',
            'room_id',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (nomi, sinf rahbari)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(class_teacher__user__first_name__icontains=value) |
            models.Q(class_teacher__user__last_name__icontains=value)
        )


class ClassStudentFilter(django_filters.FilterSet):
    """Sinf o'quvchilari uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (ism, telefon)')
    
    # Filter fields
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol o\'quvchilar bo\'yicha filter')
    
    class Meta:
        model = ClassStudent
        fields = [
            'search',
            'is_active',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (ism, telefon)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(membership__user__first_name__icontains=value) |
            models.Q(membership__user__last_name__icontains=value) |
            models.Q(membership__user__phone_number__icontains=value)
        )


