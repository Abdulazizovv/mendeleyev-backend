from rest_framework import serializers
from .models import AcademicYear, Quarter


class QuarterSerializer(serializers.ModelSerializer):
    """Chorak serializer."""
    
    class Meta:
        model = Quarter
        fields = [
            'id',
            'name',
            'number',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AcademicYearSerializer(serializers.ModelSerializer):
    """Akademik yil serializer."""
    
    quarters = QuarterSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = AcademicYear
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'start_date',
            'end_date',
            'is_active',
            'quarters',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'Tugash sanasi boshlanish sanasidan keyin bo\'lishi kerak.'
            })
        
        return data


class AcademicYearCreateSerializer(serializers.ModelSerializer):
    """Akademik yil yaratish uchun serializer."""
    
    class Meta:
        model = AcademicYear
        fields = [
            'branch',
            'name',
            'start_date',
            'end_date',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'Tugash sanasi boshlanish sanasidan keyin bo\'lishi kerak.'
            })
        
        return data


class QuarterCreateSerializer(serializers.ModelSerializer):
    """Chorak yaratish uchun serializer."""
    
    class Meta:
        model = Quarter
        fields = [
            'academic_year',
            'name',
            'number',
            'start_date',
            'end_date',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate dates, academic year, and quarter number."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        academic_year = data.get('academic_year')
        number = data.get('number')
        
        # Date validation
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'Tugash sanasi boshlanish sanasidan keyin bo\'lishi kerak.'
            })
        
        # Academic year date validation
        if academic_year and start_date:
            if start_date < academic_year.start_date or start_date > academic_year.end_date:
                raise serializers.ValidationError({
                    'start_date': 'Chorak boshlanish sanasi akademik yil ichida bo\'lishi kerak.'
                })
        
        if academic_year and end_date:
            if end_date < academic_year.start_date or end_date > academic_year.end_date:
                raise serializers.ValidationError({
                    'end_date': 'Chorak tugash sanasi akademik yil ichida bo\'lishi kerak.'
                })
        
        # Quarter number validation (1-4)
        if number is not None:
            if number < 1 or number > 4:
                raise serializers.ValidationError({
                    'number': 'Chorak raqami 1 va 4 orasida bo\'lishi kerak.'
                })
        
        return data

