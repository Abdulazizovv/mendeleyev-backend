from rest_framework import serializers
from .models import Subject, ClassSubject
from apps.branch.models import BranchMembership
from apps.school.classes.models import Class


class SubjectSerializer(serializers.ModelSerializer):
    """Fan serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    color = serializers.RegexField(r'^#(?:[0-9a-fA-F]{6})$', required=False, allow_blank=True)
    
    class Meta:
        model = Subject
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'code',
            'description',
            'color',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class SubjectCreateSerializer(serializers.ModelSerializer):
    """Fan yaratish uchun serializer."""
    
    color = serializers.RegexField(r'^#(?:[0-9a-fA-F]{6})$', required=False, allow_blank=True)
    class Meta:
        model = Subject
        fields = [
            'branch',
            'name',
            'code',
            'description',
            'color',
            'is_active',
        ]


class SubjectDetailSerializer(serializers.ModelSerializer):
    """Fan detallari uchun kengaytirilgan serializer.

    Qo'shimcha statistik ma'lumotlar: sinflar soni, faol sinflar, o'qituvchilar.
    """
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    color = serializers.RegexField(r'^#(?:[0-9a-fA-F]{6})$', required=False, allow_blank=True)
    total_classes = serializers.SerializerMethodField()
    active_classes = serializers.SerializerMethodField()
    teachers = serializers.SerializerMethodField()
    class_subjects = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'branch', 'branch_name', 'name', 'code', 'description', 'color', 'is_active',
            'total_classes', 'active_classes', 'teachers', 'class_subjects',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_total_classes(self, obj):
        return obj.class_subjects.filter(deleted_at__isnull=True).count()

    def get_active_classes(self, obj):
        return obj.class_subjects.filter(is_active=True, deleted_at__isnull=True).count()

    def get_teachers(self, obj):
        memberships = obj.class_subjects.filter(
            teacher__isnull=False,
            deleted_at__isnull=True
        ).select_related('teacher__user')
        seen = {}
        for cs in memberships:
            u = cs.teacher.user
            if u.id not in seen:
                seen[u.id] = {
                    'id': str(u.id),
                    'phone_number': u.phone_number,
                    'full_name': u.get_full_name() or '',
                }
        return list(seen.values())

    def get_class_subjects(self, obj):
        qs = obj.class_subjects.filter(deleted_at__isnull=True).select_related(
            'class_obj', 'teacher', 'teacher__user', 'quarter'
        )
        data = []
        for cs in qs:
            data.append({
                'id': str(cs.id),
                'class_id': str(cs.class_obj.id),
                'class_name': cs.class_obj.name,
                'hours_per_week': cs.hours_per_week,
                'is_active': cs.is_active,
                'teacher': (
                    {
                        'id': str(cs.teacher.user.id),
                        'full_name': cs.teacher.user.get_full_name() or cs.teacher.user.phone_number,
                        'phone_number': cs.teacher.user.phone_number
                    } if cs.teacher else None
                ),
                'quarter': (
                    {
                        'id': str(cs.quarter.id),
                        'name': cs.quarter.name,
                        'number': cs.quarter.number
                    } if cs.quarter else None
                )
            })
        return data


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

