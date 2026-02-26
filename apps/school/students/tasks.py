"""
Celery tasks for student import operations
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.db.models import F

from apps.branch.models import BranchMembership, BranchRole
from auth.profiles.models import StudentProfile, StudentRelative
from auth.users.models import User
from .utils import parse_excel_file

logger = logging.getLogger(__name__)


def get_or_create_class(branch, class_name):
    """Sinf mavjudligini tekshiradi, bo'lmasa yaratadi (grade/section aniqlab)."""
    from apps.school.classes.models import Class
    from apps.school.academic.models import AcademicYear

    if not class_name:
        return None

    class_name = class_name.strip()

    # Mavjud sinfni topish
    class_obj = Class.objects.filter(
        branch=branch,
        name=class_name,
        deleted_at__isnull=True
    ).first()
    if class_obj:
        return class_obj

    # Academic year aniqlash (faol yoki so'nggi)
    academic_year = AcademicYear.objects.filter(is_active=True).order_by('-start_date').first()
    if not academic_year:
        academic_year = AcademicYear.objects.order_by('-start_date').first()
    if not academic_year:
        # Fallback: joriy yilni yaratish (1 yil davomida)
        today = timezone.now().date()
        academic_year = AcademicYear.objects.create(
            name=f"{today.year}-{today.year + 1}",
            start_date=today,
            end_date=today + timedelta(days=365),
            is_active=True,
        )

    # Grade va section ni parse qilish (masalan "9-B" -> grade=9, section=B)
    grade_level = None
    section = ''
    try:
        parts = class_name.replace(' ', '').split('-')
        grade_level = int(parts[0]) if parts and parts[0].isdigit() else None
        section = parts[1] if len(parts) > 1 else ''
    except Exception:
        grade_level = None
        section = ''

    class_obj = Class.objects.create(
        branch=branch,
        academic_year=academic_year,
        name=class_name,
        grade_level=grade_level or 1,
        section=section,
        description=f"Import orqali yaratilgan ({timezone.now().strftime('%Y-%m-%d')})"
    )
    return class_obj


