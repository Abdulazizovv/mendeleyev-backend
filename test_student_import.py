"""
O'quvchilarni Excel orqali import qilishni test qilish.

Usage:
    python test_student_import.py [--dry-run]
"""
import sys
import os
import django

# Django sozlamalarini yuklash
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.school.students.utils import parse_excel_file
from apps.branch.models import Branch
from auth.users.models import User
import json


def test_parse_excel():
    """Excel parsing funksiyasini test qilish."""
    print("=" * 50)
    print("Excel Parsing Test")
    print("=" * 50)
    
    # Excel faylni ochish
    excel_file_path = "students_sample.xlsx"
    
    if not os.path.exists(excel_file_path):
        print(f"❌ Excel fayl topilmadi: {excel_file_path}")
        print("Iltimos, students_sample.xlsx faylini yarating yoki yo'lini to'g'rilang.")
        return
    
    try:
        with open(excel_file_path, 'rb') as f:
            students_data = parse_excel_file(f)
        
        print(f"✅ Excel fayldan {len(students_data)} ta o'quvchi ma'lumoti o'qildi\n")
        
        # Birinchi 3 ta o'quvchini ko'rsatish
        for i, student in enumerate(students_data[:3], 1):
            print(f"O'quvchi {i}:")
            print(f"  Ism: {student['first_name']} {student['middle_name']} {student['last_name']}")
            print(f"  Telefon: {student['phone_number']}")
            print(f"  Jinsi: {student['gender']}")
            print(f"  Tug'ilgan sana: {student['date_of_birth']}")
            print(f"  Manzil: {student['address']}")
            print(f"  Guruh: {student['group_name']}")
            print(f"  Yaqinlar soni: {len(student['relatives'])}")
            
            for rel_idx, relative in enumerate(student['relatives'], 1):
                print(f"    Yaqin {rel_idx}:")
                print(f"      Turi: {relative['relationship_type']}")
                print(f"      Ism: {relative['first_name']} {relative['middle_name']} {relative['last_name']}")
                print(f"      Telefon: {relative['phone_number']}")
            print()
        
        if len(students_data) > 3:
            print(f"... va yana {len(students_data) - 3} ta o'quvchi\n")
    
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        import traceback
        traceback.print_exc()


def test_import_api(dry_run=False):
    """Import API ni test qilish."""
    print("=" * 50)
    print(f"Import API Test {'(Dry Run)' if dry_run else ''}")
    print("=" * 50)
    
    # Test uchun birinchi branch ni olish
    try:
        branch = Branch.objects.filter(deleted_at__isnull=True).first()
        if not branch:
            print("❌ Test uchun Branch topilmadi")
            return
        
        print(f"✅ Test uchun branch: {branch.name} ({branch.id})")
        
        # Test user (super_admin yoki branch_admin)
        from apps.branch.models import BranchMembership
        
        admin_membership = BranchMembership.objects.filter(
            role__in=['super_admin', 'branch_admin'],
            deleted_at__isnull=True
        ).first()
        
        if not admin_membership:
            print("❌ Test uchun admin user topilmadi")
            return
        
        print(f"✅ Test user: {admin_membership.user.phone_number}")
        
        # Excel faylni ochish
        excel_file_path = "students_sample.xlsx"
        
        if not os.path.exists(excel_file_path):
            print(f"❌ Excel fayl topilmadi: {excel_file_path}")
            return
        
        # Import qilish
        from apps.school.students.serializers import StudentImportSerializer
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/school/students/import/')
        request.user = admin_membership.user
        
        with open(excel_file_path, 'rb') as f:
            data = {
                'file': f,
                'branch_id': str(branch.id),
                'dry_run': dry_run
            }
            
            serializer = StudentImportSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                results = serializer.save()
                
                print(f"\n✅ Import natijasi:")
                print(f"  Jami: {results['total']}")
                print(f"  Muvaffaqiyatli: {results['success']}")
                print(f"  Xatolik: {results['failed']}")
                print(f"  O'tkazilgan: {results['skipped']}")
                
                if results['errors']:
                    print(f"\n❌ Xatoliklar ({len(results['errors'])}):")
                    for error in results['errors'][:5]:
                        print(f"  Qator {error['row']}: {error['error']}")
                        print(f"    O'quvchi: {error['student']}")
                
                if results['students']:
                    print(f"\n✅ Import qilingan o'quvchilar ({len(results['students'])} ta):")
                    for student in results['students'][:5]:
                        print(f"  - {student['name']} ({student['phone']}) - {student['status']}")
                
                if len(results['students']) > 5:
                    print(f"  ... va yana {len(results['students']) - 5} ta")
            else:
                print(f"❌ Validatsiya xatoligi:")
                print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    
    print("\n" + "=" * 50)
    print("O'QUVCHILARNI IMPORT QILISH TEST")
    print("=" * 50 + "\n")
    
    # 1. Excel parsing test
    test_parse_excel()
    
    # 2. Import API test
    test_import_api(dry_run=dry_run)
    
    print("\n" + "=" * 50)
    print("TEST TUGADI")
    print("=" * 50)
