from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.branch.models import Branch
from apps.school.rooms.models import Building, Room

User = get_user_model()


class BuildingModelTests(TestCase):
    """Building model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
    
    def test_create_building(self):
        """Bino yaratish testi."""
        building = Building.objects.create(
            branch=self.branch,
            name="Asosiy bino",
            address="Toshkent shahar",
            floors=3,
            description="Asosiy o'quv binosi",
            created_by=self.user
        )
        self.assertEqual(building.name, "Asosiy bino")
        self.assertEqual(building.floors, 3)
        self.assertTrue(building.is_active)


class RoomModelTests(TestCase):
    """Room model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.building = Building.objects.create(
            branch=self.branch,
            name="Asosiy bino",
            floors=3
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
    
    def test_create_room(self):
        """Xona yaratish testi."""
        room = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="101",
            room_type="classroom",
            floor=1,
            capacity=30,
            created_by=self.user
        )
        self.assertEqual(room.name, "101")
        self.assertEqual(room.room_type, "classroom")
        self.assertEqual(room.floor, 1)
        self.assertEqual(room.capacity, 30)
    
    def test_room_floor_validation(self):
        """Xona qavat validatsiyasi testi."""
        # Qavat binoning qavatlar sonidan oshib ketmasligi kerak
        with self.assertRaises(ValueError):
            Room.objects.create(
                branch=self.branch,
                building=self.building,
                name="401",
                room_type="classroom",
                floor=4,  # Bino faqat 3 qavatli
                capacity=30,
                created_by=self.user
            )
    
    def test_room_building_validation(self):
        """Xona bino validatsiyasi testi."""
        # Boshqa filialga tegishli bino qo'shishga urinish
        other_branch = Branch.objects.create(
            name="Other School",
            slug="other-school",
            type="school",
            status="active"
        )
        other_building = Building.objects.create(
            branch=other_branch,
            name="Boshqa bino",
            floors=2
        )
        
        with self.assertRaises(ValueError):
            Room.objects.create(
                branch=self.branch,
                building=other_building,  # Boshqa filialga tegishli
                name="201",
                room_type="classroom",
                floor=1,
                capacity=30,
                created_by=self.user
            )

