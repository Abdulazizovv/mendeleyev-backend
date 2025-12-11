from rest_framework import serializers
from .models import Building, Room, RoomType


def normalize_equipment_items(equipment):
    normalized = []
    seen = set()
    for item in equipment:
        name = item['name']
        key = name.lower()
        if key in seen:
            raise serializers.ValidationError({'equipment': f"'{name}' nomli jihoz takrorlangan."})
        seen.add(key)
        normalized.append({
            'name': name,
            'quantity': item.get('quantity', 1),
            'unit': item.get('unit') or 'pcs',
        })
    return normalized
class EquipmentItemSerializer(serializers.Serializer):
    """Xona jihozlari elementi."""

    name = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=0, default=1)
    unit = serializers.CharField(max_length=20, allow_blank=True, required=False)

    def validate(self, attrs):
        attrs['name'] = attrs['name'].strip()
        if not attrs['name']:
            raise serializers.ValidationError({'name': 'Jihoz nomi bo\'sh bo\'lishi mumkin emas.'})
        attrs['unit'] = (attrs.get('unit') or 'pcs').strip() or 'pcs'
        return attrs



class BuildingSerializer(serializers.ModelSerializer):
    """Bino serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    rooms_count = serializers.SerializerMethodField()
    
    def get_rooms_count(self, obj):
        """Xonalar soni."""
        return obj.rooms.filter(deleted_at__isnull=True).count()
    
    class Meta:
        model = Building
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'address',
            'floors',
            'description',
            'is_active',
            'rooms_count',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'rooms_count']
    
    def get_rooms_count(self, obj):
        """Xonalar soni."""
        return obj.rooms.filter(deleted_at__isnull=True).count()


class BuildingCreateSerializer(serializers.ModelSerializer):
    """Bino yaratish uchun serializer."""
    
    class Meta:
        model = Building
        fields = [
            'name',
            'address',
            'floors',
            'description',
            'is_active',
        ]
        extra_kwargs = {
            'name': {'required': True},
        }


class RoomSerializer(serializers.ModelSerializer):
    """Xona serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    equipment = EquipmentItemSerializer(many=True, required=False)
    
    class Meta:
        model = Room
        fields = [
            'id',
            'branch',
            'branch_name',
            'building',
            'building_name',
            'name',
            'room_type',
            'room_type_display',
            'floor',
            'capacity',
            'equipment',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate room data."""
        branch = data.get('branch')
        building = data.get('building')
        floor = data.get('floor')
        
        if branch and building:
            # Building must belong to the same branch
            if building.branch != branch:
                raise serializers.ValidationError({
                    'building': 'Bino tanlangan filialga tegishli emas.'
                })
        
        if building and floor:
            # Floor must be within building floors
            if floor > building.floors:
                raise serializers.ValidationError({
                    'floor': f'Qavat binoning qavatlar sonidan ({building.floors}) oshib ketmasligi kerak.'
                })
        
        equipment = data.get('equipment')
        if equipment is not None:
            data['equipment'] = normalize_equipment_items(equipment)
        return data


class RoomCreateSerializer(serializers.ModelSerializer):
    """Xona yaratish uchun serializer."""
    equipment = EquipmentItemSerializer(many=True, required=False)
    
    class Meta:
        model = Room
        fields = [
            'building',
            'name',
            'room_type',
            'floor',
            'capacity',
            'equipment',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate room data."""
        branch = self.context.get('branch')
        building = data.get('building')
        floor = data.get('floor')
        
        if branch and building:
            # Building must belong to the same branch
            if building.branch != branch:
                raise serializers.ValidationError({
                    'building': 'Bino tanlangan filialga tegishli emas.'
                })
        
        if building and floor:
            # Floor must be within building floors
            if floor > building.floors:
                raise serializers.ValidationError({
                    'floor': f'Qavat binoning qavatlar sonidan ({building.floors}) oshib ketmasligi kerak.'
                })
        
        equipment = data.get('equipment')
        if equipment is not None:
            data['equipment'] = normalize_equipment_items(equipment)
        return data

