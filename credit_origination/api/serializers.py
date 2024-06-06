from rest_framework import serializers
from credit_origination.models import CreditType


class CreditTypeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditType
        fields = "__all__"
        read_only_fields = ("id", "created")


class CreditTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditType
        fields = ["id", "name", "description", "created"]
        read_only_fields = ("id", "name", "description", "created")
