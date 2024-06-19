from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from credit_line.models import CreditLine, CreditLineAdjustment
from credit_line.api.serializers import (
    CreditLineSerializer,
    CreditLineAdjustmentSerializer,
    CreditLineAdjustmentStatusSerializer,
)
from credit_origination.api.views import page_param, page_size_param, status_param
from django.db import transaction
from django.shortcuts import get_object_or_404
from accounts.api.permissions import IsSuperUser


class CreditLinesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreditLineAdjustmentsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


user_param = openapi.Parameter(
    "user",
    openapi.IN_QUERY,
    description="Filter by user ID",
    type=openapi.TYPE_INTEGER,
)


@swagger_auto_schema(
    method="get",
    responses={200: CreditLineSerializer(many=False)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_credit_line(request, pk):
    """
    Get My Credit Line.

    Retrieve a specific credit line directly associated with the authenticated user.
    """
    user = request.user

    try:
        credit_line = CreditLine.objects.get(pk=pk, user=user.id)
    except CreditLine.DoesNotExist:
        return Response(
            {"error": "Credit line not found."}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = CreditLineSerializer(credit_line)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: CreditLineSerializer(many=True)},
    manual_parameters=[status_param, user_param, page_param, page_size_param],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_lines_admin_list(request):
    """
    Credit Lines Admin List.

    Get the credit lines of all users with optional filtering by status and user ID.
    """
    status_filter = request.query_params.get("status")
    user_filter = request.query_params.get("user")

    credit_lines = CreditLine.objects.all()

    if status_filter:
        credit_lines = credit_lines.filter(status=status_filter)

    if user_filter:
        credit_lines = credit_lines.filter(user__id=user_filter)

    paginator = CreditLinesPagination()
    page = paginator.paginate_queryset(credit_lines, request)
    if page is not None:
        serializer = CreditLineSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = CreditLineSerializer(credit_lines, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    request_body=CreditLineAdjustmentSerializer,
    responses={
        201: CreditLineAdjustmentSerializer,
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def credit_line_adjustment_create(request, pk):
    """
    Request a credit line adjustment.

    Only staff members can make this type of requests.
    """
    credit_line = get_object_or_404(CreditLine, id=pk)

    serializer = CreditLineAdjustmentSerializer(
        data=request.data, context={"request": request, "credit_line": credit_line}
    )
    try:
        with transaction.atomic():
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@swagger_auto_schema(
    method="patch",
    request_body=CreditLineAdjustmentStatusSerializer,
    responses={
        200: CreditLineAdjustmentStatusSerializer,
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["PATCH"])
@permission_classes([IsSuperUser])
def credit_line_adjustment_status_update(request, pk):
    """
    Updates the 'adjustment_status' of a CreditLineAdjustment instance.

    Only superusers are permitted to update adjustment statuses.
    """
    adjustment = get_object_or_404(CreditLineAdjustment, pk=pk)

    if "adjustment_status" not in request.data:
        return Response(
            {"error": "The 'adjustment_status' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CreditLineAdjustmentStatusSerializer(
        adjustment, data=request.data, partial=True
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
        200: CreditLineAdjustmentSerializer(many=True),
        401: "Unauthorized",
    },
    manual_parameters=[page_param, page_size_param],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_line_adjustments_admin_list(request):
    """
    Retrieves the list of all credit line adjustments with pagination support.

    Access is restricted to staff members only.
    """
    paginator = CreditLineAdjustmentsPagination()
    query_set = CreditLineAdjustment.objects.all().order_by("-adjustment_date")

    page = paginator.paginate_queryset(query_set, request)
    if page is not None:
        serializer = CreditLineAdjustmentSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    serializer = CreditLineAdjustmentSerializer(
        query_set, many=True, context={"request": request}
    )
    return Response(serializer.data)


response_schema_dict = {
    "200": openapi.Response(
        description="Retrieves a specific credit line adjustment by its ID",
        schema=CreditLineAdjustmentSerializer(),
    ),
    "401": "Unauthorized",
    "404": "Not found",
}


@swagger_auto_schema(method="get", responses=response_schema_dict)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_line_adjustment_detail(request, pk):
    """
    Retrieves a specific credit line adjustment by its ID.

    Access is restricted to staff members only.
    """
    adjustment = get_object_or_404(CreditLineAdjustment, pk=pk)

    serializer = CreditLineAdjustmentSerializer(
        adjustment, context={"request": request}
    )
    return Response(serializer.data)
