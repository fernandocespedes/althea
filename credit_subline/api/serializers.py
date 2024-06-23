from rest_framework import serializers
from credit_subline.models import CreditSubline


class CreditSublineSerializer(serializers.ModelSerializer):
    credit_line_id = serializers.IntegerField(source="credit_line.id", read_only=True)

    class Meta:
        model = CreditSubline
        fields = [
            "id",
            "credit_line_id",
            "subline_type",
            "subline_amount",
            "amount_disbursed",
            "outstanding_balance",
            "interest_rate",
            "status",
            "created",
            "updated",
        ]
        read_only_fields = ["status", "created", "updated", "credit_line_id"]

    def validate(self, data):
        """
        Perform custom validation for decimal fields and ensure credit_line is set.
        """
        # Validation for decimal fields to ensure they are greater than 0
        decimal_fields = [
            "subline_amount",
            "amount_disbursed",
            "outstanding_balance",
            "interest_rate",
        ]
        for field in decimal_fields:
            if field in data and data[field] < 0:
                raise serializers.ValidationError(
                    {field: f"{field} must be greater than 0."}
                )

        return data

    def create(self, validated_data):
        """
        Creates a new CreditSubline instance using context data.
        """
        # Pop 'credit_line' from validated_data to avoid duplicating it in the create call
        credit_line = validated_data.pop("credit_line", None) or self.context.get(
            "credit_line"
        )

        if not credit_line:
            raise serializers.ValidationError(
                {"credit_line": "This field is required."}
            )

        # Now, 'credit_line' is not in validated_data anymore, so it won't conflict
        credit_subline = CreditSubline.objects.create(
            credit_line=credit_line, **validated_data
        )
        return credit_subline

    def update(self, instance, validated_data):
        """
        Updates an existing CreditSubline instance.
        """

        return super().update(instance, validated_data)
