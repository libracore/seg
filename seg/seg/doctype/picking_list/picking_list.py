# Copyright (c) 2026, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PickingList(Document):
	pass

#Update Sales Order on SUbmit or Cancel of Document
def update_so(self, event):
    #Update Sales Order
    actual_pl_qty = frappe.get_value("Sales Order", self.get('sales_order'), "picking_list_qty")
    if event == "on_submit":
        new_pl_qty = actual_pl_qty + 1
    else:
        new_pl_qty = actual_pl_qty - 1
    frappe.set_value("Sales Order", self.get('sales_order'), "picking_list_qty", new_pl_qty)
    
    #Update Sales Order Items
    for item in self.items:
        actual_qty = frappe.get_value("Sales Order Item", item.get('so_detail'), "picking_list_qty")
        if event == "on_submit":
            new_qty = actual_qty + item.get('qty')
        else:
            new_qty = actual_qty - item.get('qty')
        frappe.set_value("Sales Order Item", item.get('so_detail'), "picking_list_qty", new_qty)
    return
