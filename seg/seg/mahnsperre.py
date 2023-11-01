# Copyright (c) 2023, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint

@frappe.whitelist()
def set_mahnsperre(mahnsperre, customer):
    invoices = frappe.get_all("Sales Invoice", filters={"customer": customer, "docstatus": ["!=", 2], "status": ["!=", "Paid"]})
    for invoice in invoices:
        doc = frappe.get_doc("Sales Invoice", invoice.name)
        if doc.status != "Credit Note Issued" and doc.status != "Return":
            if cint(mahnsperre) == 1:
                doc.mahnsperre = 1
                doc.exclude_from_payment_reminder_until = "2099-12-31"
                doc.save()
            else:
                if doc.due_date:
                    doc.mahnsperre = 0
                    # Calculate the new date based on "due_date" + 20 days
                    new_date = frappe.utils.add_days(doc.due_date, 20)
                    doc.exclude_from_payment_reminder_until = new_date.strftime("%Y-%m-%d")
                    doc.save()
