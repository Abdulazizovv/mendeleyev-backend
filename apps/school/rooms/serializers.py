from rest_framework import serializers
from .models import Building, Room, RoomType


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
            'branch',
            'name',
            'address',
            'floors',
            'description',
            'is_active',
        ]


class RoomSerializer(serializers.ModelSerializer):
    """Xona serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    
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
        
        return data


class RoomCreateSerializer(serializers.ModelSerializer):
    """Xona yaratish uchun serializer."""
    
    class Meta:
        model = Room
        fields = [
            'branch',
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
        
        return data

