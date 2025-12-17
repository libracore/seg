import frappe
from frappe import _
from frappe.modules.utils import sync_customizations
from seg.seg.utils import set_seg_price
from erpnext.stock.utils import get_stock_balance
from frappe.utils import nowdate

def execute():
    sync_customizations("seg")
    
    item_prices = frappe.db.sql("""
                                SELECT
                                    `tabItem Price`.`name` AS `name`
                                FROM
                                    `tabItem Price`
                                LEFT JOIN
                                    `tabItem` ON `tabItem`.`name` = `tabItem Price`.`item_code`
                                WHERE
                                    `tabItem`.`disabled` = 0;""", as_dict=True)
    
    for item_price in item_prices:
        item_price_doc = frappe.get_doc("Item Price", item_price.get('name'))
        item_price_doc.save()
    
    items = frappe.db.sql("""
                                SELECT
                                    `name`
                                FROM
                                    `tabItem`;""", as_dict=True)
    
    for item in items:
        qty, valuation_rate = get_stock_balance(item_code=item.get('name'), warehouse="Lagerräume - SEG", posting_date=nowdate(), with_valuation_rate=True)
        frappe.db.set_value("Item", item.get('name'), "seg_purchase_price", valuation_rate)
        frappe.db.set_value("Item", item.get('name'), "considered_qty", qty)
    frappe.db.commit()
    return
