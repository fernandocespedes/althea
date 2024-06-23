"""
URL configuration for althea project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Althea API",
        default_version="v1",
        description="""credit core / calculator for simple loans,
                    using Python, NumPy, NumPy Financial, Pandas,
                    Django, and Django Rest Framework""",
        terms_of_service="https://www.google.com/policies/terms/",  # change later
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,
    ),  # IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/users/", include("accounts.api.routers", namespace="accounts_api")),
    path(
        "api/credit-origination/",
        include("credit_origination.api.routers", namespace="credit_origination_api"),
    ),
    path(
        "api/credit-lines/",
        include("credit_line.api.routers", namespace="credit_line_api"),
    ),
    path(
        "api/credit-sublines/",
        include("credit_subline.api.routers", namespace="credit_subline_api"),
    ),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
