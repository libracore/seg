# Copyright (c) 2025, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import json

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
    
    affected_items = []
    for item in items:
        is_purchase_item = frappe.get_value("Item", item.get('item_code'), "is_purchase_item")
        if not is_purchase_item:
            alternative_items = frappe.get_all("Item Alternative", filters=[["item_code", "=", item.get('item_code')]])
            if alternative_items:
                affected_items.append(item.get('item_code'))
            else:
                alternative_items = frappe.get_all("Item Alternative", filters=[["alternative_item_code", "=", item.get('item_code')], ["two_way", "=", 1]])
                if alternative_items:
                    affected_items.append(item.get('item_code'))
    
    if len(affected_items) > 0:
        message = "Achtung Artikelalternative buchen bei Artikel:<br>"
        for affected_item in affected_items:
            message += "<br><a href='desk#Form/Item/{item_code}' target='_blank'>{item_code}</a>".format(item_code=affected_item)
        frappe.msgprint(message, "Achtung")
