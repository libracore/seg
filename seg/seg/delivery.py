# Copyright (c) 2025, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import json
from erpnext.stock.utils import get_stock_balance
from seg.seg.utils import convert_material
from erpnext.stock.utils import get_stock_balance
from frappe.utils import nowdate

@frappe.whitelist()
def check_barcodes(doc):
    doc = json.loads(doc)
    
    updated_barcodes = []
    
    #check barcodes and ad updated barcodes to list
    for item in doc.get('items'):
        match = False
        item_doc = frappe.get_doc("Item", item.get('item_code'))
        if item_doc.get('barcodes'):
            for barcode in item_doc.get('barcodes'):
                if item.get('barcode') == barcode.get('barcode'):
                    match = True
        
        if not match:
            updated_barcodes.append({'line_name': item.get('name'), 'item_code': item.get('item_code'), 'barcode': item_doc.barcodes[0].barcode if item_doc.barcodes else None })
                
    return updated_barcodes

@frappe.whitelist()
def check_alternative_items(items):
    items = json.loads(items)
    warehouse = frappe.db.get_single_value("SEG Settings", "main_warehouse")
    
    affected_items = []
    for item in items:
        #Check if Item has enough Stock to deliver
        stock_qty = get_stock_balance(item.get('item_code'), warehouse)
        if item.get('qty') > stock_qty:
            #Check if item is Purchase Item
            is_purchase_item = frappe.get_value("Item", item.get('item_code'), "is_purchase_item")
            if not is_purchase_item:
                #If Item is not purchase Item, Check if it has an Alternative
                alternative_items = frappe.get_all("Item Alternative", filters=[["item_code", "=", item.get('item_code')]], fields=["alternative_item_code"])
                if alternative_items:
                    affected_items.append({'item': item.get('item_code'), 'alternative_item': alternative_items[0].get('alternative_item_code'), 'qty': item.get('qty') - stock_qty})
                else:
                    alternative_items = frappe.get_all("Item Alternative", filters=[["alternative_item_code", "=", item.get('item_code')], ["two_way", "=", 1]], fields=["item_code"])
                    if alternative_items:
                        affected_items.append({'item': item.get('item_code'), 'alternative_item': alternative_items[0].get('item_code'), 'qty': item.get('qty') - stock_qty})
    #Create Message if there are affected Items
    if len(affected_items) > 0:
        message = 'Achtung folgende Artikel sind nicht genügend an Lager und sollten umgebucht werden:<br>'
        for affected_item in affected_items:
            message += '<br><a href="desk#Form/Item/{item_code}" target="_blank">{item_code} (Wird umgebucht von {alt_item})</a>'.format(item_code=affected_item.get('item'), alt_item=affected_item.get('alternative_item'))
        message += '<br><br>Möchtest du diese Artikel direkt umbuchen?'
        return message, affected_items
    else:
        return None

@frappe.whitelist()
def restock_items(items):
    items = json.loads(items)
    warehouse = frappe.db.get_single_value("SEG Settings", "main_warehouse")
    #Check if items can be restocked
    for i in items:
        stock_qty = get_stock_balance(i.get('alternative_item'), warehouse, posting_date=nowdate())
        if i.get('qty') > stock_qty:
            frappe.throw("Alternativer Artikel {0} hat nur noch {1} Stock an Lager und kann deshalb nicht umgelagert werden. (Umlagerungsmenge: {2})".format(i.get('alternative_item'), stock_qty, i.get('qty')))
    #Restock Items
    for item in items:
        convert_material(item.get('alternative_item'), item.get('item'), warehouse, item.get('qty'))
    return True

#Update Field "Delivery Note" qty in Sales Orders
def update_delivery_note_qty(self, event):
    handeled_so = []
    for item in self.items:
        if item.against_sales_order and item.against_sales_order not in handeled_so:
            #get all Delivery Notes
            delivery_notes = frappe.db.sql("""
                                            SELECT
                                                `tabDelivery Note`.`name` AS `dn`
                                            FROM
                                                `tabDelivery Note`
                                            LEFT JOIN
                                                `tabDelivery Note Item` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
                                            WHERE
                                                `tabDelivery Note`.`docstatus` < 2
                                            AND
                                                `tabDelivery Note Item`.`against_sales_order` = %(so)s
                                            GROUP BY
                                                `tabDelivery Note`.`name`;""", {'so': item.against_sales_order}, as_dict=True)
            
            #Update Sales Order
            if len(delivery_notes) > 0:
                if event == "on_trash":
                    dn_qty = len(delivery_notes) - 1
                else:
                    dn_qty = len(delivery_notes)
                frappe.db.set_value("Sales Order", item.against_sales_order, "delivery_note_qty", dn_qty or 0)
            else:
                frappe.db.set_value("Sales Order", item.against_sales_order, "delivery_note_qty", 0)
            
            handeled_so.append(item.against_sales_order)
