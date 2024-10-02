# Copyright (c) 2024, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

@frappe.whitelist()
def set_allow_invoice(doc, method):
    if doc.owner != "Guest":
        doc.allow_invoice = 1
    return