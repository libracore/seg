# Copyright (c) 2022, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from erpnextswiss.erpnextswiss.utils import has_attachments
from erpnextswiss.erpnextswiss.attach_pdf import attach_pdf
""" 
This function will attach the print of all sales invoice and delivery notes
"""
def attach_prints():
    attach_print_for_doctype("Delivery Note", "Lieferschein")
    attach_print_for_doctype("Sales Invoice", "Monatsrechnung")
    return
    
def attach_print_for_doctype(doctype, print_format):
    docs = frappe.get_all(doctype, filters={'docstatus': 1}, fields=['name'])
    count = 0
    for d in docs:
        count += 1
        if not has_attachments(dn=d['name'], dt=doctype):
            attach_pdf(doctype=doctype, docname=d['name'], print_format=print_format, background=0, hashname=1, is_private=0)
            print("updated {0} ({1}%)".format(d['name'], int(100 * count / len(docs))))
        else:
            print("skipped {0} ({1}%)".format(d['name'], int(100 * count / len(docs))))
    print("done")
    return
