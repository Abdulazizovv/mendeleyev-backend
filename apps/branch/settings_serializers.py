from rest_framework import serializers
from .models import BranchSettings


class BranchSettingsSerializer(serializers.ModelSerializer):
    """Serializer for BranchSettings."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = BranchSettings
        fields = [
            'id',
            'branch',
            'branch_name',
            'lesson_duration_minutes',
            'break_duration_minutes',
            'school_start_time',
            'school_end_time',
            'academic_year_start_month',
            'academic_year_end_month',
            'currency',
            'currency_symbol',
            'additional_settings',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class BranchSettingsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating BranchSettings."""
    
    class Meta:
        model = BranchSettings
        fields = [
            'lesson_duration_minutes',
            'break_duration_minutes',
            'school_start_time',
            'school_end_time',
            'academic_year_start_month',
            'academic_year_end_month',
            'currency',
            'currency_symbol',
            'additional_settings',
        ]
    
    def validate(self, data):
        """Validate settings."""
        lesson_duration = data.get('lesson_duration_minutes', self.instance.lesson_duration_minutes if self.instance else 45)
        break_duration = data.get('break_duration_minutes', self.instance.break_duration_minutes if self.instance else 10)
        start_time = data.get('school_start_time', self.instance.school_start_time if self.instance else None)
        end_time = data.get('school_end_time', self.instance.school_end_time if self.instance else None)
        
        if lesson_duration and lesson_duration <= 0:
            raise serializers.ValidationError({
                'lesson_duration_minutes': 'Dars davomiyligi 0 dan katta bo\'lishi kerak.'
            })
        
        if break_duration and break_duration < 0:
            raise serializers.ValidationError({
                'break_duration_minutes': 'Tanaffus davomiyligi 0 dan kichik bo\'lmasligi kerak.'
            })
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'school_end_time': 'Maktab tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        return data

