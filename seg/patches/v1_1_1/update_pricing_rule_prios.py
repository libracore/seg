# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.modules.utils import sync_customizations
from frappe. utils import cint

def execute():
    sync_customizations("seg")
    
    pricing_rules = frappe.db.sql("""
                                SELECT
                                    `name`
                                FROM
                                    `tabPricing Rule`
                                WHERE
                                    `apply_on` = 'Item Group';""", as_dict=True)
    
    for pricing_rule in pricing_rules:
        pricing_rule_doc = frappe.get_doc("Pricing Rule", pricing_rule.get('name'))
        
        if len(pricing_rule_doc.get('item_groups')) > 0:
            prio = frappe.get_value("Item Group", pricing_rule_doc.get('item_groups')[0].item_group, "item_group_priority")
            if cint(prio) != cint(pricing_rule_doc.get('priority')):
                frappe.db.set_value("Pricing Rule", pricing_rule.get('name'), "priority", prio)
    
