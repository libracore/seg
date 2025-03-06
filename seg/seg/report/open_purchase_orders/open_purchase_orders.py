# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Purchase Order"), "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 120},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": _("Reqd By Date"), "fieldname": "schedule_date", "fieldtype": "Date", "width": 100}
    ]
    return columns

def get_data(filters):
    condition = ""
    if filters.only_overdue:
        condition = """AND `schedule_date` < CURDATE()"""
    
    data = frappe.db.sql("""
                            SELECT
                                `name` AS `purchase_order`,
                                `supplier`,
                                `schedule_date`
                            FROM
                                `tabPurchase Order`
                            WHERE
                                `docstatus` = 1
                            AND
                                `status` IN ("To Receive", "To Receive and Bill")
                                {condition}
                            ORDER BY `schedule_date` DESC;""".format(condition=condition), as_dict=True)
    
    return data
