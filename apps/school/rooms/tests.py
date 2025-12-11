from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.branch.models import Branch, BranchMembership
from apps.school.rooms.models import Building, Room
from apps.school.rooms.serializers import RoomCreateSerializer

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

    def test_recreate_building_after_soft_delete(self):
        building = Building.objects.create(
            branch=self.branch,
            name="Asosiy bino",
            floors=3,
            created_by=self.user
        )
        building.delete()
        recreated = Building.objects.create(
            branch=self.branch,
            name="Asosiy bino",
            floors=2,
            created_by=self.user
        )
        self.assertNotEqual(building.id, recreated.id)
        self.assertEqual(recreated.floors, 2)

    def test_building_delete_sets_inactive(self):
        building = Building.objects.create(
            branch=self.branch,
            name="Holat testi",
            floors=2,
            created_by=self.user
        )
        self.assertTrue(building.is_active)
        building.delete()
        building.refresh_from_db()
        self.assertFalse(building.is_active)
        self.assertIsNotNone(building.deleted_at)

    def test_building_restore_sets_active(self):
        building = Building.objects.create(
            branch=self.branch,
            name="Restore bino",
            floors=2,
            created_by=self.user
        )
        building.delete()
        building.restore()
        building.refresh_from_db()
        self.assertTrue(building.is_active)
        self.assertIsNone(building.deleted_at)


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

    def test_recreate_room_after_soft_delete(self):
        room = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="101",
            room_type="classroom",
            floor=1,
            capacity=30,
            created_by=self.user
        )
        room.delete()
        recreated = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="101",
            room_type="classroom",
            floor=1,
            capacity=28,
            created_by=self.user
        )
        self.assertNotEqual(room.id, recreated.id)
        self.assertEqual(recreated.capacity, 28)

    def test_room_delete_sets_inactive(self):
        room = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="Delete test",
            room_type="classroom",
            floor=1,
            capacity=20,
            created_by=self.user
        )
        room.delete()
        room.refresh_from_db()
        self.assertFalse(room.is_active)
        self.assertIsNotNone(room.deleted_at)

    def test_room_restore_sets_active(self):
        room = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="Restore test",
            room_type="classroom",
            floor=1,
            capacity=20,
            created_by=self.user
        )
        room.delete()
        room.restore()
        room.refresh_from_db()
        self.assertTrue(room.is_active)
        self.assertIsNone(room.deleted_at)


class RoomSerializerTests(TestCase):
    """Room serializer validatsiya testlari."""

    def setUp(self):
        self.branch = Branch.objects.create(
            name="Serializer School",
            slug="serializer-school",
            type="school",
            status="active"
        )
        self.building = Building.objects.create(
            branch=self.branch,
            name="Serializer Bino",
            floors=2
        )

    def test_room_serializer_accepts_structured_equipment(self):
        data = {
            'building': str(self.building.id),
            'name': 'Lab-1',
            'room_type': 'lab',
            'floor': 1,
            'capacity': 20,
            'equipment': [
                {'name': 'Microscope', 'quantity': 5, 'unit': 'pcs'},
                {'name': 'Computer', 'quantity': 10, 'unit': 'pcs'},
            ],
            'is_active': True,
        }
        serializer = RoomCreateSerializer(data=data, context={'branch': self.branch})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        room = serializer.save(branch=self.branch)
        self.assertEqual(len(room.equipment), 2)
        self.assertEqual(room.equipment[0]['name'], 'Microscope')
        self.assertEqual(room.equipment[1]['quantity'], 10)

    def test_room_serializer_rejects_duplicate_equipment(self):
        data = {
            'building': str(self.building.id),
            'name': 'Lab-2',
            'room_type': 'lab',
            'floor': 1,
            'capacity': 15,
            'equipment': [
                {'name': 'Projector', 'quantity': 1},
                {'name': 'projector', 'quantity': 2},
            ],
            'is_active': True,
        }
        serializer = RoomCreateSerializer(data=data, context={'branch': self.branch})
        self.assertFalse(serializer.is_valid())
        self.assertIn('equipment', serializer.errors)


class RoomApiSoftDeleteTests(APITestCase):
    """Ensure soft-deleted buildings/xonalar ro'yxatlarga qaytmaydi."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone_number="+998907777777",
            password="testpass123"
        )
        self.branch = Branch.objects.create(
            name="API School",
            slug="api-school",
            type="school",
            status="active"
        )
        BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role='branch_admin'
        )
        self.client.force_authenticate(self.user)

        self.building_active = Building.objects.create(
            branch=self.branch,
            name="Faol bino",
            floors=2
        )
        self.building_deleted = Building.objects.create(
            branch=self.branch,
            name="Deleted bino",
            floors=1
        )
        self.building_deleted.delete()

        self.room_active = Room.objects.create(
            branch=self.branch,
            building=self.building_active,
            name="101",
            room_type="classroom",
            floor=1,
            capacity=30
        )
        self.room_deleted = Room.objects.create(
            branch=self.branch,
            building=self.building_active,
            name="102",
            room_type="classroom",
            floor=1,
            capacity=25
        )
        self.room_deleted.delete()

    def _results(self, response):
        data = response.data
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

    def test_building_list_excludes_soft_deleted(self):
        url = reverse('rooms:building-list', kwargs={'branch_id': self.branch.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        items = self._results(resp)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['id'], str(self.building_active.id))

    def test_building_detail_404_when_deleted(self):
        url = reverse('rooms:building-detail', kwargs={'branch_id': self.branch.id, 'id': self.building_deleted.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_room_list_excludes_soft_deleted(self):
        url = reverse('rooms:room-list', kwargs={'branch_id': self.branch.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        items = self._results(resp)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['id'], str(self.room_active.id))

    def test_room_detail_404_when_deleted(self):
        url = reverse('rooms:room-detail', kwargs={'branch_id': self.branch.id, 'id': self.room_deleted.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

