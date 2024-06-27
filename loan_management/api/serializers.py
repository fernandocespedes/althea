from loan_management.models import LoanTerm
from django.core.exceptions import ValidationError
from rest_framework import serializers


class LoanTermSerializer(serializers.ModelSerializer):
    """
    Serializer for LoanTerm objects. Handles validation
    and creation, of loan term records.

    The 'credit_subline' is expected to be passed through the context,
    not directly in the serialized data, to maintain a clean separation of concerns.
    """

    class Meta:
        model = LoanTerm
        fields = [
            "id",
            "credit_subline",
            "term_length",
            "repayment_frequency",
            "payment_due_day",
            "created",
            "updated",
            "start_date",
            "status",
        ]
        read_only_fields = ["credit_subline", "status"]

    def validate(self, attrs):
        # Use existing instance if this is an update
        if self.instance:
            instance = self.instance
            for attr, value in attrs.items():
                setattr(instance, attr, value)
        else:
            instance = LoanTerm(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        # Check if a LoanTerm already exists for the credit_subline if this is a create action
        if not self.instance and "credit_subline" in self.context:
            existing_terms = LoanTerm.objects.filter(
                credit_subline=self.context["credit_subline"]
            )
            if existing_terms.exists():
                raise serializers.ValidationError(
                    {
                        "credit_subline": "A LoanTerm already exists for this CreditSubline."
                    }
                )

        return attrs

    def create(self, validated_data):
        """
        Creates a new LoanTerm instance using context data for the credit_subline.
        """
        # Try to get 'credit_subline' from the context
        credit_subline = self.context.get("credit_subline")

        if not credit_subline:
            raise serializers.ValidationError(
                {"credit_subline": "This field is required."}
            )

        # If credit_subline is provided, create the LoanTerm with it
        loan_term = LoanTerm.objects.create(
            credit_subline=credit_subline, **validated_data
        )
        return loan_term


class UpdateLoanTermStatusSerializer(serializers.ModelSerializer):
    """
    Focuses on updating the 'status' of a LoanTerm entry, ensuring that changes
    are permissible and align with defined status transition rules.

    This serializer is key to managing the lifecycle of loan term status adjustments,
    allowing for a structured and traceable progression of each adjustment's review
    and implementation process.
    """

    class Meta:
        model = LoanTerm
        fields = [
            "id",
            "credit_subline",
            "term_length",
            "repayment_frequency",
            "payment_due_day",
            "created",
            "updated",
            "start_date",
            "status",
        ]
        read_only_fields = [
            "id",
            "credit_subline",
            "term_length",
            "repayment_frequency",
            "payment_due_day",
            "created",
            "updated",
            "start_date",
        ]

    def update(self, instance, validated_data):
        # Update the status field
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        return instance

    def create(self, validated_data):
        # Prevent creation of new instances
        raise serializers.ValidationError(
            "Creation of LoanTerm instances is not supported by this serializer."
        )

    def validate_status(self, value):
        if self.instance and value == self.instance.status:
            # The new status is the same as the current one; this is fine for idempotency
            return value

        allowed_transitions = {
            "pending": ["approved", "rejected"],
            "approved": [],
            "rejected": [],
        }
        current_status = self.instance.status if self.instance else None

        if (
            current_status not in allowed_transitions
            or value not in allowed_transitions[current_status]
        ):
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}."
            )

        return value
