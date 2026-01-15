from rest_framework import serializers
from .models import Class, ClassStudent
from apps.branch.models import BranchMembership
from apps.school.academic.models import AcademicYear


class ClassSerializer(serializers.ModelSerializer):
    """Sinf serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    class_teacher_name = serializers.SerializerMethodField()
    current_students_count = serializers.IntegerField(read_only=True)
    can_add_student = serializers.BooleanField(read_only=True)
    
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
            'current_students_count',
            'can_add_student',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_class_teacher_name(self, obj):
        """O'qituvchi to'liq ismi."""
        if obj.class_teacher:
            user = obj.class_teacher.user
            return user.get_full_name() or user.phone_number
        return None
    
    def validate(self, data):
        """Validate class data."""
        branch = data.get('branch')
        academic_year = data.get('academic_year')
        class_teacher = data.get('class_teacher')
        
        # Academic year must belong to the branch
        if branch and academic_year:
            if academic_year.branch != branch:
                raise serializers.ValidationError({
                    'academic_year': 'Akademik yil tanlangan filialga tegishli emas.'
                })
        
        # Class teacher must belong to the branch and be a teacher
        if class_teacher:
            if class_teacher.branch != branch:
                raise serializers.ValidationError({
                    'class_teacher': 'O\'qituvchi tanlangan filialga tegishli emas.'
                })
            if class_teacher.role != 'teacher':
                raise serializers.ValidationError({
                    'class_teacher': 'Tanlangan a\'zolik o\'qituvchi roliga ega emas.'
                })
        
        return data


class ClassCreateSerializer(serializers.ModelSerializer):
    """Sinf yaratish uchun serializer."""
    
    class Meta:
        model = Class
        fields = [
            'branch',
            'academic_year',
            'name',
            'grade_level',
            'section',
            'class_teacher',
            'max_students',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate class data."""
        branch = data.get('branch')
        academic_year = data.get('academic_year')
        class_teacher = data.get('class_teacher')
        
        # Academic year must belong to the branch
        if branch and academic_year:
            if academic_year.branch != branch:
                raise serializers.ValidationError({
                    'academic_year': 'Akademik yil tanlangan filialga tegishli emas.'
                })
        
        # Class teacher must belong to the branch and be a teacher
        if class_teacher:
            if class_teacher.branch != branch:
                raise serializers.ValidationError({
                    'class_teacher': 'O\'qituvchi tanlangan filialga tegishli emas.'
                })
            if class_teacher.role != 'teacher':
                raise serializers.ValidationError({
                    'class_teacher': 'Tanlangan a\'zolik o\'qituvchi roliga ega emas.'
                })
        
        return data


class ClassStudentSerializer(serializers.ModelSerializer):
    """Sinf o'quvchisi serializer."""
    
    student_name = serializers.SerializerMethodField()
    student_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
    student_id = serializers.UUIDField(source='membership.user.id', read_only=True)
    student_user_id = serializers.UUIDField(source='membership.user.id', read_only=True)
    membership_id = serializers.UUIDField(source='membership.id', read_only=True)
    student_balance = serializers.IntegerField(source='membership.balance', read_only=True)
    
    class Meta:
        model = ClassStudent
        fields = [
            'id',
            'class_obj',
            'membership',
            'membership_id',
            'student_id',
            'student_user_id',
            'student_name',
            'student_phone',
            'student_balance',
            'enrollment_date',
            'is_active',
            'notes',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'enrollment_date', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_student_name(self, obj):
        """O'quvchi to'liq ismi."""
        user = obj.membership.user
        return user.get_full_name() or user.phone_number
    
    def validate(self, data):
        """Validate student enrollment."""
        class_obj = data.get('class_obj') or self.instance.class_obj if self.instance else None
        membership = data.get('membership') or (self.instance.membership if self.instance else None)
        
        if class_obj and membership:
            # Check if membership is a student
            if membership.role != 'student':
                raise serializers.ValidationError({
                    'membership': 'A\'zolik o\'quvchi roliga ega bo\'lishi kerak.'
                })
            
            # Check if membership belongs to the same branch as class
            if membership.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'membership': 'O\'quvchi sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
            
            # Check if class can accept more students
            if not class_obj.can_add_student() and not self.instance:
                raise serializers.ValidationError({
                    'membership': f'Sinf to\'ldi. Maksimal o\'quvchilar soni: {class_obj.max_students}'
                })
        
        return data

    


class ClassStudentCreateSerializer(serializers.ModelSerializer):
    """Sinf o'quvchisi qo'shish uchun serializer."""
    
    class Meta:
        model = ClassStudent
        fields = [
            'membership',
            'is_active',
            'notes',
        ]
    
    def validate(self, data):
        """Validate student enrollment."""
        membership = data.get('membership')
        class_obj = self.context.get('class_obj')
        
        if class_obj and membership:
            # Check if membership is a student
            if membership.role != 'student':
                raise serializers.ValidationError({
                    'membership': 'A\'zolik o\'quvchi roliga ega bo\'lishi kerak.'
                })
            
            # Check if membership belongs to the same branch as class
            if membership.branch != class_obj.branch:
                raise serializers.ValidationError({
                    'membership': 'O\'quvchi sinf bilan bir xil filialga tegishli bo\'lishi kerak.'
                })
            
            # Check if class can accept more students
            if not class_obj.can_add_student():
                raise serializers.ValidationError({
                    'membership': f'Sinf to\'ldi. Maksimal o\'quvchilar soni: {class_obj.max_students}'
                })
            
            # Check if student is already enrolled in any class in the branch
            if ClassStudent.objects.filter(
                class_obj__branch=class_obj.branch,
                membership=membership,
                deleted_at__isnull=True
            ).exists():
                raise serializers.ValidationError({
                    'membership': 'Bu o\'quvchi allaqachon filialdagi boshqa sinfga qo\'shilgan.'
                })
        
        return data


class ClassStudentTransferSerializer(serializers.Serializer):
    """O'quvchini bir sinfdan boshqasiga transfer qilish uchun serializer."""
    target_class_id = serializers.UUIDField()
    enrollment_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        from_class: Class = self.context.get('from_class')
        class_student: ClassStudent = self.context.get('class_student')

        try:
            target_class = Class.objects.get(id=attrs['target_class_id'], deleted_at__isnull=True)
        except Class.DoesNotExist:
            raise serializers.ValidationError({'target_class_id': 'Target class not found or deleted'})

        if target_class.branch_id != from_class.branch_id:
            raise serializers.ValidationError({'target_class_id': 'Target class must be in the same branch'})

        if target_class.id == from_class.id:
            raise serializers.ValidationError({'target_class_id': 'Target class must be different'})

        exists = ClassStudent.objects.filter(
            class_obj_id=target_class.id,
            membership_id=class_student.membership_id,
            deleted_at__isnull=True,
        ).exists()
        if exists:
            raise serializers.ValidationError({'target_class_id': 'Student already enrolled in target class'})

        attrs['target_class'] = target_class
        return attrs

