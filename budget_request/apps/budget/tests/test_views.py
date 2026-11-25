import json

from django.test import Client, TestCase

from apps.admin_panel.tests.factories import make_user
from apps.admin_panel.tests.test_views import INERTIA_HEADERS, InertiaClientMixin
from apps.budget.models import BudgetRequest
from apps.budget.services import requests as request_services
from apps.budget.dto.requests import RequestFormInputDTO
from apps.users.models import User


def create_request(actor, title="Laptops"):
    result = request_services.create_request(
        actor=actor,
        data=RequestFormInputDTO(
            title=title,
            amount="25.00",
            justification="Needed for the project.",
        ),
    )
    return result.request_id


class BudgetAccessTests(InertiaClientMixin, TestCase):
    def setUp(self):
        self.client_user = make_user("client", role=User.Roles.CLIENT)
        self.manager = make_user("manager", role=User.Roles.MANAGER)
        self.admin = make_user("admin", role=User.Roles.ADMIN)

    def test_anonymous_users_are_sent_to_login(self):
        response = self.client.get("/requests/")
        self.assertRedirects(
            response, "/?next=/requests/", fetch_redirect_response=False
        )

    def test_cross_role_pages_are_forbidden(self):
        cases = [
            (self.client_user, "/reviews/"),
            (self.client_user, "/budget/"),
            (self.manager, "/requests/"),
            (self.manager, "/budget/"),
            (self.admin, "/requests/"),
            (self.admin, "/requests/new/"),
        ]
        for user, url in cases:
            with self.subTest(user=user.username, url=url):
                client = Client()
                client.force_login(user)
                response = client.get(url, **INERTIA_HEADERS)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["component"], "Errors/Forbidden")

    def test_client_can_open_their_list(self):
        self.client.force_login(self.client_user)
        page = self.page(self.client.get("/requests/", **INERTIA_HEADERS))
        self.assertEqual(page["component"], "Budget/MyRequests")
        routes = [item["route"] for item in page["props"]["admin_nav"]]
        self.assertEqual(routes, ["budget_requests", "budget_request_create"])
        self.assertEqual(page["props"]["home"]["route"], "budget_requests")
        self.assertNotIn("activity", page["props"])


class BudgetViewTests(TestCase):
    def setUp(self):
        self.client_user = make_user("client", role=User.Roles.CLIENT)
        self.manager = make_user("manager", role=User.Roles.MANAGER)
        self.admin = make_user("admin", role=User.Roles.ADMIN)
        self.request_id = create_request(self.client_user)

    def post_json(self, client, url, data):
        return client.post(
            url, json.dumps(data), content_type="application/json", **INERTIA_HEADERS
        )

    def test_create_validation_error_rerenders_the_form(self):
        self.client.force_login(self.client_user)
        response = self.post_json(
            self.client,
            "/requests/new/",
            {"title": "", "amount": "10", "justification": ""},
        )
        self.assertEqual(response.status_code, 200)
        page = response.json()
        self.assertEqual(page["component"], "Budget/Form")
        self.assertIn("title", page["props"]["errors"])
        self.assertIn("justification", page["props"]["errors"])

    def test_reject_without_a_note_stays_pending(self):
        self.client.force_login(self.manager)
        response = self.post_json(
            self.client,
            f"/reviews/{self.request_id}/decide/",
            {"status": "rejected", "reviewer_feedback": ""},
        )
        self.assertRedirects(response, "/reviews/", fetch_redirect_response=False)
        stored = BudgetRequest.objects.get(pk=self.request_id)
        self.assertEqual(stored.status, BudgetRequest.Status.PENDING)

        follow = self.client.get("/reviews/", **INERTIA_HEADERS)
        self.assertEqual(follow.json()["props"]["flash"][0]["level"], "error")

    def test_manager_delete_is_forbidden(self):
        self.client.force_login(self.manager)
        response = self.client.post(f"/budget/{self.request_id}/delete/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(BudgetRequest.objects.filter(pk=self.request_id).exists())

    def test_admin_summary_includes_activity_and_reviews_do_not(self):
        self.client.force_login(self.admin)
        page = self.client.get("/budget/", **INERTIA_HEADERS).json()
        self.assertEqual(page["component"], "Budget/Admin")
        self.assertEqual(page["props"]["activity"][0]["action"], "created")
        self.assertEqual(page["props"]["activity"][0]["title"], "Laptops")

        self.client.force_login(self.manager)
        reviews = self.client.get("/reviews/", **INERTIA_HEADERS).json()
        self.assertNotIn("activity", reviews["props"])

    def test_admin_can_delete(self):
        self.client.force_login(self.admin)
        response = self.client.post(f"/budget/{self.request_id}/delete/")
        self.assertRedirects(response, "/budget/", fetch_redirect_response=False)
        self.assertFalse(BudgetRequest.objects.filter(pk=self.request_id).exists())
