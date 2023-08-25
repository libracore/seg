# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
from datetime import datetime, timedelta
import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 85},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data",  "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",  "width": 150},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "width": 80, "options": "UOM"},
        {"label": _("Stock in SKU"), "fieldname": "stock_in_sku", "fieldtype": "Float", "width": 80},   
        {"label": _("Ordered Qty"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 80},
        {"label": _("Lead Time in Days"), "fieldname": "lead_time_days", "fieldtype": "int", "width": 100},
        {"label": _("Avg Consumption"), "fieldname": "avg_consumption_per_day", "fieldtype": "Float", "width": 100},
        {"label": _("Stock End Date"), "fieldname": "days_until_stock_ends", "fieldtype": "Data", "width": 100},
    ]

def get_data(filters):
    # prepare filters
    if not 'item_group' in filters:
        filters['item_group'] = "%"
        
    # fetch data
    sql_query = """
        SELECT
            `tabItem`.`item_code` AS `item_code`,
            `tabItem`.`item_name` AS `item_name`,
            `tabItem`.`item_group` AS `item_group`,
            `tabItem`.`stock_uom` AS `stock_uom`,
            SUM(`tabBin`.`actual_qty`) AS `stock_in_sku`,
            SUM(`tabBin`.`ordered_qty`) AS `ordered_qty`,
            `tabItem`.`lead_time_days` AS `lead_time_days`,
            (SELECT SUM(`tabDelivery Note Item`.`qty`) / 90
             FROM `tabDelivery Note Item`
             LEFT JOIN `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
             WHERE `tabDelivery Note Item`.`item_code` = `tabItem`.`item_code`
                   AND `tabDelivery Note Item`.`docstatus` = 1
                   AND `tabDelivery Note`.`posting_date` BETWEEN DATE_SUB(CURDATE(), INTERVAL 90 DAY) AND CURDATE()
            ) AS `avg_consumption_per_day`,
            0 AS `days_until_stock_ends`
        FROM `tabItem`
        LEFT JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code`
        LEFT JOIN `tabUOM Conversion Detail` ON `tabUOM Conversion Detail`.`parent` = `tabItem`.`name`
        WHERE 
            `tabItem`.`item_group` LIKE "{item_group}"
            AND (`tabBin`.`actual_qty` > 0 OR `tabBin`.`ordered_qty` > 0)
            AND `tabItem`.`is_stock_item` = 1
            AND `tabItem`.`disabled` = 0
        GROUP BY `tabItem`.`item_code`
        ORDER BY `days_until_stock_ends` DESC
        """.format(item_group=filters['item_group'])
    data = frappe.db.sql(sql_query, as_dict=True)
    
    for row in data:
        if row['avg_consumption_per_day']:
            days_until_stock_ends = round((row['stock_in_sku'] + row['ordered_qty']) / row['avg_consumption_per_day'], 2)
            row['days_until_sock_ends'] = frappe.utils.data.add_to_date(date=frappe.utils.data.today(), days=days_until_stock_ends)
        else:
            row['days_until_stock_ends'] = ""
            
    return data

