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
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": _("Net Turnover"), "fieldname": "net_turnover", "fieldtype": "Currency", "width": 100},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "float", "options": "Customer", "width": 80},
        {"label": _("Total Purchase Price"), "fieldname": "total_purchase", "fieldtype": "Currency", "width": 100},
        {"label": _("Total SEG Purchase Price"), "fieldname": "total_seg_purchase", "fieldtype": "Currency", "width": 100},
        {"label": _("DB on Purchase Price"), "fieldname": "db_purchase_price", "fieldtype": "Currency", "width": 100},
        {"label": _("DB on SEG Purchase Price"), "fieldname": "db_seg_price", "fieldtype": "Currency", "width": 100}
    ]
    return columns

def get_data(filters):
    #Prepare Employee condition
    if filters.get('employee'):
        user = frappe.get_value("Sales Overview Employee", filters.get('employee'), "user")
        if user:
            employee_condition = """AND `tabDelivery Note`.`owner` = {0}""".format(user)
        else:
            frappe.msgprint("Fehler beim abrufen des Mitarbeiters")
    else:
        employee_condition = """"""
    
    #Get Item Groups
    if filters.get('item_group'):
        main_group = filters.get('item_group')
    else:
        main_group = "Alle Artikelgruppen"
    
    item_groups, display_groups = get_item_groups(main_group, depth)
    
    data = []
    return data
