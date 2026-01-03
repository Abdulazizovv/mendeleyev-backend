"""Serializers for grades module."""
from rest_framework import serializers
from django.db import transaction
from .models import (
    AssessmentType, Assessment, Grade, QuarterGrade
)


class AssessmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for assessment types."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = AssessmentType
        fields = [
            'id', 'branch', 'branch_name', 'name', 'code', 'description',
            'default_max_score', 'default_weight', 'color', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assessment types."""
    
    class Meta:
        model = AssessmentType
        fields = [
            'branch', 'name', 'code', 'description',
            'default_max_score', 'default_weight', 'color', 'is_active'
        ]


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for grades with student details."""
    
    student_name = serializers.SerializerMethodField()
    student_personal_number = serializers.CharField(
        source='student.personal_number',
        read_only=True
    )
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    max_score = serializers.DecimalField(
        source='assessment.max_score',
        max_digits=6,
        decimal_places=2,
        read_only=True
    )
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'assessment', 'assessment_title', 'student', 'student_name',
            'student_personal_number', 'score', 'max_score', 'percentage',
            'calculated_score', 'final_score', 'override_reason', 'notes',
            'graded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'calculated_score', 'graded_at', 'created_at', 'updated_at'
        ]
    
    def get_student_name(self, obj):
        return obj.get_student_name()
    
    def get_percentage(self, obj):
        return obj.get_percentage()


class GradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating grades."""
    
    class Meta:
        model = Grade
        fields = ['assessment', 'student', 'score', 'notes']
    
    def validate(self, data):
        """Validate grade data."""
        assessment = data.get('assessment')
        student = data.get('student')
        score = data.get('score')
        
        # Check if assessment is locked
        if assessment and assessment.is_locked:
            raise serializers.ValidationError({
                'assessment': 'Nazorat bloklangan. Baho qo\'shish mumkin emas.'
            })
        
        # Validate score <= max_score
        if assessment and score > assessment.max_score:
            raise serializers.ValidationError({
                'score': f'Ball maksimal balldan oshmasligi kerak ({assessment.max_score})'
            })
        
        # Validate student belongs to class
        if student and assessment:
            from apps.school.classes.models import ClassStudent
            
            is_enrolled = ClassStudent.objects.filter(
                class_obj=assessment.class_subject.class_obj,
                membership=student.membership,
                is_active=True,
                deleted_at__isnull=True
            ).exists()
            
            if not is_enrolled:
                raise serializers.ValidationError({
                    'student': 'O\'quvchi ushbu sinfga yozilmagan.'
                })
        
        return data


class GradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating grades."""
    
    class Meta:
        model = Grade
        fields = ['score', 'final_score', 'override_reason', 'notes']
    
    def validate(self, data):
        """Validate update data."""
        if self.instance and self.instance.assessment.is_locked:
            raise serializers.ValidationError(
                'Nazorat bloklangan. Bahoni o\'zgartirish mumkin emas.'
            )
        
        # If final_score is provided, override_reason must be provided
        if data.get('final_score') is not None:
            if not data.get('override_reason'):
                raise serializers.ValidationError({
                    'override_reason': 'Yakuniy bahoni o\'zgartirish uchun sabab ko\'rsating.'
                })
        
        return data


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for assessments with nested data."""
    
    class_name = serializers.CharField(source='class_subject.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    assessment_type_name = serializers.CharField(source='assessment_type.name', read_only=True)
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    average_score = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    grades_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'class_subject', 'class_name', 'subject_name', 'teacher_name',
            'assessment_type', 'assessment_type_name', 'lesson', 'quarter', 'quarter_name',
            'title', 'description', 'date', 'max_score', 'weight',
            'is_locked', 'locked_at', 'notes',
            'average_score', 'completion_rate', 'grades_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_locked', 'locked_at', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return None
    
    def get_average_score(self, obj):
        return obj.get_average_score()
    
    def get_completion_rate(self, obj):
        return obj.get_completion_rate()
    
    def get_grades_count(self, obj):
        return obj.grades.filter(deleted_at__isnull=True).count()


class AssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assessments."""
    
    class Meta:
        model = Assessment
        fields = [
            'class_subject', 'assessment_type', 'lesson', 'quarter',
            'title', 'description', 'date', 'max_score', 'weight', 'notes'
        ]
    
    def validate(self, data):
        """Validate assessment data."""
        # Validate quarter belongs to class subject's academic year
        quarter = data.get('quarter')
        class_subject = data.get('class_subject')
        
        if quarter and class_subject:
            if quarter.academic_year_id != class_subject.class_obj.academic_year_id:
                raise serializers.ValidationError({
                    'quarter': 'Chorak sinf akademik yiliga tegishli emas.'
                })
        
        # Validate assessment type belongs to same branch
        assessment_type = data.get('assessment_type')
        if assessment_type and class_subject:
            if assessment_type.branch_id != class_subject.class_obj.branch_id:
                raise serializers.ValidationError({
                    'assessment_type': 'Nazorat turi filialga tegishli emas.'
                })
        
        return data


class BulkGradeCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating grades."""
    
    assessment_id = serializers.UUIDField(required=True)
    grades = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text='List of {student_id, score, notes}'
    )
    
    def validate_grades(self, value):
        """Validate grades format."""
        if not value:
            raise serializers.ValidationError('Kamida bitta baho kerak.')
        
        for grade in value:
            if 'student_id' not in grade:
                raise serializers.ValidationError('Har bir bahoda student_id bo\'lishi kerak.')
            if 'score' not in grade:
                raise serializers.ValidationError('Har bir bahoda score bo\'lishi kerak.')
        
        return value
    
    def create(self, validated_data):
        """Create multiple grades in transaction."""
        from auth.profiles.models import StudentProfile
        
        assessment_id = validated_data['assessment_id']
        grades_data = validated_data['grades']
        
        with transaction.atomic():
            assessment = Assessment.objects.get(id=assessment_id)
            
            # Check if locked
            if assessment.is_locked:
                raise serializers.ValidationError({
                    'assessment': 'Nazorat bloklangan. Baho qo\'shish mumkin emas.'
                })
            
            created_grades = []
            
            for grade_data in grades_data:
                student = StudentProfile.objects.get(id=grade_data['student_id'])
                
                grade, created = Grade.objects.update_or_create(
                    assessment=assessment,
                    student=student,
                    defaults={
                        'score': grade_data['score'],
                        'notes': grade_data.get('notes', '')
                    }
                )
                created_grades.append(grade)
            
            return created_grades


class QuarterGradeSerializer(serializers.ModelSerializer):
    """Serializer for quarter grades."""
    
    student_name = serializers.SerializerMethodField()
    student_personal_number = serializers.CharField(
        source='student.personal_number',
        read_only=True
    )
    class_name = serializers.CharField(source='class_subject.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    
    class Meta:
        model = QuarterGrade
        fields = [
            'id', 'student', 'student_name', 'student_personal_number',
            'class_subject', 'class_name', 'subject_name',
            'quarter', 'quarter_name', 'calculated_grade', 'final_grade',
            'override_reason', 'is_locked', 'locked_at', 'last_calculated',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'calculated_grade', 'is_locked', 'locked_at',
            'last_calculated', 'created_at', 'updated_at'
        ]
    
    def get_student_name(self, obj):
        return obj.get_student_name()


class QuarterGradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating quarter grades (manual override)."""
    
    class Meta:
        model = QuarterGrade
        fields = ['final_grade', 'override_reason']
    
    def validate(self, data):
        """Validate quarter grade update."""
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError(
                'Chorak bahosi bloklangan. O\'zgartirish mumkin emas.'
            )
        
        # If final_grade is provided, override_reason must be provided
        if data.get('final_grade') is not None:
            if not data.get('override_reason'):
                raise serializers.ValidationError({
                    'override_reason': 'Yakuniy bahoni o\'zgartirish uchun sabab ko\'rsating.'
                })
        
        return data


class GradeLockSerializer(serializers.Serializer):
    """Serializer for locking/unlocking assessments or quarter grades."""
    
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text='List of IDs to lock/unlock'
    )
    action = serializers.ChoiceField(
        choices=['lock', 'unlock'],
        required=True
    )
    type = serializers.ChoiceField(
        choices=['assessment', 'quarter_grade'],
        required=True
    )
