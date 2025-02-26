# Copyright (c) 2025, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

@frappe.whitelist()
def get_taxes_template(supplier):
    #Get Country of Supplier
    country = frappe.get_value("Supplier", supplier, "country")
    
    #get and return template
    template = None
    if country == "Schweiz":
        template = frappe.get_value("SEG Settings", "SEG Settings", "switzerland_purchase_taxes")
    else:
        template = frappe.get_value("SEG Settings", "SEG Settings", "foreign_purchase_taxes")
        
    return template
