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
from credit_subline.api.serializers import (
    CreditSublineSerializer,
    CreditAmountAdjustmentSerializer,
    CreditAmountAdjustmentStatusSerializer,
    InterestRateAdjustmentSerializer,
    InterestRateAdjustmentStatusSerializer,
    CreditSublineStatusAdjustmentSerializer,
    CreditSublineStatusAdjustmentStatusSerializer,
)
from credit_line.models import CreditLine
from credit_origination.api.views import (
    page_param,
    page_size_param,
    status_param,
)
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from accounts.api.permissions import IsSuperUser
from itertools import chain


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


@swagger_auto_schema(
    method="post",
    request_body=CreditAmountAdjustmentSerializer,
    responses={
        201: CreditAmountAdjustmentSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def credit_amount_adjustment_create(request, subline_pk):
    """
    Request a credit subline amount adjustment.


    Use this endpoint to create a credit subline amout adjustment associated with
    a specific credit subline.


    Only staff members can make this type of requests.
    """
    credit_subline = get_object_or_404(CreditSubline, id=subline_pk)

    if request.method == "POST":
        serializer = CreditAmountAdjustmentSerializer(
            data=request.data,
            context={"request": request, "credit_subline": credit_subline},
        )
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(credit_subline=credit_subline)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return Response(
        {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@swagger_auto_schema(
    method="patch",
    request_body=CreditAmountAdjustmentStatusSerializer,
    responses={
        200: CreditAmountAdjustmentStatusSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["PATCH"])
@permission_classes([IsSuperUser])
def credit_amount_adjustment_status_update(request, adj_pk):
    """
    Updates the 'adjustment_status' of a CreditAmountAdjustment instance.


    Ensuring the transition adheres to the defined status transition rules.


    This endpoint is crucial for managing the lifecycle of credit subline adjustments,
    facilitating a structured progression through each adjustment's review
    and implementation process. Only superusers are permitted to update
    adjustment statuses.
    """
    adjustment = get_object_or_404(CreditAmountAdjustment, pk=adj_pk)

    # Check if 'adjustment_status' is provided in the request data
    if "adjustment_status" not in request.data:
        return Response(
            {"error": "The 'adjustment_status' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CreditAmountAdjustmentStatusSerializer(
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
    method="post",
    request_body=InterestRateAdjustmentSerializer,
    responses={
        201: InterestRateAdjustmentSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def interest_rate_adjustment_create(request, subline_pk):
    """
    Request a credit subline interest rate adjustment.


    Use this endpoint to create a credit subline interest rate
    adjustment associated with a specific credit subline.


    Only staff members can make this type of requests.
    """
    credit_subline = get_object_or_404(CreditSubline, id=subline_pk)

    if request.method == "POST":
        serializer = InterestRateAdjustmentSerializer(
            data=request.data,
            context={"request": request, "credit_subline": credit_subline},
        )
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(credit_subline=credit_subline)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return Response(
        {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@swagger_auto_schema(
    method="patch",
    request_body=InterestRateAdjustmentStatusSerializer,
    responses={
        200: InterestRateAdjustmentStatusSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["PATCH"])
@permission_classes([IsSuperUser])
def interest_rate_adjustment_status_update(request, adj_pk):
    """
    Updates the 'adjustment_status' of a InterestRateAdjustment instance.

    Ensuring the transition adheres to the defined status transition rules.

    This endpoint is crucial for managing the lifecycle of credit subline adjustments,
    facilitating a structured progression through each adjustment's review
    and implementation process. Only superusers are permitted to update
    adjustment statuses.
    """
    adjustment = get_object_or_404(InterestRateAdjustment, pk=adj_pk)

    # Check if 'adjustment_status' is provided in the request data
    if "adjustment_status" not in request.data:
        return Response(
            {"error": "The 'adjustment_status' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = InterestRateAdjustmentStatusSerializer(
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
    method="post",
    request_body=CreditSublineStatusAdjustmentSerializer,
    responses={
        201: CreditSublineStatusAdjustmentSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def credit_subline_status_adjustment_create(request, subline_pk):
    """
    Request a credit subline status adjustment.


    Use this endpoint to create a credit subline status
    adjustment associated with a specific credit subline.


    Only staff members can make this type of requests.
    """
    credit_subline = get_object_or_404(CreditSubline, id=subline_pk)

    if request.method == "POST":
        serializer = CreditSublineStatusAdjustmentSerializer(
            data=request.data,
            context={"request": request, "credit_subline": credit_subline},
        )
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(credit_subline=credit_subline)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return Response(
        {"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@swagger_auto_schema(
    method="patch",
    request_body=CreditSublineStatusAdjustmentStatusSerializer,
    responses={
        200: CreditSublineStatusAdjustmentStatusSerializer,
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Unexpected Error",
    },
)
@api_view(["PATCH"])
@permission_classes([IsSuperUser])
def credit_subline_status_adjustment_status_update(request, adj_pk):
    """
    Updates the 'adjustment_status' of a CreditSublineStatusAdjustment instance.

    Ensuring the transition adheres to the defined status transition rules.

    The CreditSubline cannot be set to active when the associated CreditLine's
    status is not approved; adhering to the credit flow logic.

    This endpoint is crucial for managing the lifecycle of credit subline adjustments,
    facilitating a structured progression through each adjustment's review
    and implementation process.

    Only superusers are permitted to update adjustment statuses.
    """
    adjustment = get_object_or_404(CreditSublineStatusAdjustment, pk=adj_pk)

    # Check if 'adjustment_status' is provided in the request data
    if "adjustment_status" not in request.data:
        return Response(
            {"error": "The 'adjustment_status' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if adjusted_status is set to active and credit line's status
    if (
        request.data.get("adjustment_status") == "approved"
        and adjustment.adjusted_status == "active"
    ):
        credit_line_status = adjustment.credit_subline.credit_line.status
        if credit_line_status != "approved":
            return Response(
                {
                    "error": (
                        "The CreditSubline cannot be set to active because "
                        "the associated CreditLine's status is not approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = CreditSublineStatusAdjustmentStatusSerializer(
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


class CreditSublineAdjustmentsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


adjustment_type_param = openapi.Parameter(
    "type",
    openapi.IN_QUERY,
    description="Adjustment Type (amount, interest_rate, status)",
    type=openapi.TYPE_STRING,
)


adjustment_status_param = openapi.Parameter(
    "adjustment_status",
    openapi.IN_QUERY,
    description="Adjustment Status (e.g., pending_review, approved, rejected, implemented)",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(description="A paginated list of adjustments"),
        400: "Bad Request - Invalid request or query parameters",
        401: "Unauthorized - Authentication credentials were not provided or are invalid",
        403: "Forbidden - The user does not have permission to access this resource",
        404: "Not Found - The requested resource does not exist",
        500: "Internal Server Error - An error occurred on the server",
    },
    manual_parameters=[
        page_param,
        page_size_param,
        adjustment_type_param,
        adjustment_status_param,
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def credit_subline_adjustments_admin_list(request):
    """
    Retrieves a list of all credit subline adjustments.


    The list comes with pagination support,
    and allows filtering by adjustment type and adjustment status.


    If no type is specified, returns all adjustment types with
    an additional key specifying the type.


    Access is restricted for admin users only, enhancing privacy and security.
    """
    adjustment_type = request.query_params.get("type")
    adjustment_status = request.query_params.get("adjustment_status")

    paginator = CreditSublineAdjustmentsPagination()

    # Initially set to None to avoid unnecessary filtering.
    adjustments_query = None

    # Adjust the queries to include adjustment_status if it's provided.
    if adjustment_type == "amount":
        adjustments_query = CreditAmountAdjustment.objects.all()
    elif adjustment_type == "interest_rate":
        adjustments_query = InterestRateAdjustment.objects.all()
    elif adjustment_type == "status":
        adjustments_query = CreditSublineStatusAdjustment.objects.all()

    if adjustments_query is not None and adjustment_status:
        adjustments_query = adjustments_query.filter(
            adjustment_status=adjustment_status
        )

    if adjustments_query is None:
        # This means we need to fetch all types and possibly filter by status.
        queries = [
            CreditAmountAdjustment.objects.all(),
            InterestRateAdjustment.objects.all(),
            CreditSublineStatusAdjustment.objects.all(),
        ]
        if adjustment_status:
            queries = [q.filter(adjustment_status=adjustment_status) for q in queries]

        adjustments = list(chain(*queries))
        # Since it's a combined list from different types, sort it here.
        adjustments.sort(key=lambda x: x.effective_date, reverse=True)
    else:
        # If adjustments_query is not None, it's already filtered by type and status.
        adjustments = list(adjustments_query.order_by("-effective_date"))

    page = paginator.paginate_queryset(adjustments, request)
    results = []
    for adjustment in page:
        if isinstance(adjustment, CreditAmountAdjustment):
            serializer = CreditAmountAdjustmentSerializer(
                adjustment, context={"request": request}
            )
            result = serializer.data
            result["adjustment_type"] = "amount"
        elif isinstance(adjustment, InterestRateAdjustment):
            serializer = InterestRateAdjustmentSerializer(
                adjustment, context={"request": request}
            )
            result = serializer.data
            result["adjustment_type"] = "interest_rate"
        elif isinstance(adjustment, CreditSublineStatusAdjustment):
            serializer = CreditSublineStatusAdjustmentSerializer(
                adjustment, context={"request": request}
            )
            result = serializer.data
            result["adjustment_type"] = "status"
        results.append(result)

    return paginator.get_paginated_response(results)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(description="A specific adjustment details"),
        400: "Bad Request - Invalid request or query parameters",
        404: "Not Found - The requested adjustment does not exist",
    },
    manual_parameters=[
        openapi.Parameter(
            "type",
            openapi.IN_PATH,
            description="Type of adjustment (amount, interest_rate, status)",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            "adj_id",
            openapi.IN_PATH,
            description="ID of the specific adjustment",
            type=openapi.TYPE_INTEGER,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_credit_subline_adjustment(request, type, adj_id):
    """
    Retrieves a specific adjustment based on its type and ID.


    Supports fetching details for three types of adjustments:
    - amount
    - interest_rate
    - status


    Parameters:
    - type: The type of the adjustment (amount, interest_rate, status)
    - adj_id: The unique identifier for the adjustment


    Access is restricted to admin users only.
    """
    # Define the mapping from type to model and serializer
    model_map = {
        "amount": (CreditAmountAdjustment, CreditAmountAdjustmentSerializer),
        "interest_rate": (InterestRateAdjustment, InterestRateAdjustmentSerializer),
        "status": (
            CreditSublineStatusAdjustment,
            CreditSublineStatusAdjustmentSerializer,
        ),
    }

    if type not in model_map:
        return Response(
            {"error": "Invalid adjustment type"}, status=status.HTTP_400_BAD_REQUEST
        )

    model, serializer_class = model_map[type]
    adjustment = get_object_or_404(model, pk=adj_id)

    serializer = serializer_class(adjustment)
    return Response(serializer.data)
