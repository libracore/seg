# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
from datetime import datetime, timedelta
import frappe
from frappe.utils import date_diff
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 85},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data",  "width": 180},
        {"label": _("Default Supplier"), "fieldname": "default_supplier", "fieldtype": "Link", "options": "Supplier",  "width": 120},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "width": 80, "options": "UOM"},
        {"label": _("Stock in SKU"), "fieldname": "stock_in_sku", "fieldtype": "Float", "width": 80},   
        {"label": _("Ordered Qty"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 80},
        {"label": _("Lead Time in Days"), "fieldname": "lead_time_days", "fieldtype": "int", "width": 100},
        {"label": _("Avg Consumption"), "fieldname": "avg_consumption_per_day", "fieldtype": "Float", "width": 100},
        {"label": _("Stock End Date"), "fieldname": "days_until_stock_ends", "fieldtype": "Data", "width": 100},
        {"label": _("To Order"), "fieldname": "to_order", "fieldtype": "Check", "width": 50}
    ]

def get_data(filters):
    # fetch data
    sql_query = """
        SELECT
            `tabItem`.`item_code` AS `item_code`,
            `tabItem`.`item_name` AS `item_name`,
            `tabItem`.`default_supplier` AS `default_supplier`,
            `tabItem`.`stock_uom` AS `stock_uom`,
            `tabItem`.`modified` AS `modified`,
            SUM(`tabBin`.`actual_qty`) AS `stock_in_sku`,
            SUM(`tabBin`.`ordered_qty`) AS `ordered_qty`,
            `tabItem`.`lead_time_days` AS `lead_time_days`,
            (SELECT SUM(`tabDelivery Note Item`.`qty`)
             FROM `tabDelivery Note Item`
             LEFT JOIN `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
             WHERE `tabDelivery Note Item`.`item_code` = `tabItem`.`item_code`
                   AND `tabDelivery Note Item`.`docstatus` = 1
                   AND `tabDelivery Note`.`posting_date` BETWEEN DATE_SUB(CURDATE(), INTERVAL 360 DAY) AND CURDATE()
            ) AS `dn_consumption`,
            (SELECT SUM(`tabStock Entry Detail`.`qty`)
             FROM `tabStock Entry Detail`
             LEFT JOIN `tabStock Entry` ON `tabStock Entry`.`name` = `tabStock Entry Detail`.`parent`
             WHERE `tabStock Entry Detail`.`item_code` = `tabItem`.`item_code`
                   AND `tabStock Entry Detail`.`docstatus` = 1
                   AND `tabStock Entry`.`stock_entry_type` = 'Material Issue'
                   AND `tabStock Entry`.`posting_date` BETWEEN DATE_SUB(CURDATE(), INTERVAL 360 DAY) AND CURDATE()
            ) AS `se_consumption`,
            0 AS `avg_consumption_per_day`,
            0 AS `days_until_stock_ends`,
            `tabItem`.`creation` AS `date_created`
        FROM `tabItem`
        LEFT JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code`
        LEFT JOIN `tabUOM Conversion Detail` ON `tabUOM Conversion Detail`.`parent` = `tabItem`.`name`
        WHERE 
            `tabItem`.`is_purchase_item` = 1
            AND `tabItem`.`is_stock_item` = 1
            AND `tabItem`.`disabled` = 0
            AND `tabItem`.`has_variants` = 0
        GROUP BY `tabItem`.`item_code`
        ORDER BY `modified` DESC
        """
    data = frappe.db.sql(sql_query, as_dict=True)
    
    #prepare and calculate data for report
    today_str = frappe.utils.data.today()
    today = frappe.utils.get_datetime(today_str)
    one_year_ago = frappe.utils.add_days(today, -360)
    for row in data:
        #Avoid Nonetypes and calculate average consumption
        if not row['dn_consumption']:
            row['dn_consumption'] = 0
        if not row['se_consumption']:
            row['se_consumption'] = 0
        if not row['stock_in_sku']:
            row['stock_in_sku'] = 0
        if not row['ordered_qty']:
            row['ordered_qty'] = 0
        if row['date_created'] < one_year_ago:
            avg_consumption = (row['dn_consumption'] + row['se_consumption']) / 360
        else:
            item_age = date_diff(today, row['date_created'])
            if not item_age:
                item_age = 1
            avg_consumption = (row['dn_consumption'] + row['se_consumption']) / item_age
        row['avg_consumption_per_day'] = avg_consumption
        
        #Calculate End of Stock Date and give Color (Red if Stock is out, orange if Stock runs out within Leadtime, else green)
        if row['avg_consumption_per_day']:
            days_until_stock_ends = round((row['stock_in_sku'] + row['ordered_qty']) / avg_consumption, 2)
            if days_until_stock_ends < 1:
                color = "red"
                row['to_order'] = 1
            elif days_until_stock_ends <= row['lead_time_days']:
                color = "orange"
                row['to_order'] = 1
            else:
                color = "green"
                row['to_order'] = 0
            row['days_until_stock_ends'] = "<span style='color: {0};'>{1}</span>".format(color, frappe.utils.data.add_to_date(date=today_str, days=days_until_stock_ends, as_string=True))
        else:
            row['days_until_stock_ends'] = ""
    
    return data

