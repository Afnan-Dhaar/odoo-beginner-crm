from datetime import date, timedelta

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestCustomer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer_model = cls.env["my.first.customer"]

    def test_customer_reference_and_profile_summary(self):
        customer = self.customer_model.create(
            {
                "name": "Test Customer",
                "email": "test@example.com",
                "category": "prospect",
            }
        )

        self.assertTrue(customer.reference.startswith("CUS"))
        self.assertEqual(customer.category, "prospect")
        self.assertEqual(customer.total_invoiced, 0)
        self.assertEqual(customer.total_paid, 0)
        self.assertEqual(customer.total_due, 0)

    def test_customer_timeline_combines_customer_events(self):
        customer = self.customer_model.create({"name": "Timeline Customer"})
        self.env["my.first.customer.note"].create(
            {
                "customer_id": customer.id,
                "title": "Welcome call",
                "note": "Initial conversation",
            }
        )
        self.env["my.first.customer.activity"].create(
            {
                "customer_id": customer.id,
                "title": "Schedule meeting",
            }
        )
        self.env["my.first.customer.invoice"].create(
            {
                "customer_id": customer.id,
                "amount_total": 100,
            }
        )

        customer.action_refresh_timeline()

        self.assertEqual(len(customer.timeline_ids), 3)
        self.assertSetEqual(
            set(customer.timeline_ids.mapped("event_type")),
            {"note", "activity", "invoice"},
        )

    def test_invalid_email_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.customer_model.create(
                {
                    "name": "Invalid Customer",
                    "email": "invalid-email",
                }
            )

    def test_active_customer_cannot_be_deleted(self):
        customer = self.customer_model.create({"name": "Active Customer"})
        customer.action_activate()

        with self.assertRaises(ValidationError):
            customer.unlink()


class TestCustomerActivity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["my.first.customer"].create(
            {"name": "Activity Customer"}
        )

    def test_activity_can_be_marked_done(self):
        activity = self.env["my.first.customer.activity"].create(
            {
                "customer_id": self.customer.id,
                "title": "Call customer",
                "due_date": date.today() + timedelta(days=1),
            }
        )

        activity.action_mark_done()

        self.assertEqual(activity.status, "done")
        self.assertTrue(activity.completed_at)
        self.assertEqual(activity.completed_by, self.env.user)

    def test_past_planned_activity_is_overdue(self):
        activity = self.env["my.first.customer.activity"].create(
            {
                "customer_id": self.customer.id,
                "title": "Past follow-up",
                "due_date": date.today() - timedelta(days=1),
            }
        )

        self.assertTrue(activity.is_overdue)
        self.assertIn(
            activity,
            self.env["my.first.customer.activity"].search([("is_overdue", "=", True)]),
        )


class TestCustomerInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["my.first.customer"].create({"name": "Invoice Customer"})
        cls.invoice_model = cls.env["my.first.customer.invoice"]
        cls.payment_model = cls.env["my.first.customer.payment"]

    def test_payment_updates_invoice_totals(self):
        invoice = self.invoice_model.create(
            {
                "customer_id": self.customer.id,
                "amount_total": 100,
            }
        )

        self.payment_model.create(
            {
                "invoice_id": invoice.id,
                "amount": 40,
            }
        )

        self.assertEqual(invoice.amount_paid, 40)
        self.assertEqual(invoice.amount_due, 60)
        self.assertEqual(invoice.payment_status, "partially_paid")

    def test_payment_cannot_exceed_invoice_total(self):
        invoice = self.invoice_model.create(
            {
                "customer_id": self.customer.id,
                "amount_total": 100,
            }
        )

        with self.assertRaises(ValidationError):
            self.payment_model.create(
                {
                    "invoice_id": invoice.id,
                    "amount": 101,
                }
            )

    def test_due_date_cannot_precede_invoice_date(self):
        with self.assertRaises(ValidationError):
            self.invoice_model.create(
                {
                    "customer_id": self.customer.id,
                    "amount_total": 100,
                    "invoice_date": date.today(),
                    "due_date": date.today() - timedelta(days=1),
                }
            )

    def test_posted_invoice_cannot_be_edited(self):
        invoice = self.invoice_model.create(
            {
                "customer_id": self.customer.id,
                "amount_total": 100,
            }
        )
        invoice.action_post()

        with self.assertRaises(ValidationError):
            invoice.write({"amount_total": 120})

    def test_cancelled_invoice_cannot_receive_payment(self):
        invoice = self.invoice_model.create(
            {
                "customer_id": self.customer.id,
                "amount_total": 100,
            }
        )
        invoice.action_cancel()

        with self.assertRaises(ValidationError):
            self.payment_model.create(
                {
                    "invoice_id": invoice.id,
                    "amount": 25,
                }
            )

    def test_posted_invoice_can_be_cancelled(self):
        invoice = self.invoice_model.create(
            {
                "customer_id": self.customer.id,
                "amount_total": 100,
            }
        )
        invoice.action_post()
        invoice.action_cancel()

        self.assertEqual(invoice.state, "cancelled")


class TestCrmSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_group = cls.env.ref("my_first_module.group_my_first_crm_user")
        cls.manager_group = cls.env.ref("my_first_module.group_my_first_crm_manager")
        cls.crm_user = cls.env["res.users"].create(
            {
                "name": "CRM User Test",
                "login": "crm_user_test",
                "email": "crm_user_test@example.com",
                "group_ids": [(6, 0, [cls.user_group.id])],
            }
        )
        cls.crm_manager = cls.env["res.users"].create(
            {
                "name": "CRM Manager Test",
                "login": "crm_manager_test",
                "email": "crm_manager_test@example.com",
                "group_ids": [(6, 0, [cls.manager_group.id])],
            }
        )

    def test_regular_user_sees_only_owned_activities(self):
        customer = self.env["my.first.customer"].create({"name": "Security Customer"})
        activity = self.env["my.first.customer.activity"].create(
            {
                "customer_id": customer.id,
                "title": "Manager activity",
                "assigned_to": self.crm_manager.id,
            }
        )

        user_activities = self.env["my.first.customer.activity"].with_user(
            self.crm_user
        )
        manager_activities = self.env["my.first.customer.activity"].with_user(
            self.crm_manager
        )

        self.assertNotIn(activity, user_activities.search([]))
        self.assertIn(activity, manager_activities.search([]))

    def test_regular_user_cannot_edit_invoices(self):
        customer = self.env["my.first.customer"].create(
            {"name": "Invoice Security Customer"}
        )
        invoice = self.env["my.first.customer.invoice"].create(
            {
                "customer_id": customer.id,
                "amount_total": 100,
            }
        )

        with self.assertRaises(AccessError):
            self.env["my.first.customer.invoice"].with_user(self.crm_user).browse(
                invoice.id
            ).write({"notes": "Not allowed"})
