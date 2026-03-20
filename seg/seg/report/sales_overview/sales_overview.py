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
        # ~ {"label": _("Total Purchase Price"), "fieldname": "total_purchase", "fieldtype": "Currency", "width": 100}, -> TBD
        {"label": _("Total SEG Purchase Price"), "fieldname": "total_seg_purchase", "fieldtype": "Currency", "width": 100},
        # ~ {"label": _("DB on Purchase Price CHF"), "fieldname": "db_purchase_price_chf", "fieldtype": "Currency", "width": 100}, -> TBD
        # ~ {"label": _("DB on Purchase Price %"), "fieldname": "db_purchase_price", "fieldtype": "Percent", "width": 100}, -> TBD
        {"label": _("DB on SEG Purchase Price CHF"), "fieldname": "db_seg_price_chf", "fieldtype": "Currency", "width": 100},
        {"label": _("DB on SEG Purchase Price %"), "fieldname": "db_seg_price", "fieldtype": "Percent", "width": 100}
    ]
    return columns

def get_data(filters):
    #Prepare Employee condition
    if filters.get('employee'):
        employee_condition = """AND `tabSales Team`.`sales_person` = '{0}'""".format(filters.get('employee'))
    else:
        employee_condition = """"""
    
    frappe.log_error(employee_condition, "employee_condition")
    # ~ #Prepare Employee condition
    # ~ if filters.get('employee'):
        # ~ user = frappe.get_value("Sales Overview Employee", filters.get('employee'), "user")
        # ~ if user:
            # ~ employee_condition = """AND `tabDelivery Note`.`owner` = {0}""".format(user)
        # ~ else:
            # ~ frappe.msgprint("Fehler beim abrufen des Mitarbeiters")
    # ~ else:
        # ~ employee_condition = """"""
    
    #Get Item Groups
    if filters.get('item_group'):
        main_group = filters.get('item_group')
    else:
        main_group = "Alle Artikelgruppen"
    
    display_groups = get_display_groups(main_group, filters.get('depth'))
    frappe.log_error(display_groups, "display_groups")
    #Collect Data
    datas = []
    for dp in display_groups:
        item_groups = [dp]
        item_groups = get_child_groups(dp, item_groups)
        frappe.log_error(item_groups, "item_groups")
        
        data = frappe.db.sql("""
                                SELECT 
                                    %(item_group)s AS `item_group`,
                                    SUM(`tabDelivery Note Item`.`net_amount`) AS `net_turnover`,
                                    SUM(`tabDelivery Note Item`.`qty`) AS `quantity`,
                                    SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`) AS `total_seg_purchase`,
                                    SUM(`tabDelivery Note Item`.`net_amount`) - SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`) AS `db_seg_price_chf`,
                                    (SUM(`tabDelivery Note Item`.`net_amount`) - SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`)) / SUM(`tabDelivery Note Item`.`net_amount`) * 100 AS `db_seg_price`
                                FROM
                                    `tabDelivery Note Item`
                                LEFT JOIN
                                    `tabItem` ON `tabItem`.`item_code` = `tabDelivery Note Item`.`item_code`
                                LEFT JOIN   
                                    `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
                                LEFT JOIN   
                                    `tabSales Team` ON `tabDelivery Note`.`customer` = `tabSales Team`.`parent`
                                LEFT JOIN
                                    `tabCustomer` ON `tabDelivery Note`.`customer` = `tabCustomer`.`name`
                                WHERE
                                    `tabDelivery Note`.`docstatus` = 1
                                AND
                                    `tabDelivery Note`.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
                                AND
                                    `tabItem`.`item_group` IN %(item_groups)s
                                %(employee_condition)s
                                ;""", {'item_group': dp, 'from_date': filters.get('from_date'), 'to_date': filters.get('to_date'), 'item_groups': tuple(item_groups), 'employee_condition': employee_condition}, as_dict=True)
        
        if len(data) > 0:
            datas.append(data[0])
    
    return datas

def get_display_groups(main_group, depth):
    #Get all group types to be displayed
    depth_sort = ["Product Category", "Product Subcategory", "Product Group", "Item Group"]
    display_types = []
    for g in depth_sort:
        display_types.append(g)
        if g == depth:
            break
    
    display_groups = [main_group]
    display_groups = get_child_display_groups(main_group, display_types, display_groups)
    
    return display_groups

def get_child_display_groups(item_group, display_types, display_groups):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for s in sub_groups:
        if s['item_group_type'] in display_types:
            display_groups.append(s['name'])
        sg = {}
        sg[s['name']] = get_child_display_groups(s['name'], display_types, display_groups)
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for n in nodes:
        if n['item_group_type'] in display_types:
            display_groups.append(n['name'])
    return display_groups

def get_child_groups(item_group, item_groups):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for s in sub_groups:
        item_groups.append(s['name'])
        sg = {}
        sg[s['name']] = get_child_groups(s['name'], item_groups)
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for n in nodes:
        item_groups.append(n['name'])
    return item_groups
    
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
