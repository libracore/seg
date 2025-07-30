# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe import _
from seg.seg.shop import get_child_group

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 50},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 80},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": _("Default Supplier"), "fieldname": "default_supplier", "fieldtype": "Link", "options": "Supplier", "width": 120}
    ]
    return columns

def get_data(filters):
    #get all Delivery Note Item Entries within given Dates
    entries = get_dn_positions(from_date=filters.from_date, to_date=filters.to_date)
    
    #Group by Default Suppliers
    if filters.based_on == "Default Supplier":
        #find suppliers
        suppliers = []
        for e in entries:
            if e.get('default_supplier') not in suppliers:
                suppliers.append(e.get('default_supplier'))
    
        # create grouped entries
        output = []
        for s in suppliers:
            details = []
            total_qty = 0
            total_amount = 0
            for e in entries:
                if e.default_supplier == s:
                    total_qty += e.total_qty or 0
                    total_amount += e.total_amount or 0
                    details.append(e)
                    
            # insert supplier row
            output.append({
                'default_supplier': s,
                'total_qty': total_qty,
                'total_amount': total_amount,
                'indent': 0
            })
            
            #Insert Sub Entries
            for d in details:
                output.append(d)
        return output
    elif filters.based_on == "Item Group":
        #Check if Item Group is selected
        if not filters.item_group:
            frappe.throw("Bitte Artikelgruppe angeben")
        
        #Check if given Group has Child Groups
        has_child = frappe.get_value("Item Group", filters.item_group, "is_group")
        
        #Create List with Item Group and all Child Groups
        group_list = []
        
        if has_child:
            groups_to_check = []
            group_list.append(filters.item_group)
            groups_to_check.append(filters.item_group)
            while len(groups_to_check) > 0:
                child_groups, groups_to_check = get_child_groups(groups_to_check)
                for child_group in child_groups:
                    group_list.append(child_group)
        else:
            group_list.append(filters.item_group)
        
        #Create Output according to needed Item Groups
        output = []
        details = []
        total_qty = 0
        total_amount = 0
        
        for e in entries:
            if e.get('item_group') in group_list:
                total_qty += e.get('total_qty')
                total_amount += e.get('total_amount')
                details.append(e)
                
        # Insert Item Group Row
        output.append({
            'item_group': filters.item_group,
            'total_qty': total_qty,
            'total_amount': total_amount,
            'indent': 0
        })
        
        #Insert Sub Entries
        for d in details:
            output.append(d)
        
        return output
    else:
        output = []
        for e in entries:
            e['indent'] = 0
            output.append(e)
            
        return output

def get_dn_positions(from_date=None, to_date=None):
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = "2099-12-31"
    
    positions = frappe.db.sql("""SELECT
                                    `tabItem`.`item_code` AS `item`,
                                    SUM(`tabDelivery Note Item`.`qty`) AS `total_qty`,
                                    SUM(`tabDelivery Note Item`.`amount`) AS `total_amount`,
                                    `tabItem`.`item_name` AS `item_name`,
                                    `tabItem`.`item_group` AS `item_group`,
                                    `tabItem`.`default_supplier` AS `default_supplier`,
                                    1 AS `indent`
                                FROM
                                    `tabDelivery Note Item`
                                LEFT JOIN
                                    `tabItem` ON `tabItem`.`name` = `tabDelivery Note Item`.`item_code`
                                LEFT JOIN
                                    `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
                                WHERE
                                    `tabDelivery Note Item`.`docstatus` = 1
                                AND
                                    DATE(`tabDelivery Note`.`posting_date`) BETWEEN "{from_date}" AND "{to_date}"
                                GROUP BY
                                    `item`
                                ORDER BY
                                    `total_amount` DESC;""".format(from_date=from_date, to_date=to_date), as_dict=True)
                                
    return positions

def get_child_groups(item_groups):
    child_groups = []
    groups_to_check = []
    
    for item_group in item_groups:
        new_groups = frappe.db.sql("""
                                    SELECT
                                        `name`,
                                        `is_group`
                                    FROM
                                        `tabItem Group`
                                    WHERE
                                        `parent_item_group` = '{group}';""".format(group=item_group), as_dict=True)
                                        
        if len(new_groups) > 0:
            for new_group in new_groups:
                child_groups.append(new_group.get('name'))
                if new_group.get('is_group'):
                    groups_to_check.append(new_group.get('name'))
                    
    return child_groups, groups_to_check
