from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.db import transaction
from credit_subline.api.serializers import CreditSublineSerializer
from credit_line.models import CreditLine
from credit_origination.api.views import (
    page_param,
    page_size_param,
    status_param,
)
from credit_subline.models import CreditSubline


class CreditSublinesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@swagger_auto_schema(
    method="post",
    request_body=CreditSublineSerializer,
    responses={
        201: CreditSublineSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def credit_subline_create(request, credit_line_pk):
    """
    Create a credit subline


    Use this endpoint to create a credit subline associated with a specific credit line.


    Only staff members can make this type of requests.
    """
    credit_line = get_object_or_404(CreditLine, pk=credit_line_pk)

    if request.method == "POST":
        serializer = CreditSublineSerializer(
            data=request.data, context={"request": request, "credit_line": credit_line}
        )
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(credit_line=credit_line)
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
    method="get",
    responses={
        200: openapi.Response(
            description="A paginated list of credit sublines",
            schema=CreditSublineSerializer(many=True),
        ),
        400: "Bad Request - Invalid request or query parameters",
        401: "Unauthorized - Authentication credentials were not provided or are invalid",
        403: "Forbidden - The user does not have permission to access this resource",
        404: "Not Found - The requested resource does not exist",
        500: "Internal Server Error - An error occurred on the server",
    },
    manual_parameters=[page_param, page_size_param, status_param],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_sublines_admin_list(request):
    """
    Retrieves the list of all credit sublines with pagination support.

    Access is restricted to staff members only.

    Pagination parameters can be adjusted via query parameters.
    """
    status = request.query_params.get("status")

    query_set = CreditSubline.objects.all().order_by("-created")

    if status:
        query_set = query_set.filter(status=status)

    paginator = CreditSublinesPagination()
    page = paginator.paginate_queryset(query_set, request)
    if page is not None:
        serializer = CreditSublineSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    serializer = CreditSublineSerializer(
        query_set, many=True, context={"request": request}
    )
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            description="Details of a specific credit subline",
            schema=CreditSublineSerializer(),
        ),
        400: "Bad Request - Invalid request or query parameters",
        401: "Unauthorized - Authentication credentials were not provided or are invalid",
        403: "Forbidden - The user does not have permission to access this resource",
        404: "Not Found - The requested resource does not exist",
        500: "Internal Server Error - An error occurred on the server",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_credit_subline(request, pk):
    """
    Retrieves the details of a specific credit subline.

    Access is restricted to the authenticated user.
    """
    try:
        credit_subline = CreditSubline.objects.get(
            pk=pk, credit_line__user=request.user
        )
    except CreditSubline.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CreditSublineSerializer(credit_subline, context={"request": request})
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            description="A list of credit sublines associated with the specified credit line",
            schema=CreditSublineSerializer(many=True),
        ),
        401: "Unauthorized - Authentication credentials were not provided or are invalid",
        404: "Not Found - The requested Credit sublines info could not be found",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_account_credit_sublines(request, credit_line_pk):
    """
    Retrieve all credit sublines associated with the authenticated user's credit line.

    This endpoint allows users to get detailed information
    about all sublines of their credit line by the credit line's unique identifier.

    Access is restricted to ensure that users can only view credit sublines
    they are authorized to see, enhancing privacy and security.
    """
    user = request.user

    credit_line = get_object_or_404(CreditLine, pk=credit_line_pk, user=user)

    # Retrieve all CreditSublines associated with the CreditLine
    credit_sublines = credit_line.creditsubline_set.all()
    serializer = CreditSublineSerializer(
        credit_sublines, many=True, context={"request": request}
    )

    return Response(serializer.data)
