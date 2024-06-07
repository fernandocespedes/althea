from rest_framework import serializers
from credit_origination.models import CreditType, CreditRequest


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


class CreditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ["id", "credit_type", "amount", "term", "created", "user", "status"]
        read_only_fields = ["id", "created", "status"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        if len(str(value).replace(".", "").replace("-", "")) > 12:
            raise serializers.ValidationError("Amount must not exceed 12 digits.")
        return value

    def validate_term(self, value):
        if not (0 < value <= 120):
            raise serializers.ValidationError(
                "Term must be greater than 0 and less than or equal to 120."
            )
        return value

    def validate(self, data):
        # Add any additional validations if needed
        return data


class CreditRequestStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ["status"]
        read_only_fields = ["id", "credit_type", "amount", "term", "created", "user"]

    def validate_status(self, value):
        if value not in dict(CreditRequest.CREDIT_REQUEST_STATUS).keys():
            raise serializers.ValidationError("Invalid status.")
        return value
