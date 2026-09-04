# Copyright (c) 2026, libracore AG
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.modules.utils import sync_customizations

def execute():
    sync_customizations("seg")
    
    pricing_rules = frappe.db.sql("""
                                    SELECT
                                        `name`,
                                        `customer`
                                    FROM
                                        `tabPricing Rule`
                                    WHERE
                                        `applicable_for` = 'Customer';""", as_dict=True)
    
    for pricing_rule in pricing_rules:
        customer_name = frappe.get_value("Customer", pricing_rule.get('customer'), "customer_name")
        update = frappe.db.set_value("Pricing Rule", pricing_rule.get('name'), "customer_name", customer_name)
