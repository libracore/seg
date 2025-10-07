import frappe
from frappe import _
from frappe.modules.utils import sync_customizations

def execute():
    sync_customizations("seg")

    
    update = frappe.db.sql("""
                                UPDATE
                                    `tabPurchase Receipt`
                                SET
                                    `exclude_from_seg_price` = 1""")
    
    frappe.db.commit()
    return
