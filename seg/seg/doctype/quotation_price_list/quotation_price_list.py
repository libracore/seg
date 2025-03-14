# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from seg.seg.shop import get_recursive_item_groups
import re

class QuotationPriceList(Document):
	pass

@frappe.whitelist()
def get_new_items(doc):
    doc = json.loads(doc)
    
    new_items = []
    imported_templates = []
    something_to_import = False
    items = []
    
    #get items to import
    for template in doc.get('templates'):
        if not template.get('items_set') == 1:
            #get prices for all items
            prices = get_prices(template.get('item_code'), doc.get('customer'))
            #check if it is a template or a single item
            is_template = frappe.get_value("Item", template.get('item_code'), "has_variants")
            #if it is a template, get all variants
            if is_template:
                items = frappe.db.sql("""
                                        SELECT
                                            `tabItem`.`item_code`,
                                            `tabItem`.`variant_of`,
                                            GROUP_CONCAT(`tabItem Variant Attribute`.`attribute_value` SEPARATOR ', ') AS `attribute_value`
                                        FROM
                                            `tabItem`
                                        LEFT JOIN
                                            `tabItem Variant Attribute` ON `tabItem Variant Attribute`.`parent` = `tabItem`.`name`
                                        WHERE
                                            `tabItem`.`variant_of` = '{template}'
                                        AND
                                            `tabItem`.`disabled` = 0
                                        GROUP BY
                                            `tabItem`.`item_code`, `tabItem`.`item_code`""".format(template=template.get('item_code')), as_dict=True)
            #if it is a single item, just add this item
            else:
                items = [{'item_code': template.get('item_code'), 'variant_of': template.get('item_code')}]
        #get price for each item, add item and releated price to new items
        if len(items) > 0:
            for item in items:
                item_price = None
                for price in prices:
                    if item.get('item_code') == price.get('item_code'):
                        item_price = price.get('discounted_rate')
                        price_list_rate = price.get('price_list_rate')
                        discount = price.get('discount_percentage')
                new_items.append({'item_code': item.get('item_code'), 'variant_of': item.get('variant_of'), 'item_price': item_price, 'price_list_rate': price_list_rate, 'kg_price': template.get('calculate_kg_and_l'), 'discount': discount, 'variant': item.get('attribute_value')})
            
            #add template to imported templates and set flag for JS
            imported_templates.append(template.get('name'))
            something_to_import = True
    
    return {
            'something_to_import': something_to_import,
            'new_items': new_items,
            'imported_templates': imported_templates
            }

