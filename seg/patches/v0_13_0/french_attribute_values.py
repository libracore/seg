import frappe
from frappe import _
from frappe.modules.utils import sync_customizations
from seg.seg.utils import set_french_attributes

def execute():
    sync_customizations("seg")

    
    items = frappe.db.sql("""
                                SELECT
                                    `name`
                                FROM
                                    `tabItem`;""", as_dict=True)
    
    for item in items:
        set_french_attributes(item.get('name'), "button")
    
    frappe.db.commit()
    return
