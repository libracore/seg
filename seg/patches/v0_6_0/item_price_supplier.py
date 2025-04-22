import frappe
from frappe import _

def execute():
    frappe.reload_doc("Stock", "doctype", "Item Price")
    
    item_prices = frappe.db.sql("""
                                SELECT
                                    `name`
                                FROM
                                    `tabItem Price`""", as_dict=True)
    
    for item_price in item_prices:
        item_price_doc = frappe.get_doc("Item Price", item_price.get('name'))
        try:
            item_price_doc.save()
        except Exception as e:
            frappe.log_error("Item Price: {0} - Error: {1}".format(item_price.get('name'), e), "Fehler beim aktualisieren des Item Price")
    return
