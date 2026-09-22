from odoo import fields, models


class CustomerNote(models.Model):
    _name = "my.first.customer.note"
    _description = "Customer Note"

    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(
        string="Title",
        required=True,
    )

    note = fields.Text(
        string="Note",
        required=True,
    )

    note_type = fields.Selection(
        [
            ("general", "General"),
            ("call", "Call"),
            ("email", "Email"),
            ("meeting", "Meeting"),
            ("follow_up", "Follow-up"),
        ],
        string="Note Type",
        default="general",
        required=True,
    )

    status = fields.Selection(
        [
            ("open", "Open"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="open",
        required=True,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        required=True,
    )

    follow_up_date = fields.Date(
        string="Follow-up Date",
    )

    contacted = fields.Boolean(
        string="Contacted",
        default=False,
    )

    created_at = fields.Datetime(
        string="Created At",
        readonly=True,
        default=fields.Datetime.now,
    )

    updated_at = fields.Datetime(
        string="Updated At",
        readonly=True,
    )

    created_by = fields.Many2one(
        "res.users",
        string="Created By",
        readonly=True,
        default=lambda self: self.env.user,
    )

    def write(self, vals):
        vals["updated_at"] = fields.Datetime.now()
        return super().write(vals)

    def action_mark_done(self):
        for note in self:
            note.status = "done"

    def action_mark_contacted(self):
        for note in self:
            note.contacted = True
