from rest_framework import serializers
from credit_line.models import CreditLine, CreditLineAdjustment
from decimal import Decimal


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


class CreditLineAdjustmentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating CreditLineAdjustment instances.
    Includes custom field validation and object-level validation
    to ensure the integrity of adjustments. The 'credit_line' is expected to be passed
    through the context, not directly in the serialized data, to avoid redundancy
    and enforce cleaner separation of concerns.
    """

    credit_line_id = serializers.IntegerField(source="credit_line.id", read_only=True)

    class Meta:
        model = CreditLineAdjustment
        exclude = ["credit_line"]
        read_only_fields = (
            "id",
            "credit_line_id",
            "previous_credit_limit",
            "previous_end_date",
            "previous_currency",
            "previous_status",
            "adjustment_date",
            "adjustment_status",
        )

    def validate_new_credit_limit(self, value):
        """
        Validate that the new credit limit is positive and does not
        exceed the maximum allowed limit.
        """
        if value <= 0:
            raise serializers.ValidationError("Credit limit must be greater than 0.")
        max_limit = Decimal("1000000000.00")
        if value > max_limit:
            raise serializers.ValidationError(
                f"New credit limit cannot exceed {max_limit}."
            )
        return value

    def validate_new_status(self, value):
        # Obtain the previous status
        previous_status = (
            self.instance.credit_line.status
            if self.instance and hasattr(self.instance, "credit_line")
            else None
        )

        # allow idempotent operations
        if previous_status == value:
            return value

        # allowed transitions from each status
        allowed_transitions = {
            None: [
                "pending",
                "approved",
                "rejected",
                None,
            ],
            "pending": [
                "approved",
                "rejected",
                "pending",
            ],
            "rejected": ["rejected"],
            "approved": ["approved"],
        }

        # Check if the transition from the current (previous) status to the new value is allowed
        if value not in allowed_transitions.get(previous_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {previous_status} to {value}."
            )

        return value

    def to_representation(self, instance):
        """
        Modifies the way that the credit line adjustment instances
        are converted to a dictionary representation.
        """
        rep = super().to_representation(instance)
        rep.update(
            {
                "previous_credit_limit": instance.credit_line.credit_limit,
                "previous_end_date": instance.credit_line.end_date,
                "previous_currency": instance.credit_line.currency,
                "previous_status": instance.credit_line.status,
            }
        )
        return rep

    def validate(self, attrs):
        """
        Object-level validation to ensure the credit line is
        specified and other validations related to the credit line.
        """
        if not self.instance:
            if "credit_line" not in attrs:
                credit_line = self.context.get("credit_line")
                if not credit_line:
                    raise serializers.ValidationError(
                        {"credit_line": "This field is required."}
                    )
                attrs["credit_line"] = credit_line

        credit_line = attrs.get(
            "credit_line", self.instance.credit_line if self.instance else None
        )
        new_end_date = attrs.get("new_end_date")

        if new_end_date and new_end_date <= credit_line.start_date:
            raise serializers.ValidationError(
                {"new_end_date": "End date must be after the start date."}
            )

        return attrs

    def create(self, validated_data):
        """
        Creates a new CreditLineAdjustment instance using the validated
        data and the credit line from the context.
        """
        credit_line = self.context.get("credit_line")
        validated_data["credit_line"] = credit_line
        return CreditLineAdjustment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Updates an existing CreditLineAdjustment instance.
        'credit_line' is not expected to change during updates, so it is ignored if passed.
        """
        validated_data.pop("credit_line", None)
        return super().update(instance, validated_data)


class CreditLineAdjustmentStatusSerializer(serializers.ModelSerializer):
    """
    Focuses on updating the 'adjustment_status' of a CreditLineAdjustment,
    ensuring that changes are permissible and align with defined status transition rules.

    It supports additional actions tied to specific status changes,
    such as updating the 'adjustment_date' to the current date when the status
    transitions to 'implemented'.

    This serializer is key to managing the lifecycle
    of credit line adjustments, allowing for a structured and traceable
    progression of each adjustment's review and implementation process.
    """

    credit_line = CreditLineSerializer(read_only=True)

    class Meta:
        model = CreditLineAdjustment
        fields = ["id", "credit_line", "adjustment_date", "adjustment_status", "reason"]
        read_only_fields = ("id", "credit_line", "adjustment_date")

    def validate_adjustment_status(self, value):
        if self.instance and value == self.instance.adjustment_status:
            # The new status is the same as the current one; this is fine for idempotency
            return value

        allowed_transitions = {
            "pending_review": ["approved", "rejected"],
            "approved": ["implemented"],
            "rejected": [],
            "implemented": [],
        }
        current_status = self.instance.adjustment_status if self.instance else None

        if (
            current_status not in allowed_transitions
            or value not in allowed_transitions[current_status]
        ):
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}."
            )

        return value
