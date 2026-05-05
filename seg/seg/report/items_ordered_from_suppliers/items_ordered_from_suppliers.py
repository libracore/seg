# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data()
    return columns, data

def get_columns():
    columns = [
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 250},
        {"label": _("Ordered Qty"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 80, "precision": 1},
        {"label": _("Stock Qty"), "fieldname": "stock_qty", "fieldtype": "Float", "width": 80, "precision": 1},
        {"label": _("Expected Delivery Date"), "fieldname": "schedule_date", "fieldtype": "Date", "width": 100},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": _("Purchase Order"), "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 100},
        {"label": _("Reserved Qty"), "fieldname": "reserved_qty", "fieldtype": "Float",  "precision": 1, "width": 50}
    ]
    return columns

def get_data():
    main_warehouse = frappe.db.get_single_value("SEG Settings", "main_warehouse")
    data = frappe.db.sql("""
                            SELECT
                                `tabPurchase Order Item`.`item_code` AS `item_code`,
                                `tabPurchase Order Item`.`item_name` AS `item_name`,
                                (IFNULL(`tabPurchase Order Item`.`qty`, 0) - IFNULL(`tabPurchase Order Item`.`received_qty`, 0)) AS `ordered_qty`,
                                `tabBin`.`actual_qty` AS `stock_qty`,
                                `tabPurchase Order Item`.`schedule_date` AS `schedule_date`,
                                `tabPurchase Order`.`supplier` AS `supplier`,
                                `tabPurchase Order`.`name` AS `purchase_order`,
                                `tabBin`.`reserved_qty` AS `reserved_qty`
                            FROM
                                `tabPurchase Order Item`
                            LEFT JOIN
                                `tabBin` ON `tabPurchase Order Item`.`item_code` = `tabBin`.`item_code`
                            LEFT JOIN
                                `tabPurchase Order` ON `tabPurchase Order Item`.`parent` = `tabPurchase Order`.`name`
                            WHERE
                                `tabBin`.`ordered_qty` > 0
                            AND
                                `tabBin`.`warehouse` = %(warehouse)s
                            AND
                                `tabPurchase Order Item`.`docstatus` = 1
                            AND
                                `tabPurchase Order Item`.`received_qty` < `tabPurchase Order Item`.`qty`;""", {'warehouse': main_warehouse}, as_dict=True)
    return data
