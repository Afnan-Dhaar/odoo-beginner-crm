from datetime import date, timedelta

from odoo.exceptions import ValidationError
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
