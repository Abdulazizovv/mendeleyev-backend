from rest_framework import serializers
from apps.school.classes.models import Class, ClassStudent
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.academic.models import AcademicYear, Quarter


class TeacherClassSerializer(serializers.ModelSerializer):
    """O'qituvchi sinflari uchun serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    current_students_count = serializers.IntegerField(read_only=True)
    subjects_count = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Class
        fields = [
            'id',
            'branch',
            'branch_name',
            'academic_year',
            'academic_year_name',
            'name',
            'grade_level',
            'section',
            'max_students',
            'current_students_count',
            'subjects_count',
            'room',
            'room_name',
            'is_active',
        ]
    
    def get_subjects_count(self, obj):
        """Sinfdagi fanlar soni."""
        return obj.class_subjects.filter(deleted_at__isnull=True, is_active=True).count()


class TeacherSubjectSerializer(serializers.ModelSerializer):
    """O'qituvchi fanlari uchun serializer."""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    class_id = serializers.UUIDField(source='class_obj.id', read_only=True)
    academic_year_name = serializers.CharField(source='class_obj.academic_year.name', read_only=True)
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassSubject
        fields = [
            'id',
            'subject',
            'subject_name',
            'subject_code',
            'class_obj',
            'class_id',
            'class_name',
            'academic_year_name',
            'hours_per_week',
            'quarter',
            'quarter_name',
            'students_count',
            'is_active',
        ]
    
    def get_students_count(self, obj):
        """Sinfdagi o'quvchilar soni."""
        return obj.class_obj.current_students_count


class TeacherStudentSerializer(serializers.ModelSerializer):
    """O'qituvchi o'quvchilari uchun serializer."""
    
    student_id = serializers.UUIDField(source='membership.user.id', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    class_id = serializers.UUIDField(source='class_obj.id', read_only=True)
    academic_year_name = serializers.CharField(source='class_obj.academic_year.name', read_only=True)
    
    class Meta:
        model = ClassStudent
        fields = [
            'id',
            'student_id',
            'student_name',
            'student_phone',
            'class_obj',
            'class_id',
            'class_name',
            'academic_year_name',
            'enrollment_date',
            'is_active',
        ]
    
    def get_student_name(self, obj):
        """O'quvchi to'liq ismi."""
        user = obj.membership.user
        return user.get_full_name() or user.phone_number


class StudentClassSerializer(serializers.ModelSerializer):
    """O'quvchi sinfi uchun serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    class_teacher_name = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    students_count = serializers.IntegerField(source='current_students_count', read_only=True)
    subjects = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id',
            'branch',
            'branch_name',
            'academic_year',
            'academic_year_name',
            'name',
            'grade_level',
            'section',
            'class_teacher',
            'class_teacher_name',
            'max_students',
            'students_count',
            'room',
            'room_name',
            'subjects',
            'is_active',
        ]
    
    def get_class_teacher_name(self, obj):
        """O'qituvchi to'liq ismi."""
        if obj.class_teacher:
            user = obj.class_teacher.user
            return user.get_full_name() or user.phone_number
        return None
    
    def get_subjects(self, obj):
        """Sinfdagi fanlar."""
        subjects = obj.class_subjects.filter(
            deleted_at__isnull=True,
            is_active=True
        ).select_related('subject', 'teacher', 'teacher__user', 'quarter')
        
        return [
            {
                'id': cs.id,
                'subject_id': cs.subject.id,
                'subject_name': cs.subject.name,
                'subject_code': cs.subject.code,
                'teacher_id': cs.teacher.id if cs.teacher else None,
                'teacher_name': cs.teacher.user.get_full_name() or cs.teacher.user.phone_number if cs.teacher else None,
                'hours_per_week': cs.hours_per_week,
                'quarter_id': cs.quarter.id if cs.quarter else None,
                'quarter_name': cs.quarter.name if cs.quarter else None,
            }
            for cs in subjects
        ]


class StudentSubjectSerializer(serializers.ModelSerializer):
    """O'quvchi fanlari uchun serializer."""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    teacher_id = serializers.UUIDField(source='teacher.id', read_only=True)
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = [
            'id',
            'subject',
            'subject_name',
            'subject_code',
            'teacher',
            'teacher_id',
            'teacher_name',
            'hours_per_week',
            'quarter',
            'quarter_name',
            'is_active',
        ]
    
    def get_teacher_name(self, obj):
        """O'qituvchi to'liq ismi."""
        if obj.teacher:
            user = obj.teacher.user
            return user.get_full_name() or user.phone_number
        return None