@frappe.whitelist()
def get_prices(item_code, customer):
    # find recursive item groups
    item_groups = get_recursive_item_groups(frappe.get_value("Item", item_code, "item_group"))
    sql_query = """SELECT 
            `raw`.`item_code`,
            `raw`.`item_name`,
            `raw`.`item_group`,
            GROUP_CONCAT(`tabItem Variant Attribute`.`attribute_value{lang}`) AS `attributes`,
            `raw`.`stock_uom`,
            ROUND(`raw`.`price_list_rate`, 2) AS `price_list_rate`,
            `raw`.`pricing_rule`,
            `tPR`.`discount_percentage` AS `discount_percentage`,
            ROUND(((100 - IFNULL(`tPR`.`discount_percentage`, 0))/100) * `raw`.`price_list_rate`, 2) AS `discounted_rate`
        FROM 
            (SELECT 
              `tabItem`.`item_code` AS `item_code`,
              `tabItem`.`item_name{lang}` AS `item_name`,
              `tabItem Group`.`item_group_name{lang}` AS `item_group`,
              `tabItem`.`last_purchase_rate` AS `last_purchase_rate`,
              CONCAT(ROUND(`tabItem`.`weight_per_unit`, 1), " ", `tabItem`.`weight_uom`) AS `stock_uom`,
              (SELECT `tabItem Price`.`price_list_rate` 
               FROM `tabItem Price` 
               WHERE `tabItem Price`.`item_code` = `tabItem`.`item_code`
                 AND `tabItem Price`.`price_list` = "Standard-Vertrieb") AS `price_list_rate`,
              (SELECT `tabPricing Rule`.`name`
               FROM `tabPricing Rule`
               LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule Item Code`.`parent` = `tabPricing Rule`.`name`
               LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule Item Group`.`parent` = `tabPricing Rule`.`name`
               WHERE `tabPricing Rule`.`selling` = 1
                 AND `tabPricing Rule`.`customer` = "{customer}"
                 AND `tabPricing Rule`.`disable` = 0
                 AND (`tabPricing Rule Item Code`.`item_code` = `tabItem`.`item_code`
                      OR `tabPricing Rule Item Group`.`item_group` IN ({item_groups})
                      OR `tabPricing Rule Item Group`.`item_group` = "Alle Artikelgruppen")
               ORDER BY `tabPricing Rule`.`priority` DESC
               LIMIT 1) AS `pricing_rule`
            FROM `tabItem`
            LEFT JOIN `tabItem Group` ON `tabItem`.`item_group` = `tabItem Group`.`name`
            WHERE `tabItem`.`item_code` = "{item_code}"
              OR `tabItem`.`variant_of` = "{item_code}"
            ) AS `raw`
        LEFT JOIN `tabPricing Rule` AS `tPR` ON `tPR`.`name` = `raw`.`pricing_rule`
        LEFT JOIN `tabItem Variant Attribute` ON `raw`.`item_code` = `tabItem Variant Attribute`.`parent`
        GROUP BY `raw`.`item_code`
    """.format(customer=customer, item_code=item_code, item_groups=", ".join('"{w}"'.format(w=w) for w in item_groups), lang = "")
    data = frappe.db.sql(sql_query, as_dict=True)
    return data

@frappe.whitelist()
def get_kg_and_l_price(row):
    row = json.loads(row)
    
    #get item Attribute
    item_attribute = frappe.db.sql("""
                                    SELECT
                                        `attribute_value`
                                    FROM
                                        `tabItem Variant Attribute`
                                    WHERE
                                        `attribute` = "Gebinde"
                                    AND
                                        `parent` = '{item}'""".format(item=row.get('item_code')), as_dict=True)
                                        
    if len(item_attribute) > 0:
        item_attribute_value = item_attribute[0].get('attribute_value')
    else:
        frappe.throw("Kein Gebinde Attribut in Artikel {0} gefunden!".format(row.get('item_code')))
        
    #get unit of Attribute (kg or l)
    qty, unit = extract_unit(item_attribute[0].get('attribute_value'))
    
    if not qty or not unit:
        frappe.throw("Gebinde Attribut von Artikel {0} konnte nicht gelesen werden! Bitte Attribut überprüfen.".format(row.get('item_code')))
        
    #Calculate kg and Liter prices
    density = frappe.get_value("Item", row.get('item_code'), "density")
    if unit == "L":
        liter_price = row.get('item_price') / qty
        kg_price = liter_price / density
    elif unit == "KG":
        kg_price = row.get('item_price') / qty
        liter_price = kg_price * density
    else:
        frappe.throw("Gebinde Attribut von Artikel {0} konnte nicht gelesen werden! Bitte Attribut überprüfen.".format(row.get('item_code')))
        
    #Return Prices
    return {'liter_price': liter_price, 'kg_price': kg_price}

def extract_unit(s):
    match = re.match(r"^(\d+(\.\d+)?)(KG|L)", s, re.IGNORECASE)
    if match:
        qty = float(match.group(1))
        unit = match.group(3).upper()
        return qty, unit
    return None, None

@frappe.whitelist()
def get_customer_group(user):
    first_name = frappe.get_value("User", user, "first_name")
    customer_group = None
    customer_group = frappe.get_value("Customer Group", first_name, "name")
    return customer_group
