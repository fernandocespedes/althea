from rest_framework import serializers
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from decimal import Decimal
from django.utils import timezone


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


class CreditAmountAdjustmentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating CreditAmountAdjustment instances for credit sublines.
    Includes custom field validation and object-level validation
    to ensure the integrity of adjustments. The 'credit_subline' is expected to be passed
    through the context, not directly in the serialized data, to avoid redundancy
    and enforce cleaner separation of concerns.
    """

    credit_subline_id = serializers.IntegerField(
        source="credit_subline.id", read_only=True
    )

    class Meta:
        model = CreditAmountAdjustment
        exclude = ["credit_subline"]
        read_only_fields = (
            "id",
            "credit_subline_id",
            "initial_amount",
            "effective_date",
            "adjustment_status",
        )

    def validate_adjusted_amount(self, value):
        """
        Validate that the adjusted amount is positive and does not
        exceed the maximum allowed limit.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        max_limit = Decimal("1000000000.00")
        if value > max_limit:
            raise serializers.ValidationError(
                "Adjusted amount cannot exceed {max_limit}."
            )
        return value

    def to_representation(self, instance):
        """
        Modifies the way that the credit amount adjustment instances
        are converted to a dictionary representation.


        Removes 'credit_subline' from the representation and adds readable
        fields from the associated credit subline.
        """
        rep = super().to_representation(instance)
        rep["initial_amount"] = instance.credit_subline.subline_amount
        return rep

    def validate(self, attrs):
        """
        Object-level validation to ensure the credit subline is
        specified and other validations related to the credit subline.
        """
        if "credit_subline" not in attrs:
            credit_subline = self.context.get("credit_subline")
            if not credit_subline:
                raise serializers.ValidationError(
                    {"credit_subline": "This field is required."}
                )
            attrs["credit_subline"] = credit_subline

        return attrs

    def create(self, validated_data):
        """
        Creates a new CreditAmountAdjustment instance using the validated
        data and the credit subline from the context.
        """
        credit_subline = validated_data.pop(
            "credit_subline", None
        )  # Ensure 'credit_subline' is not duplicated
        adjustment = CreditAmountAdjustment.objects.create(
            credit_subline=credit_subline, **validated_data
        )
        return adjustment

    def update(self, instance, validated_data):
        """
        Updates an existing CreditAmountAdjustment instance.
        'credit_subline' is not expected to change during updates, so it is ignored if passed.
        """
        validated_data.pop("credit_subline", None)
        return super().update(instance, validated_data)


class CreditAmountAdjustmentStatusSerializer(serializers.ModelSerializer):
    """
    Focuses on updating the 'adjustment_status' of a CreditAmountAdjustment entry,
    ensuring that changes are permissible and align with defined status transition rules.


    It supports additional actions tied to specific status changes,
    such as updating the 'effective_date' to the current date when the status
    transitions to 'implemented'.


    This serializer is key to managing the lifecycle
    of credit subline adjustments, allowing for a structured and traceable
    progression of each adjustment's review and implementation process.
    """

    credit_subline = CreditSublineSerializer(read_only=True)

    class Meta:
        model = CreditAmountAdjustment
        fields = [
            "id",
            "credit_subline",
            "effective_date",
            "adjustment_status",
        ]
        read_only_fields = ("id", "credit_subline", "effective_date")

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

    def update(self, instance, validated_data):
        new_adjustment_status = validated_data.get("adjustment_status")
        if (
            instance.adjustment_status == "approved"
            and new_adjustment_status == "implemented"
        ):
            # Ensure only the date part is saved
            instance.effective_date = timezone.now().date()
        instance.adjustment_status = new_adjustment_status
        instance.save()
        return instance


class InterestRateAdjustmentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating InterestRateAdjustment instances for credit sublines.
    Includes custom field validation to ensure the integrity of interest rate adjustments.


    The 'credit_subline' is expected to be passed through the context,
    not directly in the serialized data, to maintain a clean separation of concerns.
    """

    credit_subline_id = serializers.IntegerField(
        source="credit_subline.id", read_only=True
    )

    class Meta:
        model = InterestRateAdjustment
        exclude = ["credit_subline"]
        read_only_fields = (
            "id",
            "credit_subline_id",
            "initial_interest_rate",
            "effective_date",
            "adjustment_status",
        )

    def validate_adjusted_interest_rate(self, value):
        """
        Validate that the adjusted interest rate is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Interest rate must be greater than 0.")
        return value

    def to_representation(self, instance):
        """
        Modifies the way that interest rate adjustment instances
        are converted to dictionary representation.


        Removes 'credit_subline' from the representation and adds
        the initial_interest_rate from the associated credit subline.
        """
        rep = super().to_representation(instance)
        rep["initial_interest_rate"] = instance.credit_subline.interest_rate
        return rep

    def validate(self, attrs):
        """
        Object-level validation to ensure the credit subline is specified.
        """
        if "credit_subline" not in attrs:
            credit_subline = self.context.get("credit_subline")
            if not credit_subline:
                raise serializers.ValidationError(
                    {"credit_subline": "This field is required."}
                )
            attrs["credit_subline"] = credit_subline
        return attrs

    def create(self, validated_data):
        """
        Creates a new InterestRateAdjustment instance using the
        validated data and the credit subline from the context.
        """
        credit_subline = validated_data.pop(
            "credit_subline", None
        )  # Ensure 'credit_subline' is not duplicated
        adjustment = InterestRateAdjustment.objects.create(
            credit_subline=credit_subline, **validated_data
        )
        return adjustment

    def update(self, instance, validated_data):
        """
        Updates an existing InterestRateAdjustment instance.'credit_subline' is not
        expected to change during updates, so it is ignored if passed.
        """
        validated_data.pop("credit_subline", None)
        return super().update(instance, validated_data)


