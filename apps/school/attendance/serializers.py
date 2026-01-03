"""Serializers for attendance module."""
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import (
    LessonAttendance, StudentAttendanceRecord, AttendanceStatistics,
    AttendanceStatus
)
from apps.school.schedule.serializers import LessonInstanceSerializer


class StudentAttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for student attendance record with student details."""
    
    student_name = serializers.SerializerMethodField()
    student_personal_number = serializers.CharField(
        source='student.personal_number', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    
    class Meta:
        model = StudentAttendanceRecord
        fields = [
            'id', 'attendance', 'student', 'student_name', 
            'student_personal_number', 'status', 'status_display',
            'notes', 'marked_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'marked_at', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        """Get student's full name."""
        return obj.get_student_name()


class StudentAttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating student attendance records."""
    
    class Meta:
        model = StudentAttendanceRecord
        fields = ['attendance', 'student', 'status', 'notes']
    
    def validate(self, data):
        """Validate attendance record."""
        attendance = data.get('attendance')
        student = data.get('student')
        
        # Check if attendance is locked
        if attendance and attendance.is_locked:
            # For updates, allow if it's admin override
            if not self.instance:
                raise serializers.ValidationError({
                    'attendance': 'Davomat bloklangan. Yangi yozuv qo\'shish mumkin emas.'
                })
        
        # Validate student belongs to class
        if student and attendance:
            from apps.school.classes.models import ClassStudent
            
            is_enrolled = ClassStudent.objects.filter(
                class_obj=attendance.class_obj,
                membership=student.membership,
                is_active=True,
                deleted_at__isnull=True
            ).exists()
            
            if not is_enrolled:
                raise serializers.ValidationError({
                    'student': 'O\'quvchi ushbu sinfga yozilmagan.'
                })
        
        return data


class LessonAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for lesson attendance with nested records and statistics."""
    
    class_name = serializers.CharField(
        source='class_subject.class_obj.name', 
        read_only=True
    )
    subject_name = serializers.CharField(
        source='class_subject.subject.name', 
        read_only=True
    )
    teacher_name = serializers.SerializerMethodField()
    records = StudentAttendanceRecordSerializer(many=True, read_only=True)
    present_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    late_count = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()
    lesson_details = LessonInstanceSerializer(source='lesson', read_only=True)
    
    class Meta:
        model = LessonAttendance
        fields = [
            'id', 'lesson', 'lesson_details', 'class_subject', 'class_name',
            'subject_name', 'teacher_name', 'date', 'lesson_number',
            'is_locked', 'locked_at', 'locked_by', 'notes',
            'records', 'present_count', 'absent_count', 'late_count', 'total_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_locked', 'locked_at', 'locked_by', 
            'created_at', 'updated_at'
        ]
    
    def get_teacher_name(self, obj):
        """Get teacher name."""
        if obj.teacher and obj.teacher.user:
            return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return None
    
    def get_present_count(self, obj):
        return obj.get_present_count()
    
    def get_absent_count(self, obj):
        return obj.get_absent_count()
    
    def get_late_count(self, obj):
        return obj.get_late_count()
    
    def get_total_count(self, obj):
        return obj.get_total_count()


class LessonAttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lesson attendance."""
    
    class Meta:
        model = LessonAttendance
        fields = [
            'lesson', 'class_subject', 'date', 'lesson_number', 'notes'
        ]
    
    def validate(self, data):
        """Validate attendance data."""
        # If lesson is provided, sync data from lesson
        lesson = data.get('lesson')
        if lesson:
            if lesson.class_subject_id != data.get('class_subject').id:
                raise serializers.ValidationError({
                    'lesson': 'Dars ushbu sinf faniga tegishli emas.'
                })
            # Auto-fill date and lesson_number if not provided
            if not data.get('date'):
                data['date'] = lesson.date
            if not data.get('lesson_number') or data.get('lesson_number') == 1:
                data['lesson_number'] = lesson.lesson_number
        
        return data


class BulkAttendanceMarkSerializer(serializers.Serializer):
    """Serializer for bulk marking attendance."""
    
    attendance_id = serializers.UUIDField(required=False, allow_null=True)
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    class_subject_id = serializers.UUIDField(required=False)
    date = serializers.DateField(required=False)
    lesson_number = serializers.IntegerField(required=False, default=1)
    notes = serializers.CharField(required=False, allow_blank=True)
    records = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text='List of {student_id, status, notes}'
    )
    
    def validate_records(self, value):
        """Validate records format."""
        if not value:
            raise serializers.ValidationError('Kamida bitta o\'quvchi yozuvi kerak.')
        
        for record in value:
            if 'student_id' not in record:
                raise serializers.ValidationError('Har bir yozuvda student_id bo\'lishi kerak.')
            if 'status' not in record:
                raise serializers.ValidationError('Har bir yozuvda status bo\'lishi kerak.')
            if record['status'] not in dict(AttendanceStatus.choices):
                raise serializers.ValidationError(
                    f'Noto\'g\'ri status: {record["status"]}'
                )
        
        return value
    
    def validate(self, data):
        """Validate bulk attendance data."""
        # Either attendance_id or (class_subject_id + date) must be provided
        if not data.get('attendance_id'):
            if not data.get('class_subject_id') or not data.get('date'):
                raise serializers.ValidationError({
                    'non_field_errors': [
                        'attendance_id yoki (class_subject_id + date) kerak.'
                    ]
                })
        
        return data
    
    def create(self, validated_data):
        """Create or update attendance with bulk records."""
        from apps.school.subjects.models import ClassSubject
        from apps.school.schedule.models import LessonInstance
        from auth.profiles.models import StudentProfile
        
        with transaction.atomic():
            # Get or create attendance
            if validated_data.get('attendance_id'):
                attendance = LessonAttendance.objects.get(
                    id=validated_data['attendance_id']
                )
            else:
                # Find or create lesson if lesson_id provided
                lesson = None
                if validated_data.get('lesson_id'):
                    lesson = LessonInstance.objects.get(
                        id=validated_data['lesson_id']
                    )
                
                # Create attendance
                attendance, created = LessonAttendance.objects.get_or_create(
                    class_subject_id=validated_data['class_subject_id'],
                    date=validated_data['date'],
                    lesson_number=validated_data.get('lesson_number', 1),
                    defaults={
                        'lesson': lesson,
                        'notes': validated_data.get('notes', '')
                    }
                )
            
            # Check if locked
            if attendance.is_locked:
                raise serializers.ValidationError({
                    'attendance': 'Davomat bloklangan. O\'zgartirish mumkin emas.'
                })
            
            # Create or update records
            records_data = validated_data['records']
            
            for record_data in records_data:
                student = StudentProfile.objects.get(
                    id=record_data['student_id']
                )
                
                StudentAttendanceRecord.objects.update_or_create(
                    attendance=attendance,
                    student=student,
                    defaults={
                        'status': record_data['status'],
                        'notes': record_data.get('notes', '')
                    }
                )
            
            return attendance


class AttendanceStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for attendance statistics."""
    
    student_name = serializers.SerializerMethodField()
    class_name = serializers.CharField(
        source='class_subject.class_obj.name', 
        read_only=True
    )
    subject_name = serializers.CharField(
        source='class_subject.subject.name', 
        read_only=True
    )
    
    class Meta:
        model = AttendanceStatistics
        fields = [
            'id', 'student', 'student_name', 'class_subject', 'class_name',
            'subject_name', 'start_date', 'end_date', 'total_lessons',
            'present_count', 'absent_count', 'late_count', 'excused_count',
            'attendance_rate', 'last_calculated'
        ]
        read_only_fields = [
            'id', 'total_lessons', 'present_count', 'absent_count',
            'late_count', 'excused_count', 'attendance_rate', 'last_calculated'
        ]
    
    def get_student_name(self, obj):
        """Get student's full name."""
        return obj.get_student_name() if obj.student else None


class AttendanceLockSerializer(serializers.Serializer):
    """Serializer for locking/unlocking attendance."""
    
    attendance_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text='List of attendance IDs to lock/unlock'
    )
    action = serializers.ChoiceField(
        choices=['lock', 'unlock'],
        required=True
    )
    
    def validate_attendance_ids(self, value):
        """Validate attendance IDs exist."""
        if not value:
            raise serializers.ValidationError('Kamida bitta davomat ID kerak.')
        
        # Check all IDs exist
        existing_count = LessonAttendance.objects.filter(
            id__in=value,
            deleted_at__isnull=True
        ).count()
        
        if existing_count != len(value):
            raise serializers.ValidationError('Ba\'zi davomat ID lari topilmadi.')
        
        return value
