from rest_framework import serializers
from credit_line.models import CreditLine


class CreditLineSerializer(serializers.ModelSerializer):
    """
    Serializer for CreditLine objects. Handles validation, creation,
    and updating of credit line records.
    Includes custom validation for credit limits,
    start and end dates, and related object types.
    """

    class Meta:
        model = CreditLine
        fields = [
            "id",
            "credit_limit",
            "currency",
            "start_date",
            "end_date",
            "status",
            "user",
            "created",
        ]
        read_only_fields = ("id", "created", "status")

    def validate_credit_limit(self, value):
        """
        Check that the credit limit is greater than 0 and does not exceed 12 digits.
        """
        if value <= 0:
            raise serializers.ValidationError("Credit limit must be greater than 0.")
        if len(str(value).replace(".", "").replace("-", "")) > 12:
            raise serializers.ValidationError("Credit limit must not exceed 12 digits.")
        return value

    def validate(self, data):
        """
        Check that the start_date is before the end_date.
        """
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if end_date and start_date >= end_date:
            raise serializers.ValidationError("Start date must be before the end date.")
        return data

    def create(self, validated_data):
        """
        Ensure full_clean() is called on model instance creation.
        """
        instance = CreditLine(**validated_data)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Ensure full_clean() is called on model instance update.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