def create_student_balance_transaction(branch, student_profile, amount, cash_register=None):
    """
    Student import qilinganda boshlang'ich balans uchun tranzaksiya yaratish.
    
    Bu funksiya:
    1. CashRegister'ni topadi yoki yaratadi (atomic)
    2. Transaction yaratadi (StudentBalance signalda avtomatik yangilanadi)
    3. Race condition'lardan himoyalaydi (select_for_update)
    
    Args:
        branch: Branch obyekti
        student_profile: StudentProfile obyekti
        amount: Boshlang'ich balans summasi (so'm)
        cash_register: (Optional) CashRegister obyekti
        
    Returns:
        Transaction obyekti yoki None (agar amount=0)
    """
    import logging
    from apps.school.finance.models import (
        CashRegister, Transaction, TransactionType, 
        TransactionStatus, PaymentMethod, StudentBalance
    )
    
    logger = logging.getLogger(__name__)
    
    # Agar balans 0 bo'lsa, tranzaksiya yaratmaslik
    if amount <= 0:
        logger.info(f"StudentProfile {student_profile.id}: balans=0, tranzaksiya yaratilmadi")
        return None
    
    try:
        with transaction.atomic():
            # 1. CashRegister topish yoki yaratish (atomic, race-safe)
            if not cash_register:
                cash_register, created = CashRegister.objects.select_for_update().get_or_create(
                    branch=branch,
                    name="Asosiy kassa",
                    defaults={
                        'description': 'Import jarayonida avtomatik yaratilgan asosiy kassa',
                        'balance': 0,
                        'is_active': True
                    }
                )
                if created:
                    logger.info(f"Yangi CashRegister yaratildi: {cash_register.id} ({branch.name})")
            
            # 2. StudentBalance ni lock qilish (race condition oldini olish)
            student_balance = StudentBalance.objects.select_for_update().get(
                student_profile=student_profile
            )
            
            # 3. Transaction yaratish
            transaction_obj = Transaction.objects.create(
                branch=branch,
                cash_register=cash_register,
                transaction_type=TransactionType.INCOME,
                status=TransactionStatus.COMPLETED,
                amount=amount,
                payment_method=PaymentMethod.CASH,
                description=f"Import: Boshlang'ich balans - {student_profile.user_branch.user.get_full_name()}",
                student_profile=student_profile,
                transaction_date=timezone.now(),
            )
            
            # 4. StudentBalance yangilash (atomic F() expression)
            student_balance.add_amount(amount)
            
            logger.info(
                f"Import tranzaksiyasi yaratildi: Student={student_profile.id}, "
                f"Amount={amount:,} so'm, Transaction={transaction_obj.id}"
            )
            
            return transaction_obj
            
    except Exception as e:
        logger.error(f"Balans tranzaksiyasi yaratishda xatolik: {str(e)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=3)
def import_students_task(self, file_content, branch_id, dry_run=False):
    """
    Celery task for importing students from Excel file
    
    Args:
        file_content: Binary content of the uploaded Excel file
        branch_id: UUID of the branch to import students into
        dry_run: If True, validate without creating records
        
    Returns:
        dict: {
            'total': int,
            'success': int,
            'failed': int,
            'skipped': int,
            'errors': list,
            'students': list
        }
    """
    import io
    import logging
    from apps.branch.models import Branch
    
    logger = logging.getLogger(__name__)
    logger.info(f"Import task boshlandi: dry_run={dry_run}, branch_id={branch_id}")
    
    try:
        # Get branch
        branch = Branch.objects.get(id=branch_id, deleted_at__isnull=True)
    except Branch.DoesNotExist:
        return {
            'total': 0,
            'success': 0,
            'failed': 1,
            'skipped': 0,
            'errors': [{'error': 'Filial topilmadi'}],
            'students': []
        }
    
    # Parse Excel file from bytes
    file_like = io.BytesIO(file_content)
    students_data = parse_excel_file(file_like)
    
    results = {
        'total': len(students_data),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'dry_run': dry_run,
        'errors': [],
        'students': []
    }
    
    if not students_data:
        return results
    
    # Dry run - faqat validatsiya qilish
    if dry_run:
        logger.info("DRY RUN rejimi - faqat validatsiya qilinmoqda, obyektlar yaratilmaydi")
        for student_data in students_data:
            phone = student_data['phone_number']
            
            # User tekshirish
            user = User.objects.filter(phone_number=phone).first()
            if user:
                # Membership tekshirish
                existing_membership = BranchMembership.objects.filter(
                    user=user,
                    branch=branch,
                    role=BranchRole.STUDENT,
                    deleted_at__isnull=True
                ).first()
                
                if existing_membership:
                    # StudentProfile tekshirish
                    existing_profile = StudentProfile.objects.filter(
                        user_branch=existing_membership,
                        deleted_at__isnull=True
                    ).first()
                    
                    if existing_profile:
                        results['skipped'] += 1
                        results['errors'].append({
                            'row': student_data['row_number'],
                            'error': f"O'quvchi {phone} allaqachon bu filialda ro'yxatdan o'tgan (ID: {existing_profile.personal_number})",
                            'student': f"{student_data['first_name']} {student_data['last_name']}"
                        })
                    else:
                        # Membership bor lekin profile yo'q - yaratiladi
                        results['success'] += 1
                else:
                    # User bor lekin bu filialda yo'q - yaratiladi
                    results['success'] += 1
            else:
                # Yangi user - yaratiladi
                results['success'] += 1
        
        logger.info(f"DRY RUN tugadi: total={results['total']}, will_create={results['success']}, already_exists={results['skipped']}")
        return results
    
    # Haqiqiy import - har bir studentni alohida transaction ichida
    logger.info("HAQIQIY IMPORT boshlandi - obyektlar yaratilmoqda")
    for student_data in students_data:
        try:
            with transaction.atomic():
                phone = student_data['phone_number']
                
                # 1. Telefon raqam bo'yicha User tekshirish
                user = User.objects.filter(phone_number=phone).first()
                
                if user:
                    # 2. User mavjud - bu filialda BranchMembership borligini tekshirish
                    membership = BranchMembership.objects.filter(
                        user=user,
                        branch=branch,
                        role=BranchRole.STUDENT,
                        deleted_at__isnull=True
                    ).first()
                    
                    if not membership:
                        # User bor, lekin bu filialda membership yo'q - yangi membership yaratish
                        membership = BranchMembership.objects.create(
                            user=user,
                            branch=branch,
                            role=BranchRole.STUDENT,
                            balance=0  # Balans tranzaksiya orqali qo'shiladi
                        )
                else:
                    # User yo'q - yangi User va BranchMembership yaratish
                    user = User.objects.create(
                        phone_number=phone,
                        first_name=student_data['first_name'],
                        last_name=student_data['last_name'],
                        phone_verified=False,
                    )
                    
                    membership = BranchMembership.objects.create(
                        user=user,
                        branch=branch,
                        role=BranchRole.STUDENT,
                        balance=0  # Balans tranzaksiya orqali qo'shiladi
                    )
                
                # 3. StudentProfile mavjudligini tekshirish (MUHIM: har doim tekshirish kerak!)
                existing_profile = StudentProfile.objects.filter(
                    user_branch=membership,
                    deleted_at__isnull=True
                ).first()
                
                if existing_profile:
                    # Student to'liq mavjud - skip qilish
                    results['skipped'] += 1
                    results['errors'].append({
                        'row': student_data['row_number'],
                        'error': f"O'quvchi {phone} allaqachon bu filialda ro'yxatdan o'tgan",
                        'student': f"{student_data['first_name']} {student_data['last_name']}",
                        'personal_number': existing_profile.personal_number
                    })
                    continue
                
                # 4. Sinf bilan bog'lash (agar sinf nomi mavjud bo'lsa)
                class_obj = None
                class_name = student_data.get('class_name')
                if class_name:
                    class_obj = get_or_create_class(branch, class_name)
                
                # 5. StudentProfile yaratish (faqat mavjud bo'lmasa)
                student_profile = StudentProfile.objects.create(
                    user_branch=membership,
                    middle_name=student_data.get('middle_name', ''),
                    date_of_birth=student_data.get('date_of_birth'),
                    gender=student_data.get('gender'),
                    address=student_data.get('address', ''),
                )
                
                # 6. Boshlang'ich balans uchun tranzaksiya yaratish (agar amount > 0)
                initial_balance = student_data.get('balance', 0)
                try:
                    initial_balance = int(initial_balance)
                except (TypeError, ValueError):
                    initial_balance = 0
                logger.info(f"Student yaratildi: {phone}, balance={initial_balance}")
                
                if initial_balance > 0:
                    try:
                        logger.info(f"Balans tranzaksiya yaratilmoqda: Student={phone}, Amount={initial_balance}")
                        txn = create_student_balance_transaction(
                            branch=branch,
                            student_profile=student_profile,
                            amount=initial_balance
                        )
                        logger.info(f"Balans tranzaksiya muvaffaqiyatli yaratildi: Transaction ID={txn.id}, Amount={initial_balance}")
                    except Exception as balance_error:
                        logger.error(
                            f"Balans tranzaksiyasi yaratishda xatolik: Student={phone}, "
                            f"Amount={initial_balance}, Error={str(balance_error)}",
                            exc_info=True
                        )
                        # Balans tranzaksiyasi xatosi butun import jarayonini to'xtatmasin
                        # Student yaratiladi lekin balanssiz
                else:
                    logger.info(f"Balans 0 yoki manfiy, tranzaksiya yaratilmadi: Student={phone}")
                
                # 7. O'quvchini sinfga qo'shish (agar sinf mavjud bo'lsa)
                if class_obj:
                    try:
                        from apps.school.classes.models import ClassStudent
                        
                        logger.info(f"Sinfga qo'shilmoqda: Student={phone}, Class={class_name}, Class ID={class_obj.id}")
                        
                        # Oldindan shu sinfda borligini tekshirish (membership orqali!)
                        existing_class_student = ClassStudent.objects.filter(
                            class_obj=class_obj,
                            membership=membership,  # BranchMembership
                            deleted_at__isnull=True
                        ).first()
                        
                        if not existing_class_student:
                            class_student = ClassStudent.objects.create(
                                class_obj=class_obj,
                                membership=membership,  # BranchMembership
                                enrollment_date=timezone.now().date()
                            )
                            logger.info(f"O'quvchi {phone} {class_name} sinfga MUVAFFAQIYATLI qo'shildi (ClassStudent ID: {class_student.id})")
                        else:
                            logger.info(f"O'quvchi {phone} allaqachon {class_name} sinfda mavjud")
                    except Exception as class_error:
                        logger.error(
                            f"Sinfga biriktrishda xatolik (student: {phone}, class: {class_name}): {str(class_error)}",
                            exc_info=True
                        )
                        # Sinfga biriktirish xatosidan o'quvchi yaratish to'xtatilmasin
                else:
                    logger.info(f"Sinf nomi yo'q yoki bo'sh: Student={phone}, class_name={class_name}")
                
                # Success
                results['success'] += 1
                results['students'].append({
                    'phone': phone,
                    'name': f"{student_data['first_name']} {student_data['last_name']}",
                    'personal_number': student_profile.personal_number,
                    'class': class_name if class_name else None
                })
                
        except Exception as e:
            # Error handling
            logger.error(
                f"Student import xatolik: Row={student_data['row_number']}, "
                f"Phone={student_data.get('phone_number', 'N/A')}, Error={str(e)}",
                exc_info=True
            )
            results['failed'] += 1
            results['errors'].append({
                'row': student_data['row_number'],
                'error': str(e),
                'student': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
            })
    
    return results
