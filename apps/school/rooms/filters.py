"""
Filtering, search va ordering uchun filter classes.
"""
import django_filters
from .models import Building, Room


class BuildingFilter(django_filters.FilterSet):
    """Binolar uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (nomi, manzil)')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', help_text='Bino nomi bo\'yicha qidirish')
    
    # Filter fields
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol binolar bo\'yicha filter')
    
    class Meta:
        model = Building
        fields = [
            'search',
            'name',
            'is_active',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (nomi, manzil)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(address__icontains=value)
        )


class RoomFilter(django_filters.FilterSet):
    """Xonalar uchun filter."""
    
    # Search fields
    search = django_filters.CharFilter(method='filter_search', help_text='Qidirish (nomi, raqam)')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', help_text='Xona nomi bo\'yicha qidirish')
    number = django_filters.CharFilter(field_name='number', lookup_expr='icontains', help_text='Xona raqami bo\'yicha qidirish')
    
    # Filter fields
    building_id = django_filters.UUIDFilter(field_name='building_id', help_text='Bino ID bo\'yicha filter')
    room_type = django_filters.CharFilter(field_name='room_type', lookup_expr='iexact', help_text='Xona turi bo\'yicha filter')
    is_active = django_filters.BooleanFilter(field_name='is_active', help_text='Faol xonalar bo\'yicha filter')
    
    class Meta:
        model = Room
        fields = [
            'search',
            'name',
            'number',
            'building_id',
            'room_type',
            'is_active',
        ]
    
    def filter_search(self, queryset, name, value):
        """Umumiy qidiruv (nomi, raqam)."""
        if not value:
            return queryset
        
        from django.db import models
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(number__icontains=value)
        )


