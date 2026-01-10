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
            'lunch_break_start',
            'lunch_break_end',
            'academic_year_start_month',
            'academic_year_end_month',
            'currency',
            'currency_symbol',
            'working_days',
            'holidays',
            'daily_lesson_start_time',
            'daily_lesson_end_time',
            'max_lessons_per_day',
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
            'lunch_break_start',
            'lunch_break_end',
            'academic_year_start_month',
            'academic_year_end_month',
            'currency',
            'currency_symbol',
            'working_days',
            'holidays',
            'daily_lesson_start_time',
            'daily_lesson_end_time',
            'max_lessons_per_day',
            'additional_settings',
        ]
    
    def validate_working_days(self, value):
        """Validate working days format."""
        if not isinstance(value, list):
            raise serializers.ValidationError('Ish kunlari ro\'yxat formatida bo\'lishi kerak.')
        
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in value:
            if day.lower() not in valid_days:
                raise serializers.ValidationError(
                    f'Noto\'g\'ri kun: {day}. Faqat: {", ".join(valid_days)}'
                )
        return [day.lower() for day in value]
    
    def validate_holidays(self, value):
        """Validate holidays format (YYYY-MM-DD)."""
        if not isinstance(value, list):
            raise serializers.ValidationError('Bayram kunlari ro\'yxat formatida bo\'lishi kerak.')
        
        from datetime import datetime
        for date_str in value:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                raise serializers.ValidationError(
                    f'Noto\'g\'ri sana formati: {date_str}. YYYY-MM-DD formatida bo\'lishi kerak.'
                )
        return value
    
    def validate_max_lessons_per_day(self, value):
        """Validate max lessons per day."""
        if value < 1:
            raise serializers.ValidationError('Kunlik darslar soni 1 dan kam bo\'lmasligi kerak.')
        if value > 15:
            raise serializers.ValidationError('Kunlik darslar soni 15 dan ko\'p bo\'lmasligi kerak.')
        return value
    
    def validate(self, data):
        """Validate settings."""
        lesson_duration = data.get('lesson_duration_minutes', self.instance.lesson_duration_minutes if self.instance else 45)
        break_duration = data.get('break_duration_minutes', self.instance.break_duration_minutes if self.instance else 10)
        start_time = data.get('school_start_time', self.instance.school_start_time if self.instance else None)
        end_time = data.get('school_end_time', self.instance.school_end_time if self.instance else None)
        daily_start = data.get('daily_lesson_start_time', self.instance.daily_lesson_start_time if self.instance else None)
        daily_end = data.get('daily_lesson_end_time', self.instance.daily_lesson_end_time if self.instance else None)
        
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
        
        if daily_start and daily_end and daily_start >= daily_end:
            raise serializers.ValidationError({
                'daily_lesson_end_time': 'Oxirgi dars tugash vaqti birinchi dars boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        # Validate lunch break times
        lunch_start = data.get('lunch_break_start', self.instance.lunch_break_start if self.instance else None)
        lunch_end = data.get('lunch_break_end', self.instance.lunch_break_end if self.instance else None)
        
        if (lunch_start and not lunch_end) or (lunch_end and not lunch_start):
            raise serializers.ValidationError({
                'lunch_break_start': 'Tushlik tanaffusi boshlanish va tugash vaqti ikkalasi ham kiritilishi kerak.',
                'lunch_break_end': 'Tushlik tanaffusi boshlanish va tugash vaqti ikkalasi ham kiritilishi kerak.'
            })
        
        if lunch_start and lunch_end and lunch_start >= lunch_end:
            raise serializers.ValidationError({
                'lunch_break_end': 'Tushlik tanaffusi tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        # Validate lunch break is within school hours
        if lunch_start and start_time and lunch_start < start_time:
            raise serializers.ValidationError({
                'lunch_break_start': 'Tushlik tanaffusi maktab boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        if lunch_end and end_time and lunch_end > end_time:
            raise serializers.ValidationError({
                'lunch_break_end': 'Tushlik tanaffusi maktab tugash vaqtidan oldin bo\'lishi kerak.'
            })
        
        return data

