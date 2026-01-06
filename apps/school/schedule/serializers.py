"""Serializers for schedule module."""
from rest_framework import serializers
from django.db import transaction
from .models import (
    TimetableTemplate, TimetableSlot, LessonInstance, 
    LessonTopic, DayOfWeek, LessonStatus
)
from .services import ScheduleConflictDetector
from apps.school.subjects.serializers import SubjectSerializer, ClassSubjectSerializer
from apps.school.classes.serializers import ClassSerializer
from apps.school.rooms.serializers import RoomSerializer


class LessonTopicSerializer(serializers.ModelSerializer):
    """Serializer for LessonTopic with nested subject info."""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    
    class Meta:
        model = LessonTopic
        fields = [
            'id', 'subject', 'subject_name', 'quarter', 'quarter_name',
            'title', 'description', 'position', 'estimated_hours',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LessonTopicCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lesson topics."""
    
    class Meta:
        model = LessonTopic
        fields = [
            'subject', 'quarter', 'title', 'description', 
            'position', 'estimated_hours'
        ]
    
    def validate(self, data):
        """Validate topic data."""
        subject = data.get('subject')
        quarter = data.get('quarter')
        
        # If quarter is provided, ensure it belongs to same branch as subject
        if quarter and subject:
            if quarter.academic_year.branch_id != subject.branch_id:
                raise serializers.ValidationError({
                    'quarter': 'Chorak va fan bir xil filialga tegishli bo\'lishi kerak.'
                })
        
        return data


class TimetableTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TimetableTemplate with nested data."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    slots_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TimetableTemplate
        fields = [
            'id', 'branch', 'branch_name', 'academic_year', 'academic_year_name',
            'name', 'description', 'is_active', 'effective_from', 'effective_until',
            'slots_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_slots_count(self, obj):
        """Get number of slots in this timetable."""
        return obj.slots.filter(deleted_at__isnull=True).count()


class TimetableTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timetable templates."""
    
    class Meta:
        model = TimetableTemplate
        fields = [
            'branch', 'academic_year', 'name', 'description',
            'is_active', 'effective_from', 'effective_until'
        ]
    
    def validate(self, data):
        """Validate timetable data."""
        effective_from = data.get('effective_from')
        effective_until = data.get('effective_until')
        academic_year = data.get('academic_year')
        
        if effective_until and effective_from and effective_until <= effective_from:
            raise serializers.ValidationError({
                'effective_until': 'Tugash sanasi boshlanish sanasidan keyin bo\'lishi kerak.'
            })
        
        if academic_year:
            if effective_from and effective_from < academic_year.start_date:
                raise serializers.ValidationError({
                    'effective_from': 'Jadval akademik yildan oldin boshlanmasligi kerak.'
                })
            if effective_until and effective_until > academic_year.end_date:
                raise serializers.ValidationError({
                    'effective_until': 'Jadval akademik yildan keyin tugamasligi kerak.'
                })
        
        return data


class TimetableSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimetableSlot with nested data."""
    
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'timetable', 'class_obj', 'class_name', 'class_subject',
            'subject_name', 'teacher_name', 'day_of_week', 'day_display',
            'lesson_number', 'start_time', 'end_time', 'room', 'room_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        """Get teacher name from class_subject."""
        if obj.class_subject and obj.class_subject.teacher:
            membership = obj.class_subject.teacher
            if hasattr(membership, 'user'):
                return f"{membership.user.first_name} {membership.user.last_name}"
        return None


class TimetableSlotCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timetable slots with conflict checking."""
    
    check_conflicts = serializers.BooleanField(
        default=True,
        write_only=True,
        help_text='Konfliktlarni tekshirish (default: True)'
    )
    
    class Meta:
        model = TimetableSlot
        fields = [
            'timetable', 'class_obj', 'class_subject', 'day_of_week',
            'lesson_number', 'start_time', 'end_time', 'room',
            'check_conflicts'
        ]
    
    def validate(self, data):
        """Validate slot data and check conflicts."""
        # Basic validation
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    'end_time': 'Tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
                })
        
        # Validate class_subject belongs to class (if both provided)
        class_subject = data.get('class_subject') or (self.instance.class_subject if self.instance else None)
        class_obj = data.get('class_obj') or (self.instance.class_obj if self.instance else None)
        
        if class_subject and class_obj:
            if class_subject.class_obj_id != class_obj.id:
                raise serializers.ValidationError({
                    'class_subject': 'Tanlangan fan ushbu sinfga tegishli emas.'
                })
        
        # Validate room belongs to same branch (if both provided)
        room = data.get('room')
        if room and class_obj:
            if room.branch_id != class_obj.branch_id:
                raise serializers.ValidationError({
                    'room': 'Xona sinfning filialiga tegishli emas.'
                })
        
        # Check conflicts if enabled
        check_conflicts = data.pop('check_conflicts', True)
        if check_conflicts:
            # For update, use existing instance data as base
            if self.instance:
                slot_data = {
                    'timetable': data.get('timetable', self.instance.timetable),
                    'class_obj': data.get('class_obj', self.instance.class_obj),
                    'class_subject': data.get('class_subject', self.instance.class_subject),
                    'day_of_week': data.get('day_of_week', self.instance.day_of_week),
                    'lesson_number': data.get('lesson_number', self.instance.lesson_number),
                    'start_time': data.get('start_time', self.instance.start_time),
                    'end_time': data.get('end_time', self.instance.end_time),
                    'room': data.get('room', self.instance.room),
                }
                temp_slot = TimetableSlot(**slot_data)
                exclude_slot_id = self.instance.id
            else:
                temp_slot = TimetableSlot(**data)
                exclude_slot_id = None
            
            conflicts = ScheduleConflictDetector.check_slot_conflicts(
                temp_slot, 
                exclude_slot_id=exclude_slot_id
            )
            
            if conflicts:
                raise serializers.ValidationError({
                    'conflicts': [
                        {
                            'type': c['type'],
                            'message': c['message'],
                            'details': c.get('details', {})
                        }
                        for c in conflicts
                    ]
                })
        
        return data


class TimetableSlotBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating timetable slots."""
    
    slots = TimetableSlotCreateSerializer(many=True)
    check_conflicts = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate bulk slot data."""
        slots_data = data.get('slots', [])
        
        if not slots_data:
            raise serializers.ValidationError({
                'slots': 'Kamida bitta slot ma\'lumoti kerak.'
            })
        
        return data
    
    def create(self, validated_data):
        """Create multiple slots in transaction."""
        slots_data = validated_data['slots']
        check_conflicts = validated_data.get('check_conflicts', True)
        
        created_slots = []
        
        with transaction.atomic():
            for slot_data in slots_data:
                slot_data['check_conflicts'] = check_conflicts
                serializer = TimetableSlotCreateSerializer(data=slot_data)
                serializer.is_valid(raise_exception=True)
                slot = serializer.save()
                created_slots.append(slot)
        
        return created_slots


class LessonInstanceSerializer(serializers.ModelSerializer):
    """Serializer for LessonInstance with nested data."""
    
    class_name = serializers.CharField(source='class_subject.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = LessonInstance
        fields = [
            'id', 'class_subject', 'class_name', 'subject_name', 'teacher_name',
            'date', 'lesson_number', 'start_time', 'end_time', 'room', 'room_name',
            'topic', 'topic_title', 'homework', 'teacher_notes', 'status', 'status_display',
            'is_auto_generated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_auto_generated', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        """Get teacher name."""
        if obj.teacher:
            return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return None


class LessonInstanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lesson instances with conflict checking."""
    
    check_conflicts = serializers.BooleanField(
        default=True,
        write_only=True,
        help_text='Konfliktlarni tekshirish'
    )
    
    class Meta:
        model = LessonInstance
        fields = [
            'class_subject', 'date', 'lesson_number', 'start_time', 'end_time',
            'room', 'topic', 'homework', 'teacher_notes', 'status',
            'check_conflicts'
        ]
    
    def validate(self, data):
        """Validate lesson data and check conflicts."""
        # Basic validation
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                'end_time': 'Tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        # Validate topic belongs to subject
        if data.get('topic'):
            if data['topic'].subject_id != data['class_subject'].subject_id:
                raise serializers.ValidationError({
                    'topic': 'Mavzu ushbu fanga tegishli emas.'
                })
        
        # Check conflicts if enabled
        check_conflicts = data.pop('check_conflicts', True)
        if check_conflicts:
            # Create temporary lesson for conflict checking
            temp_lesson = LessonInstance(**data)
            conflicts = ScheduleConflictDetector.check_lesson_conflicts(temp_lesson)
            
            if conflicts:
                raise serializers.ValidationError({
                    'conflicts': [
                        {
                            'type': c['type'],
                            'message': c['message'],
                            'details': c.get('details', {})
                        }
                        for c in conflicts
                    ]
                })
        
        return data


class LessonInstanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating lesson instances."""
    
    class Meta:
        model = LessonInstance
        fields = [
            'topic', 'homework', 'teacher_notes', 'status', 'room'
        ]


class LessonGenerationRequestSerializer(serializers.Serializer):
    """Serializer for lesson generation request."""
    
    timetable_id = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    skip_existing = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate generation request."""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError({
                'end_date': 'Tugash sanasi boshlanish sanasidan keyin bo\'lishi kerak.'
            })
        
        # Check if timetable exists
        if not TimetableTemplate.objects.filter(
            id=data['timetable_id'],
            deleted_at__isnull=True
        ).exists():
            raise serializers.ValidationError({
                'timetable_id': 'Jadval topilmadi.'
            })
        
        return data


class WeeklyScheduleSerializer(serializers.Serializer):
    """Serializer for weekly schedule view."""
    
    class_id = serializers.UUIDField(required=True)
    week_start = serializers.DateField(required=True)
    
    def validate_week_start(self, value):
        """Ensure week_start is a Monday."""
        if value.weekday() != 0:  # 0 = Monday
            raise serializers.ValidationError('Hafta boshlanishi dushanba bo\'lishi kerak.')
        return value
