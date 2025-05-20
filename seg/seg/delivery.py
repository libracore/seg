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
