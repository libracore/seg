# Copyright (c) 2017-2026, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint

@frappe.whitelist()
def get_entry_warehouse_items():
    #Get Entry Warehouse
    entry_warehouse = frappe.db.get_single_value("SEG Settings", "entry_warehouse")
    
    #Get all Items in Entry Warehouse
    items = frappe.get_all("Bin", filters={"warehouse": entry_warehouse}, fields=["item_code", "actual_qty"])
    frappe.log_error("items", items)
    #Prepare response
    if len(items) > 0:
        frappe.log_error("entered_items", items)
        response = []
        for item in items:
            #Get Item Doc
            item_doc = frappe.get_doc("Item", item.get('item_code'))
            
            #Add Information for this item to response
            item_response = {
                        'item_code': item.get('item_code'),
                        'picture': item_doc.get('image') or "",
                        'content': {
                            'qty': item.get('actual_qty'),
                            'item_name': item_doc.get('item_name'),
                            'locations': get_item_locations(item.get('item_code')),
                            'stored_qty': 0
                        }}
        
            response.append(item_response)
    else:
        response = None
    
    return response

def get_item_locations(item_code):
    #Get all Item Locations
    warehouses = frappe.get_all("Bin", filters={"item_code": item_code}, fields=["warehouse", "actual_qty"])
    
    #Return Information String
    if len(warehouses) > 0:
        wh_info = ""
        for index, wh in enumerate(warehouses):
            if index == 0:
                wh_info += "{0}({1})".format(wh.get('warehouse'), cint(wh.get('actual_qty')))
            else:
                wh_info += ", {0}({1})".format(wh.get('warehouse'), cint(wh.get('actual_qty')))
    else:
        wh_info = None
    
    return wh_info
