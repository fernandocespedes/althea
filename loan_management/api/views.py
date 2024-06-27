from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from loan_management.api.serializers import (
    LoanTermSerializer,
    UpdateLoanTermStatusSerializer,
)
from loan_management.models import LoanTerm
from credit_subline.models import CreditSubline
from accounts.api.permissions import IsSuperUser


@swagger_auto_schema(
    method="post",
    request_body=LoanTermSerializer,
    responses={
        201: LoanTermSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def loan_term_create(request, subline_pk):
    """
    Create a LoanTerm entry.

    Use this endpoint to create a loan term
    associated with a specific credit subline.

    Only staff members can make this type of requests.

    The status field is a read-only one, as well as the
    credit_subline, since we will get the latter from the context.
    """
    credit_subline = get_object_or_404(CreditSubline, pk=subline_pk)

    if request.method == "POST":
        serializer = LoanTermSerializer(
            data=request.data,
            context={"request": request, "credit_subline": credit_subline},
        )
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        return Response(
            {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@swagger_auto_schema(
    method="patch",
    request_body=UpdateLoanTermStatusSerializer,
    responses={
        200: UpdateLoanTermStatusSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["PATCH"])
@permission_classes([IsSuperUser])
def loan_term_status_update(request, loan_term_pk):
    """
    Updates the 'status' of a LoanTerm instance.

    Ensuring the transition adheres to the defined status transition rules.

    This endpoint is crucial for managing the lifecycle of loan term status,
    facilitating a structured progression and implementation process.

    Only superusers are permitted to update loan term statuses.
    """
    loan_term = get_object_or_404(LoanTerm, pk=loan_term_pk)

    # Check if 'status' is provided in the request data
    if "status" not in request.data:
        return Response(
            {"error": "The 'status' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = UpdateLoanTermStatusSerializer(
        loan_term, data=request.data, partial=True
    )

    try:
        with transaction.atomic():
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
    except ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@swagger_auto_schema(
    method="get",
    responses={
        200: LoanTermSerializer(),
        401: "Unauthorized - Authentication credentials were not provided or are invalid",
        404: "Not Found - The requested resource could not be found",
    },
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def loan_term_detail(request, loan_term_pk):
    """
    Retrieves a specific loan term by its ID.

    Access is restricted to staff members only.
    """
    try:
        loan_term = LoanTerm.objects.get(pk=loan_term_pk)
    except LoanTerm.DoesNotExist:
        # logger.error(f"CreditLineAdjustment with ID {pk} not found.")
        return Response(
            {"error": f"LoanTerm with ID {loan_term_pk} not found."}, status=404
        )

    serializer = LoanTermSerializer(loan_term, context={"request": request})
    return Response(serializer.data)
