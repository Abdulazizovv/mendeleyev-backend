from rest_framework import serializers
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from .models import Homework, HomeworkSubmission, HomeworkStatus, SubmissionStatus


class HomeworkListSerializer(serializers.ModelSerializer):
    """List homework with basic info."""
    
    class_name = serializers.CharField(source='class_subject.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'title', 'class_name', 'subject_name', 'teacher_name',
            'assigned_date', 'due_date', 'status', 'submission_count',
            'completion_rate', 'is_overdue', 'created_at'
        ]
    
    def get_teacher_name(self, obj):
        """Get teacher's full name."""
        if obj.teacher and obj.teacher.user:
            return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return None
    
    def get_submission_count(self, obj):
        """Get submission count."""
        return obj.get_submission_count()
    
    def get_completion_rate(self, obj):
        """Get completion rate."""
        return obj.get_completion_rate()
    
    def get_is_overdue(self, obj):
        """Check if overdue."""
        return obj.is_overdue()


class HomeworkDetailSerializer(serializers.ModelSerializer):
    """Detail view of homework."""
    
    class_name = serializers.CharField(source='class_subject.class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='class_subject.subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    lesson_info = serializers.SerializerMethodField()
    assessment_info = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    graded_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'class_subject', 'class_name', 'subject_name', 'teacher_name',
            'lesson', 'lesson_info', 'assessment', 'assessment_info',
            'title', 'description', 'assigned_date', 'due_date',
            'allow_late_submission', 'max_score', 'status', 'attachments',
            'notes', 'submission_count', 'graded_count', 'completion_rate',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        """Get teacher's full name."""
        if obj.teacher and obj.teacher.user:
            return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return None
    
    def get_lesson_info(self, obj):
        """Get lesson information."""
        if obj.lesson:
            return {
                'id': obj.lesson.id,
                'date': obj.lesson.date,
                'lesson_number': obj.lesson.lesson_number,
                'topic': obj.lesson.topic.title if obj.lesson.topic else None
            }
        return None
    
    def get_assessment_info(self, obj):
        """Get assessment information."""
        if obj.assessment:
            return {
                'id': obj.assessment.id,
                'title': obj.assessment.title,
                'type': obj.assessment.assessment_type.name,
                'max_score': str(obj.assessment.max_score),
                'date': obj.assessment.date
            }
        return None
    
    def get_submission_count(self, obj):
        """Get submission count."""
        return obj.get_submission_count()
    
    def get_graded_count(self, obj):
        """Get graded submission count."""
        return obj.get_graded_count()
    
    def get_completion_rate(self, obj):
        """Get completion rate."""
        return obj.get_completion_rate()
    
    def get_is_overdue(self, obj):
        """Check if overdue."""
        return obj.is_overdue()


class HomeworkCreateSerializer(serializers.ModelSerializer):
    """Create homework."""
    
    class Meta:
        model = Homework
        fields = [
            'class_subject', 'lesson', 'assessment', 'title', 'description',
            'assigned_date', 'due_date', 'allow_late_submission', 'max_score',
            'attachments', 'notes'
        ]
    
    def validate(self, attrs):
        """Validate homework data."""
        # Check due_date >= assigned_date
        if attrs.get('due_date') and attrs.get('assigned_date'):
            if attrs['due_date'] < attrs['assigned_date']:
                raise serializers.ValidationError({
                    'due_date': 'Topshirish muddati berilgan sanadan oldin bo\'lmasligi kerak.'
                })
        
        # Check lesson belongs to class_subject
        if attrs.get('lesson') and attrs.get('class_subject'):
            if attrs['lesson'].class_subject_id != attrs['class_subject'].id:
                raise serializers.ValidationError({
                    'lesson': 'Dars ushbu sinf faniga tegishli emas.'
                })
        
        # Check assessment belongs to class_subject
        if attrs.get('assessment') and attrs.get('class_subject'):
            if attrs['assessment'].class_subject_id != attrs['class_subject'].id:
                raise serializers.ValidationError({
                    'assessment': 'Nazorat ushbu sinf faniga tegishli emas.'
                })
        
        return attrs


class HomeworkUpdateSerializer(serializers.ModelSerializer):
    """Update homework."""
    
    class Meta:
        model = Homework
        fields = [
            'title', 'description', 'due_date', 'allow_late_submission',
            'max_score', 'status', 'attachments', 'notes'
        ]
    
    def validate_due_date(self, value):
        """Validate due date."""
        if value and self.instance.assigned_date:
            if value < self.instance.assigned_date:
                raise serializers.ValidationError(
                    'Topshirish muddati berilgan sanadan oldin bo\'lmasligi kerak.'
                )
        return value


class SubmissionListSerializer(serializers.ModelSerializer):
    """List submissions."""
    
    student_name = serializers.SerializerMethodField()
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = [
            'id', 'homework', 'homework_title', 'student', 'student_name',
            'submitted_at', 'status', 'is_late', 'score', 'graded_at',
            'created_at'
        ]
    
    def get_student_name(self, obj):
        """Get student's full name."""
        return obj.get_student_name()


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Detail view of submission."""
    
    student_name = serializers.SerializerMethodField()
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    homework_max_score = serializers.DecimalField(
        source='homework.max_score',
        read_only=True,
        max_digits=6,
        decimal_places=2
    )
    
    class Meta:
        model = HomeworkSubmission
        fields = [
            'id', 'homework', 'homework_title', 'homework_max_score',
            'student', 'student_name', 'submission_text', 'submitted_at',
            'status', 'is_late', 'score', 'teacher_feedback', 'graded_at',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['submitted_at', 'graded_at', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        """Get student's full name."""
        return obj.get_student_name()


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Create or update submission by student."""
    
    class Meta:
        model = HomeworkSubmission
        fields = ['homework', 'submission_text', 'attachments']
    
    def validate_homework(self, value):
        """Validate homework is active."""
        if value.status != HomeworkStatus.ACTIVE:
            raise serializers.ValidationError('Ushbu vazifa faol emas.')
        
        # Check if late submission is allowed
        if value.is_overdue() and not value.allow_late_submission:
            raise serializers.ValidationError('Muddatdan keyin topshirishga ruxsat berilmagan.')
        
        return value
    
    def create(self, validated_data):
        """Create submission and mark as submitted."""
        student = self.context['request'].user.student_profile
        homework = validated_data['homework']
        
        # Check if submission already exists
        submission, created = HomeworkSubmission.objects.get_or_create(
            homework=homework,
            student=student,
            defaults={
                'submission_text': validated_data.get('submission_text'),
                'attachments': validated_data.get('attachments', [])
            }
        )
        
        if not created:
            # Update existing submission
            submission.submission_text = validated_data.get('submission_text')
            submission.attachments = validated_data.get('attachments', [])
        
        # Submit
        submission.submit(
            submission_text=validated_data.get('submission_text'),
            attachments=validated_data.get('attachments')
        )
        
        return submission


class SubmissionGradeSerializer(serializers.ModelSerializer):
    """Grade submission by teacher."""
    
    class Meta:
        model = HomeworkSubmission
        fields = ['score', 'teacher_feedback']
    
    def validate_score(self, value):
        """Validate score."""
        if value is None:
            raise serializers.ValidationError('Ball kiritilishi shart.')
        
        homework = self.instance.homework
        if homework.max_score and value > homework.max_score:
            raise serializers.ValidationError(
                f'Ball maksimal balldan oshmasligi kerak ({homework.max_score})'
            )
        
        if value < 0:
            raise serializers.ValidationError('Ball manfiy bo\'lmasligi kerak.')
        
        return value
    
    def update(self, instance, validated_data):
        """Update and mark as graded."""
        instance.grade(
            score=validated_data['score'],
            feedback=validated_data.get('teacher_feedback')
        )
        return instance


class BulkGradeSerializer(serializers.Serializer):
    """Bulk grade multiple submissions."""
    
    grades = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1
    )
    
    def validate_grades(self, value):
        """Validate grades list."""
        for item in value:
            if 'submission_id' not in item:
                raise serializers.ValidationError('submission_id kerak.')
            if 'score' not in item:
                raise serializers.ValidationError('score kerak.')
        
        return value
    
    def save(self):
        """Grade all submissions."""
        grades_data = self.validated_data['grades']
        results = []
        errors = []
        
        for item in grades_data:
            try:
                submission = HomeworkSubmission.objects.get(
                    id=item['submission_id'],
                    deleted_at__isnull=True
                )
                
                score = float(item['score'])
                feedback = item.get('teacher_feedback', '')
                
                # Validate score
                if submission.homework.max_score and score > submission.homework.max_score:
                    errors.append({
                        'submission_id': str(submission.id),
                        'error': f'Ball maksimal balldan oshmasligi kerak ({submission.homework.max_score})'
                    })
                    continue
                
                submission.grade(score=score, feedback=feedback)
                results.append({
                    'submission_id': str(submission.id),
                    'student_name': submission.get_student_name(),
                    'score': str(score),
                    'status': 'success'
                })
                
            except HomeworkSubmission.DoesNotExist:
                errors.append({
                    'submission_id': item['submission_id'],
                    'error': 'Topshiriq topilmadi'
                })
            except Exception as e:
                errors.append({
                    'submission_id': item['submission_id'],
                    'error': str(e)
                })
        
        return {'results': results, 'errors': errors}


class StudentHomeworkStatisticsSerializer(serializers.Serializer):
    """Student homework statistics."""
    
    total_homework = serializers.IntegerField()
    submitted = serializers.IntegerField()
    not_submitted = serializers.IntegerField()
    late = serializers.IntegerField()
    graded = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=6, decimal_places=2)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class ClassHomeworkStatisticsSerializer(serializers.Serializer):
    """Class homework statistics."""
    
    total_homework = serializers.IntegerField()
    active_homework = serializers.IntegerField()
    closed_homework = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    average_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_score = serializers.DecimalField(max_digits=6, decimal_places=2)
