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
    
    item_groups, display_groups = get_item_groups(main_group, filters.get('depth'))
    
    data = []
    return data

def get_item_groups(main_group, depth):
    #Get all group types to be displayed
    depth_sort = ["Product Category", "Product Subcategory", "Product Group", "Item Group"]
    display_types = []
    for g in depth_sort:
        display_types.append(g)
        if g == depth:
            break
    
    item_groups = [main_group]
    display_groups = [main_group]
    item_groups, display_groups = get_child_group(main_group, display_types, item_groups, display_groups)
    frappe.log_error(item_groups, "item_groups")
    frappe.log_error(display_groups, "display_groups")
    
    return item_groups, display_groups

# ~ def get_item_groups(language="de"):
    # ~ # grab root node
    # ~ root_node = frappe.db.sql("""SELECT `name` FROM `tabItem Group` 
        # ~ WHERE (`parent_item_group` IS NULL OR `parent_item_group` = "");""", 
        # ~ as_dict=True)[0]['name']
    # ~ if language == "de":
        # ~ return get_child_group(root_node)
    # ~ else:
        # ~ return get_translated_child_group(root_node, language, root_call=True)

def get_child_group(item_group, display_types, item_groups, display_groups):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for s in sub_groups:
        sg = {}
        sg[s['name']] = get_child_group(s['name'], display_types, item_groups, display_groups)
        groups.append(sg)
        item_groups.append(s['name'])
        if s['item_group_type'] in display_types:
            display_groups.append(s['name'])
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for n in nodes:
        item_groups.append(n['name'])
        if n['item_group_type'] in display_types:
            display_groups.append(n['name'])
    return item_groups, display_groups
    
# ~ def get_child_group(item_group):
    # ~ groups = []
    # ~ sub_groups = frappe.get_all("Item Group", 
        # ~ filters={'parent_item_group': item_group, 'is_group': 1, 'show_in_website': 1},
        # ~ order_by='weightage desc',
        # ~ fields=['name'])
    # ~ for s in sub_groups:
        # ~ sg = {}
        # ~ sg[s['name']] = get_child_group(s['name'])
        # ~ groups.append(sg)
    # ~ nodes = frappe.get_all("Item Group", 
        # ~ filters={'parent_item_group': item_group, 'is_group': 0, 'show_in_website': 1},
        # ~ order_by='weightage desc',
        # ~ fields=['name'])
    # ~ for n in nodes:
        # first item per group
        # ~ item = frappe.get_all("Item", filters={'item_group': n['name'], 'disabled': 0, 'show_in_website': 1}, 
            # ~ fields=['name'], 
            # ~ order_by='weightage desc',
            # ~ limit=1)
        # ~ record = {}
        # ~ if item and len(item) > 0:
            # ~ record[n['name']] = item[0]
        # ~ groups.append(n)
    # ~ return groups
