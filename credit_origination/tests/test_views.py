from accounts.tests.base_test import BaseTest
from credit_origination.models import CreditType, CreditRequest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from decimal import Decimal
from datetime import timedelta
from django.utils.timezone import now


class CreditTypeViewsTests(BaseTest):

    def setUp(self):
        self.client = APIClient()
        self.create_url = reverse("credit_origination_api:credit_type_create")
        self.update_url = lambda pk: reverse(
            "credit_origination_api:credit_type_update", args=[pk]
        )
        self.list_url = reverse("credit_origination_api:credit_type_list")
        self.admin_list_url = reverse("credit_origination_api:admin_credit_type_list")
        self.delete_url = lambda pk: reverse(
            "credit_origination_api:credit_type_delete", args=[pk]
        )

    def test_create_credit_type_as_admin(self):
        self.client.force_authenticate(user=self.superuser)
        new_credit_type_data = {
            "name": "Business Loan",
            "description": "A loan for business expenses",
            "active": False,
        }
        response = self.client.post(
            self.create_url, new_credit_type_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditType.objects.count(), 2)
        self.assertEqual(
            CreditType.objects.get(name="Business Loan").description,
            "A loan for business expenses",
        )

    def test_create_credit_type_as_non_admin(self):
        self.client.force_authenticate(user=self.user)
        new_credit_type_data = {
            "name": "Business Loan",
            "description": "A loan for business expenses",
            "active": False,
        }
        response = self.client.post(
            self.create_url, new_credit_type_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_credit_type_as_admin(self):
        self.client.force_authenticate(user=self.superuser)
        updated_data = {
            "name": "Updated Loan",
            "description": "Updated description",
            "active": False,
        }
        response = self.client.put(
            self.update_url(self.credit_type.pk), updated_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.credit_type.refresh_from_db()
        self.assertEqual(self.credit_type.name, "Updated Loan")
        self.assertEqual(self.credit_type.description, "Updated description")
        self.assertFalse(self.credit_type.active)

    def test_update_credit_type_as_non_admin(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {
            "name": "Updated Loan",
            "description": "Updated description",
            "active": False,
        }
        response = self.client.put(
            self.update_url(self.credit_type.pk), updated_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_credit_types(self):
        url = self.list_url
        for n in range(15):
            CreditType.objects.create(
                name=f"Type {n}", description="Sample description"
            )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 16)

    def test_list_credit_types_admin(self):
        self.client.force_authenticate(user=self.superuser)
        url = self.admin_list_url
        for n in range(15):
            CreditType.objects.create(
                name=f"Type {n}", description="Sample description", active=True
            )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 16)

    def test_list_credit_types_pagination(self):
        url = self.list_url
        for n in range(25):
            CreditType.objects.create(
                name=f"Type {n}", description="Sample description"
            )
        response = self.client.get(url, {"page": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_credit_types_pagination_page_size(self):
        url = self.list_url
        for n in range(25):
            CreditType.objects.create(
                name=f"Type {n}", description="Sample description"
            )
        response = self.client.get(url, {"page_size": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertEqual(len(response.data["results"]), 5)

    def test_create_credit_type_invalid_data(self):
        self.client.force_authenticate(user=self.superuser)
        url = self.create_url
        invalid_data = {
            "name": "",
            "description": "",
        }
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIsNotNone(response.data)
        self.assertIn("name", response.data)

    def test_update_credit_type_invalid_data(self):
        self.client.force_authenticate(user=self.superuser)
        url = self.update_url(self.credit_type.pk)
        invalid_data = {
            "name": "",
            "description": "",
        }
        response = self.client.put(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIsNotNone(response.data)
        self.assertIn("name", response.data)

    def test_get_all_credit_types(self):
        CreditType.objects.create(name="Personal Loan", description="For personal use")
        url = self.list_url
        response = self.client.get(url, format="json")
        credit_type = CreditType.objects.first()
        expected_data = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": credit_type.id,
                    "name": "Personal Loan",
                    "description": "For personal use",
                    "created": credit_type.created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
            ],
        }
        self.assertEqual(response.data["count"], expected_data["count"])
        result = response.data["results"][0]
        expected_result = expected_data["results"][0]
        self.assertEqual(result["id"], expected_result["id"])
        self.assertEqual(result["name"], expected_result["name"])
        self.assertEqual(result["description"], expected_result["description"])
        self.assertTrue("created" in result)

    def test_get_all_credit_types_admin(self):
        CreditType.objects.create(name="Personal Loan", description="For personal use")
        self.client.force_authenticate(user=self.superuser)
        url = self.admin_list_url
        response = self.client.get(url, format="json")
        credit_type = CreditType.objects.first()
        expected_data = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": credit_type.id,
                    "name": "Personal Loan",
                    "description": "For personal use",
                    "created": credit_type.created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "active": True,
                }
            ],
        }
        self.assertEqual(response.data["count"], expected_data["count"])
        result = response.data["results"][0]
        expected_result = expected_data["results"][0]
        self.assertEqual(result["id"], expected_result["id"])
        self.assertEqual(result["name"], expected_result["name"])
        self.assertEqual(result["description"], expected_result["description"])
        self.assertTrue("created" in result)
        self.assertTrue("active" in result)

    def test_credit_type_admin_list_pagination_invalid(self):
        self.client.force_authenticate(user=self.user)
        url = self.admin_list_url
        for n in range(2):
            CreditType.objects.create(
                name=f"Type {n}", description="Sample description", active=True
            )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_credit_type_description_active(self):
        credit_type_w_des = CreditType.objects.create(
            name="Personal Loan", description="For personal use"
        )
        self.client.force_authenticate(user=self.superuser)
        url = self.update_url(credit_type_w_des.pk)
        data = {
            "description": "Updated description",
            "active": True,
        }
        response = self.client.put(url, data, format="json")
        if response.status_code != status.HTTP_200_OK:
            print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        credit_type_w_des.refresh_from_db()
        self.assertEqual(credit_type_w_des.description, "Updated description")
        self.assertTrue(credit_type_w_des.active)

    def test_update_credit_type_unauthorized(self):
        credit_type_w_des = CreditType.objects.create(
            name="Personal Loan", description="For personal use"
        )
        self.client.force_authenticate(user=self.user)
        url = self.update_url(credit_type_w_des.pk)
        data = {"description": "Unauthorized update"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_credit_type_as_admin(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(
            self.delete_url(self.credit_type.pk), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CreditType.objects.count(), 0)

    def test_delete_credit_type_as_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            self.delete_url(self.credit_type.pk), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(CreditType.objects.count(), 1)

    def test_delete_credit_type_not_found(self):
        self.client.force_authenticate(user=self.superuser)
        invalid_pk = 999
        response = self.client.delete(self.delete_url(invalid_pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestCreateUserCreditRequestView(BaseTest, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("credit_origination_api:create_user_credit_request")
        self.data = {
            "credit_type": self.credit_type.id,
            "amount": Decimal("5000.00"),
            "term": 24,
        }

    def test_create_credit_request(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], str(self.data["amount"]))
        self.assertEqual(response.data["term"], self.data["term"])
        self.assertEqual(response.data["status"], "pending")

    def test_create_credit_request_invalid_amount(self):
        self.data["amount"] = Decimal("-5000.00")
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_create_credit_request_invalid_term(self):
        self.data["term"] = 150
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("term", response.data)


class TestUpdateUserCreditRequestView(BaseTest, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
            status="pending",
        )
        self.url = reverse(
            "credit_origination_api:update_user_credit_request",
            kwargs={"pk": self.credit_request.pk},
        )
        self.update_data = {
            "amount": Decimal("6000.00"),
            "term": 36,
        }

    def test_update_credit_request_within_48_hours(self):
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], str(self.update_data["amount"]))
        self.assertEqual(response.data["term"], self.update_data["term"])

    def test_update_credit_request_after_48_hours(self):
        self.credit_request.created = now() - timedelta(hours=49)
        self.credit_request.save()
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_credit_request_status_not_pending(self):
        self.credit_request.status = "approved"
        self.credit_request.save()
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class TestCreditRequestsAdminListView(BaseTest, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.superuser)
        self.url = reverse("credit_origination_api:credit_requests_admin_list")
        self.credit_request1 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
            status="pending",
        )
        self.credit_request2 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("6000.00"),
            term=36,
            user=self.user,
            status="approved",
        )

    def test_get_all_credit_requests(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_credit_requests_filtered_by_status(self):
        response = self.client.get(self.url, {"status": "approved"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "approved")

    def test_get_credit_requests_filtered_by_username(self):
        response = self.client.get(self.url, {"username": self.user.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        for result in response.data["results"]:
            self.assertEqual(result["user"], self.user.pk)

    def test_pagination_of_credit_requests(self):
        for i in range(15):
            CreditRequest.objects.create(
                credit_type=self.credit_type,
                amount=Decimal("7000.00"),
                term=12,
                user=self.user,
                status="pending",
            )
        response = self.client.get(self.url, {"page_size": 10, "page": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 7)


class TestListCreditRequestsView(BaseTest, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("credit_origination_api:list_credit_requests")
        self.credit_request1 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
            status="pending",
        )
        self.credit_request2 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("6000.00"),
            term=36,
            user=self.user,
            status="approved",
        )

    def test_get_user_credit_requests(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for result in response.data:
            self.assertEqual(result["user"], self.user.pk)


class TestCreditRequestStatusUpdateView(BaseTest, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.superuser)
        self.credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
            status="pending",
        )
        self.url = reverse(
            "credit_origination_api:credit_request_status_update",
            kwargs={"pk": self.credit_request.pk},
        )
        self.update_data = {
            "status": "approved",
        }

    def test_update_credit_request_status(self):
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], self.update_data["status"])

    def test_update_credit_request_status_invalid_status(self):
        self.update_data["status"] = "invalid_status"
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_credit_request_status_update_success_by_superuser(self):
        response = self.client.put(self.url, {"status": "approved"}, format="json")
        self.credit_request.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.credit_request.status, "approved")

    def test_credit_request_status_update_forbidden_for_staff(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(self.url, {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_credit_request_status_update_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url, {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
