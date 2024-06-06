from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from credit_origination.models import (
    CreditType,
)
from credit_origination.api.serializers import (
    CreditTypeSerializer,
    CreditTypeAdminSerializer,
)

from django.db import transaction
from django.shortcuts import get_object_or_404


class CreditTypePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


page_param = openapi.Parameter(
    "page",
    openapi.IN_QUERY,
    description="Page number of the results to retrieve",
    type=openapi.TYPE_INTEGER,
)
page_size_param = openapi.Parameter(
    "page_size",
    openapi.IN_QUERY,
    description="Number of results per page",
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
