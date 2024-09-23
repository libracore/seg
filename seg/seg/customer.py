# Copyright (c) 2024, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

@frappe.whitelist()
def set_allow_invoice(customer, allow_invoice):
    customer = frappe.get_doc("Customer", customer)
    customer.allow_invoice = allow_invoice
    customer.save()
    return