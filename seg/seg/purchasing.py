# Copyright (c) 2025, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import json

@frappe.whitelist()
def get_taxes_template(supplier):
    #Get Country of Supplier
    country = frappe.get_value("Supplier", supplier, "country")
    
    #get and return template
    template = None
    if country == "Schweiz":
        template = frappe.get_value("SEG Settings", "SEG Settings", "switzerland_purchase_taxes")
    else:
        template = frappe.get_value("SEG Settings", "SEG Settings", "foreign_purchase_taxes")
        
    return template

#update default supplier if imported Items
def update_default_supplier():
    affected_items = frappe.db.sql("""
                                    SELECT
                                        `tabItem`.`name` AS `item_code`,
                                        `tabItem`.`default_supplier` AS `default_supplier`,
                                        `tabItem Supplier`.`supplier`
                                    FROM
                                        `tabItem`
                                    INNER JOIN
                                        `tabItem Supplier` ON `tabItem Supplier`.`parent` = `tabItem`.`name`
                                    WHERE
                                        `tabItem Supplier`.`idx` = 1
                                    AND
                                        `tabItem`.`default_supplier` != `tabItem Supplier`.`supplier` OR `tabItem`.`default_supplier` IS NULL
                                    AND
                                        `tabItem`.disabled = 0""", as_dict=True)
    
    for item in affected_items:
        item_doc = frappe.get_doc("Item", item.get('item_code'))
        
        #Set French to avoid Mandatory Errors
        if not item_doc.get('item_name_fr'):
            item_doc.item_name_fr = "-"
            
        if not item_doc.get('description_fr'):
            item_doc.description_fr = "-"
            
        if len(item_doc.get('more_images')) > 0:
            for image in item_doc.get('more_images'):
                if not image.get('description_fr'):
                    image.description_fr = "-"
        
        item_doc.default_supplier = item_doc.supplier_items[0].supplier
            
        try:
            item_doc.save()
        except Exception as e:
            frappe.log_error(str(e), "Fehler beim der Standardlieferantenaktualisierung")
            
    return


#Set Default Supplier when Item Price is saved
def set_price_supplier(self, event):
    self.default_supplier = frappe.get_value("Item", self.get('item_code'), "default_supplier")

#Update Prices when Default Supplier in Item has changed
def set_supplier_on_prices(self, event):
    if not self.is_new():
        old_doc = frappe.get_doc("Item", self.get('name'))
        if self.get('default_supplier') != old_doc.get('default_supplier'):
            update_items_prices = frappe.db.sql("""
                                                UPDATE
                                                    `tabItem Price`
                                                SET
                                                    `default_supplier` = '{supplier}'
                                                WHERE
                                                    `item_code` = '{item}'""".format(supplier=self.get('default_supplier'), item=self.get('name')), as_dict=True)
            frappe.db.commit()
    return

@frappe.whitelist()
def get_updated_seg_prices(items, price_list):
    items = json.loads(items)
    for item in items:
        item_price = frappe.get_all(
            "Item Price",
            filters={
                        'item_code': item.get('item_code'),
                        'price_list': price_list,
                        'supplier': ""},
            fields=["name"]
            )

        
        if len(item_price) > 0:
            item_price_doc = frappe.get_doc("Item Price", item_price[0])
            item['freight_costs'] = item_price_doc.get('freight_costs') or 0
            item['currency_exchange_fees'] = item_price_doc.get('currency_exchange_fee') or 0
            item['seg_purchase_price'] = item.get('rate') + (item.get('rate') / 100 * (item_price_doc.get('currency_exchange_fee') or 0)) + (item_price_doc.get('freight_costs') or 0)
    return items

@frappe.whitelist()
def update_item_seg_price(items):
    items = json.loads(items)
    for item in items:
        #get purchase receipt items
        receipt_info = frappe.db.sql("""
                                    SELECT
                                        `qty`,
                                        `seg_purchase_price`
                                    FROM
                                        `tabPurchase Receipt Item`
                                    WHERE
                                        `docstatus` = 1
                                    AND
                                        `item_code` = %(item_code)s;""", {'item_code': item.get('item_code')}, as_dict=True)
        #Set SEG Price in Item
        seg_price = 0
        total_qty = 0
        total_price = 0
        if len(receipt_info) > 0:
            for receipt in receipt_info:
                if receipt.get('seg_purchase_price'):
                    total_qty += receipt.get('qty')
                    total_price += receipt.get('seg_purchase_price') * receipt.get('qty')
            seg_price = total_price / total_qty
        frappe.db.set_value("Item", item.get('item_code'), "seg_purchase_price", seg_price)
    
    return
