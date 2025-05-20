# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 300},
        # ~ {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 80},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": _("Default Supplier"), "fieldname": "default_supplier", "fieldtype": "Link", "options": "Supplier", "width": 120}
    ]
    return columns

def get_data(filters):
    #get all Delivery Note Item Entries within given Dates
    entries = get_dn_positions(from_date=filters.from_date, to_date=filters.to_date)
    
    return entries

def get_dn_positions(from_date=None, to_date=None):
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = "2099-12-31"
    
    positions = frappe.db.sql("""SELECT
                                    `tabDelivery Note Item`.`item_code` AS `item`,
                                    SUM(`tabDelivery Note Item`.`qty`) AS `total_qty`,
                                    SUM(`tabDelivery Note Item`.`amount`) AS `total_amount`,
                                    `tabItem`.`item_name` AS `item_name`,
                                    `tabItem`.`item_group` AS `item_group`,
                                    `tabItem`.`default_supplier` AS `default_supplier`
                                FROM
                                    `tabDelivery Note Item`
                                LEFT JOIN
                                    `tabItem` ON `tabItem`.`name` = `tabDelivery Note Item`.`item_code`
                                WHERE
                                    `tabDelivery Note Item`.`docstatus` = 1
                                GROUP BY
                                    `tabDelivery Note Item`.`item_code`""", as_dict=True)
                                
    return positions
