# Copyright (c) 2023, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint

@frappe.whitelist()
def set_mahnsperre(customer, mahnsperre):
    invoices = frappe.get_all("Sales Invoice", filters=[["customer", "=", customer], ["docstatus", "<", 2], ["outstanding_amount", ">", 0]])
    for invoice in invoices:
        doc = frappe.get_doc("Sales Invoice", invoice.name)
        if cint(mahnsperre) == 1:
            doc.mahnsperre = 1
            doc.exclude_from_payment_reminder_until = "2099-12-31"
        else:
            if doc.due_date:
                doc.mahnsperre = 0
                # Calculate the new date based on "due_date" + 20 days
                new_date = frappe.utils.add_days(doc.due_date, 20)
                doc.exclude_from_payment_reminder_until = new_date.strftime("%Y-%m-%d")
        doc.save()
