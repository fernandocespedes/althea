from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from credit_line.models import CreditLine
from credit_line.api.serializers import CreditLineSerializer
from credit_origination.api.views import page_param, page_size_param, status_param


class CreditLinesPagination(PageNumberPagination):
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
