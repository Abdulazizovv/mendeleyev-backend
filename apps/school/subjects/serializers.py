from rest_framework import serializers
from .models import Subject, ClassSubject
from apps.branch.models import BranchMembership
from apps.school.classes.models import Class


class SubjectSerializer(serializers.ModelSerializer):
    """Fan serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Subject
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'code',
            'description',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class SubjectCreateSerializer(serializers.ModelSerializer):
    """Fan yaratish uchun serializer."""
    
    class Meta:
        model = Subject
        fields = [
            'branch',
            'name',
            'code',
            'description',
            'is_active',
        ]


class ClassSubjectSerializer(serializers.ModelSerializer):
    """Sinf fani serializer."""
    
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    quarter_name = serializers.CharField(source='quarter.name', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = [
            'id',
            'class_obj',
            'class_name',
            'subject',
            'subject_name',
            'subject_code',
            'teacher',
            'teacher_name',
            'hours_per_week',
            'quarter',
            'quarter_name',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_teacher_name(self, obj):
        """O'qituvchi to'liq ismi."""
        if obj.teacher:
            user = obj.teacher.user
            return user.get_full_name() or user.phone_number
        return None
    
    def validate(self, data):
        """Validate class subject data."""
        class_obj = data.get('class_obj') or (self.instance.class_obj if self.instance else None)
        subject = data.get('subject') or (self.instance.subject if self.instance else None)
        teacher = data.get('teacher')
        quarter = data.get('quarter')
        
        if class_obj and subject:
            # Subject must belong to the same branch
            if subject.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'subject': 'Fan sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
        
        if class_obj and teacher:
            # Teacher must belong to the same branch and be a teacher
            if teacher.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'teacher': 'O\'qituvchi sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
            if teacher.role != 'teacher':
                raise serializers.ValidationError({
                    'teacher': 'Tanlangan a\'zolik o\'qituvchi roliga ega emas.'
                })
        
        if class_obj and quarter:
            # Quarter must belong to the same academic year
            if quarter.academic_year != class_obj.academic_year:
                raise serializers.ValidationError({
                    'quarter': 'Chorak sinf bilan bir xil akademik yilga tegishli bo\'lishi kerak.'
                })
        
        return data


class ClassSubjectCreateSerializer(serializers.ModelSerializer):
    """Sinfga fan qo'shish uchun serializer."""
    
    class Meta:
        model = ClassSubject
        fields = [
            'subject',
            'teacher',
            'hours_per_week',
            'quarter',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate class subject data."""
        class_obj = self.context.get('class_obj')
        subject = data.get('subject')
        teacher = data.get('teacher')
        quarter = data.get('quarter')
        
        if class_obj and subject:
            # Subject must belong to the same branch
            if subject.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'subject': 'Fan sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
            
            # Check if subject is already added to class
            if ClassSubject.objects.filter(
                class_obj=class_obj,
                subject=subject,
                deleted_at__isnull=True
            ).exists():
                raise serializers.ValidationError({
                    'subject': 'Bu fan allaqachon sinfga qo\'shilgan.'
                })
        
        if class_obj and teacher:
            # Teacher must belong to the same branch and be a teacher
            if teacher.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'teacher': 'O\'qituvchi sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
            if teacher.role != 'teacher':
                raise serializers.ValidationError({
                    'teacher': 'Tanlangan a\'zolik o\'qituvchi roliga ega emas.'
                })
        
        if class_obj and quarter:
            # Quarter must belong to the same academic year
            if quarter.academic_year != class_obj.academic_year:
                raise serializers.ValidationError({
                    'quarter': 'Chorak sinf bilan bir xil akademik yilga tegishli bo\'lishi kerak.'
                })
        
        return data