class InterestRateAdjustmentStatusSerializer(serializers.ModelSerializer):
    """
    Focuses on updating the 'adjustment_status' of a InterestRateAdjustment entry,
    ensuring that changes are permissible and align with defined status transition rules.

    It supports additional actions tied to specific status changes,
    such as updating the 'effective_date' to the current date when the status
    transitions to 'implemented'.

    This serializer is key to managing the lifecycle
    of credit subline adjustments, allowing for a structured and traceable
    progression of each adjustment's review and implementation process.
    """

    credit_subline = CreditSublineSerializer(read_only=True)

    class Meta:
        model = InterestRateAdjustment
        fields = [
            "id",
            "credit_subline",
            "effective_date",
            "adjustment_status",
        ]
        read_only_fields = ("id", "credit_subline", "effective_date")

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


class CreditSublineStatusAdjustmentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating CreditSublineStatusAdjustment
    instances for credit sublines.
    …
    """

    credit_subline_id = serializers.IntegerField(
        source="credit_subline.id", read_only=True
    )

    class Meta:
        model = CreditSublineStatusAdjustment
        exclude = ["credit_subline"]
        read_only_fields = (
            "id",
            "credit_subline_id",
            "initial_status",
            "effective_date",
            "adjustment_status",
        )

    def to_representation(self, instance):
        """
        Modifies the way that subline status adjustment instances
        are converted to dictionary representation.
        …
        """
        rep = super().to_representation(instance)
        rep["initial_status"] = instance.credit_subline.status
        return rep

    def validate(self, attrs):
        """
        Object-level validation to ensure the credit subline is specified.
        """
        if "credit_subline" not in attrs:
            credit_subline = self.context.get("credit_subline")
            if not credit_subline:
                raise serializers.ValidationError(
                    {"credit_subline": "This field is required."}
                )
            attrs["credit_subline"] = credit_subline
        return attrs

    def validate_adjusted_status(self, value):
        if self.instance and hasattr(self.instance, "credit_subline"):
            initial_status = self.instance.credit_subline.status
        else:
            # For new instances, retrieve the credit_subline from the context
            credit_subline = self.context.get("credit_subline")
            initial_status = credit_subline.status if credit_subline else None

        # allow idempotent operations
        if initial_status == value:
            return value

        # allowed transitions from each status
        allowed_transitions = {
            None: [
                "pending",
                "active",
                "inactive",
                None,
            ],
            "pending": [
                "pending",
                "active",
                "inactive",
            ],
            "inactive": ["inactive"],
            "active": ["active"],
        }

        # Check if the transition from the current (previous) status to the new value is allowed
        if value not in allowed_transitions.get(initial_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {initial_status} to {value}."
            )

        return value

    def create(self, validated_data):
        """
        Creates a new CreditSublineStatusAdjustment instance using the
        validated data and the credit subline from the context.
        """
        credit_subline = validated_data.pop(
            "credit_subline", None
        )  # Ensure 'credit_subline' is not duplicated
        adjustment = CreditSublineStatusAdjustment.objects.create(
            credit_subline=credit_subline, **validated_data
        )
        return adjustment

    def update(self, instance, validated_data):
        """
        Updates an existing CreditSublineStatusAdjustment instance.'credit_subline' is not
        expected to change during updates, so it is ignored if passed.
        """
        validated_data.pop("credit_subline", None)
        return super().update(instance, validated_data)


class CreditSublineStatusAdjustmentStatusSerializer(serializers.ModelSerializer):
    """
    Focuses on updating the 'adjustment_status' of a CreditSublineStatusAdjustment entry,
    ensuring that changes are permissible and align with defined status transition rules.

    It supports additional actions tied to specific status changes,
    such as updating the 'effective_date' to the current date when the status
    transitions to 'implemented'.

    This serializer is key to managing the lifecycle
    of credit subline status adjustments, allowing for a structured and traceable
    progression of each adjustment's review and implementation process.
    """

    credit_subline = CreditSublineSerializer(read_only=True)

    class Meta:
        model = CreditSublineStatusAdjustment
        fields = [
            "id",
            "credit_subline",
            "effective_date",
            "adjustment_status",
        ]
        read_only_fields = ("id", "credit_subline", "effective_date")

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
