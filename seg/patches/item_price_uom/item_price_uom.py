import frappe

def execute():
    item_prices = frappe.db.sql("""
                                    SELECT
                                        `name`,
                                        `item_code`
                                    FROM
                                        `tabItem Price`
                                    WHERE
                                        `uom` IS NULL""", as_dict=True)
    
    for item_price in item_prices:
        default_uom = frappe.get_value("Item", item_price.get('item_code'), "stock_uom")
        set_value = frappe.db.set_value("Item Price", item_price.get('name'), "uom", default_uom)
    
    frappe.db.commit()
