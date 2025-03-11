# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

class QuotationPriceList(Document):
	pass

@frappe.whitelist()
def get_new_items(doc):
    doc = json.loads(doc)
    
    new_items = []
    imported_templates = []
    something_to_import = False
    
    #get items to import
    for template in doc.get('templates'):
        if not template.get('items_set'):
            is_template = frappe.get_value("Item", template.get('item_code'), "has_variants")
            if is_template:
                items = frappe.db.sql("""
                                        SELECT
                                            `item_code`
                                        FROM
                                            `tabItem`
                                        WHERE
                                            `is_variant_of` = '{template}'
                                        AND
                                            `disabled` = 0""".format(template=template.get('item_code')), as_dict=True)
            else:
                items = {'item_code': template.get('item_code')}
        
        if len(items) > 0:
            for item in items:
                new_items.append({'item_code': item.get('item_code'), 'item_price': 1.5})
                
            imported_templates.append(template.get('name'))
            something_to_import = True
        
        return {
                'something_to_import': something_to_import,
                'new_items': new_items,
                'imported_templates': imported_templates
                }
