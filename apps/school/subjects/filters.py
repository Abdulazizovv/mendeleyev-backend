"""
Filtering, search va ordering uchun filter classes.
"""
import django_filters
from .models import Subject, ClassSubject


class SubjectFilter(django_filters.FilterSet):
    """Fanlar uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (nomi, kod)')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', help_text='Fan nomi bo\'yicha qidirish')
    code = django_filters.CharFilter(field_name='code', lookup_expr='icontains', help_text='Fan kodi bo\'yicha qidirish')
    
    # Filter fields
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol fanlar bo\'yicha filter')
    
    class Meta:
        model = Subject
        fields = [
            'search',
            'name',
            'code',
            'is_active',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (nomi, kod)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(code__icontains=value)
        )


class ClassSubjectFilter(django_filters.FilterSet):
    """Sinf fanlari uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (fan nomi, o\'qituvchi)')
    
    # Filter fields
    subject_id = django_filters.UUIDFilter(field_name='subject_id', help_text='Fan ID bo\'yicha filter')
    teacher_id = django_filters.UUIDFilter(field_name='teacher_id', help_text='O\'qituvchi ID bo\'yicha filter')
    quarter_id = django_filters.UUIDFilter(field_name='quarter_id', help_text='Chorak ID bo\'yicha filter')
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol fanlar bo\'yicha filter')
    
    class Meta:
        model = ClassSubject
        fields = [
            'search',
            'subject_id',
            'teacher_id',
            'quarter_id',
            'is_active',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (fan nomi, o'qituvchi)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(subject__name__icontains=value) |
            models.Q(teacher__user__first_name__icontains=value) |
            models.Q(teacher__user__last_name__icontains=value)
        )


