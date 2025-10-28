import frappe
from frappe import _
from frappe.modules.utils import sync_customizations

def execute():
    sync_customizations("seg")

    
    pricing_rule_item_codes = frappe.db.sql("""
                                SELECT
                                    `tabPricing Rule Item Code`.`name` AS `name`,
                                    `tabPricing Rule Item Code`.`item_code` AS `item_code`
                                FROM
                                    `tabPricing Rule Item Code`
                                WHERE
                                    `item_code` IS NOT NULL;""", as_dict=True)
    
    for item in pricing_rule_item_codes:
        item_doc = frappe.get_doc("Item", item.get('item_code'))
        frappe.db.set_value("Pricing Rule Item Code", item.get('name'), "item_name", item_doc.get('item_name'))
        frappe.db.set_value("Pricing Rule Item Code", item.get('name'), "default_supplier", item_doc.get('default_supplier'))
    
    frappe.db.commit()
    return
