import frappe
from frappe import _
from frappe.modules.utils import sync_customizations

def execute():
    sync_customizations("seg")

    
    update = frappe.db.sql("""
                                UPDATE
                                    `tabItem Group`
                                LEFT JOIN
                                    `tabItem Group Priority` ON `tabItem Group Priority`.`rule_type` = `tabItem Group`.`item_group_type`
                                SET
                                    `item_group_priority` = IFNULL(`tabItem Group Priority`.`rule_priority`, 0);""")
    
    frappe.db.commit()
    return
