# Copyright (c) 2025, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

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
