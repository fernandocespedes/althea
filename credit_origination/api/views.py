from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from credit_origination.models import CreditType, CreditRequest
from credit_origination.api.serializers import (
    CreditTypeSerializer,
    CreditTypeAdminSerializer,
    CreditRequestSerializer,
    CreditRequestStatusUpdateSerializer,
)
from datetime import timedelta
from django.utils.timezone import now
from django.db import transaction
from django.shortcuts import get_object_or_404


class CreditTypePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreditRequestsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


status_param = openapi.Parameter(
    "status",
    openapi.IN_QUERY,
    description="Filter by status",
    type=openapi.TYPE_STRING,
)

username_param = openapi.Parameter(
    "username",
    openapi.IN_QUERY,
    description="Filter by username",
    type=openapi.TYPE_STRING,
)

page_param = openapi.Parameter(
    "page",
    openapi.IN_QUERY,
    description="Page number",
    type=openapi.TYPE_INTEGER,
)

page_size_param = openapi.Parameter(
    "page_size",
    openapi.IN_QUERY,
    description="Number of items per page",
    type=openapi.TYPE_INTEGER,
)


@swagger_auto_schema(
    method="post",
    request_body=CreditTypeAdminSerializer,
    responses={201: CreditTypeAdminSerializer, 400: "Bad Request"},
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def credit_type_create(request):
    """
    Create a credit type

    Only authorized staff can do this.
    """
    serializer = CreditTypeAdminSerializer(data=request.data)
    try:
        with transaction.atomic():
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="put",
    request_body=CreditTypeAdminSerializer,
    responses={
        200: CreditTypeAdminSerializer(many=False),
        400: "Bad Request",
        404: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAdminUser])
def credit_type_update(request, pk):
    """
    Update a credit type description

    Only authorized staff can do this.
    """
    credit_type = get_object_or_404(CreditType, pk=pk)
    serializer = CreditTypeAdminSerializer(credit_type, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    responses={200: CreditTypeSerializer(many=True)},
    manual_parameters=[page_param, page_size_param],
)
@api_view(["GET"])
def credit_type_list(request):
    """
    Get a list of all available credit types

    Accessible for all users.
    """
    credit_types = CreditType.objects.all()
    paginator = CreditTypePagination()
    page = paginator.paginate_queryset(credit_types, request)
    if page is not None:
        serializer = CreditTypeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = CreditTypeSerializer(credit_types, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: CreditTypeAdminSerializer(many=True)},
    manual_parameters=[page_param, page_size_param],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_credit_type_list(request):
    """
    Get a list of all available credit types (Admin)

    Accessible for admin members.
    """
    credit_types = CreditType.objects.all()
    paginator = CreditTypePagination()
    page = paginator.paginate_queryset(credit_types, request)
    if page is not None:
        serializer = CreditTypeAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = CreditTypeAdminSerializer(credit_types, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="delete",
    responses={
        204: "No Content",
        404: "Not Found",
        403: "Forbidden",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_credit_type(request, pk):
    """
    Delete a credit type

    Only authorized staff can do this.
    """
    try:
        credit_type = CreditType.objects.get(pk=pk)
    except CreditType.DoesNotExist:
        return Response(
            {"error": "Credit type not found"}, status=status.HTTP_404_NOT_FOUND
        )

    credit_type.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method="post",
    request_body=CreditRequestSerializer,
    responses={201: CreditRequestSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_user_credit_request(request):
    """
    Create a credit request for users

    Use this endpoint to create a credit request associated with the
    currently authenticated user.
    """
    modified_data = request.data.copy()
    modified_data["user"] = request.user.pk

    serializer = CreditRequestSerializer(data=modified_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="put",
    request_body=CreditRequestSerializer,
    responses={200: CreditRequestSerializer},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_credit_request(request, pk):
    """
    Update credit requests made by a user

    Requests cannot be updated after 48 hours of creation
    or if the status is different from "pending".
    """
    try:
        credit_request = CreditRequest.objects.get(
            pk=pk,
            user=request.user,
        )
    except CreditRequest.DoesNotExist:
        return Response(
            {"error": "Credit request not found."}, status=status.HTTP_404_NOT_FOUND
        )

    # Check if the status is not "pending" or if more than 48 hours have passed
    if credit_request.status != "pending" or now() - credit_request.created > timedelta(
        hours=48
    ):
        return Response(
            {
                "error": "Cannot update the request after 48 hours or if the status isn't pending."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CreditRequestSerializer(
        credit_request, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    responses={200: CreditRequestSerializer(many=True)},
    manual_parameters=[page_param, page_size_param, status_param, username_param],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_requests_admin_list(request):
    """
    Get all credit requests made by users

    Only staff members can access this endpoint.

    Pagination and size of pages can be added to the path in a request.
    """
    status_filter = request.query_params.get("status", None)
    username_filter = request.query_params.get("username", None)

    credit_requests = CreditRequest.objects.all()

    if status_filter:
        credit_requests = credit_requests.filter(status=status_filter)

    if username_filter:
        credit_requests = credit_requests.filter(user__username=username_filter)

    paginator = CreditRequestsPagination()
    page = paginator.paginate_queryset(credit_requests, request)
    if page is not None:
        serializer = CreditRequestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = CreditRequestSerializer(credit_requests, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: CreditRequestSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_credit_requests(request):
    """
    List credit requests by authenticated user.

    This endpoint lists credit requests made by the authenticated user.
    """
    credit_requests = CreditRequest.objects.filter(user=request.user)
    serializer = CreditRequestSerializer(credit_requests, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="put",
    request_body=CreditRequestStatusUpdateSerializer,
    responses={
        200: CreditRequestStatusUpdateSerializer(many=False),
        400: "Bad Request",
        404: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAdminUser])
def credit_request_status_update(request, pk):
    """
    Update a credit request status

    Only admin users can access this endpoint.
    """
    credit_request = get_object_or_404(CreditRequest, pk=pk)
    serializer = CreditRequestStatusUpdateSerializer(credit_request, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
