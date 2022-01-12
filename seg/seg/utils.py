# Copyright (c) 2017-2021, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

# customisation for total weight calculation
import frappe
import json
import six
from erpnext.portal.product_configurator.utils import get_next_attribute_and_values

@frappe.whitelist()
def get_total_weight(items, qtys, kgperL=1.5):
    total_weight = 0
    if isinstance(items, six.string_types):
        items = json.loads(items)
    if isinstance(qtys, six.string_types):
        qtys = json.loads(qtys)
    i = 0
    while i < len(items):
        doc = frappe.get_doc("Item", items[i])
        if doc != None:
            if doc.weight_per_unit > 0 and doc.has_weight:
                if doc.weight_uom == "kg":
                    total_weight += qtys[i] * doc.weight_per_unit
                elif doc.weight_uom == "L":
                    # make sure, tabItem contains custom field (float) density!
                    total_weight += qtys[i] * doc.density * doc.weight_per_unit
        i += 1
    return { 'total_weight': total_weight }

@frappe.whitelist()
def get_user_image(user):
    return frappe.get_value("User", user, "user_image")

@frappe.whitelist()
def get_matching_variant(item_code, old_selection, new_selection):
    attributes = json.loads(new_selection)
    for a in json.loads(old_selection):
        # refine search, add attribute
        for k,v in a.items():
            if k not in attributes:
                attributes[k] = v
        # check if there are multiple variants matching
        matches = get_next_attribute_and_values(item_code, attributes)
        if len(matches['filtered_items']) == 1:
            # leave with this variant code
            return list(matches['filtered_items'])[0]
    # nothing found
    return None

@frappe.whitelist()
def get_prices(item_code, user):
    from erpnext.controllers.website_list_for_contact import get_customers_suppliers
    customers, suppliers = get_customers_suppliers("Sales Invoice", user)
    if len(customers) > 0:
        customer = customers[0]
    else:
        customer  = "None"
    sql_query = """SELECT 
            `raw`.`item_code`,
            `raw`.`item_name`,
            `raw`.`item_group`,
            GROUP_CONCAT(`tabItem Variant Attribute`.`attribute_value`) AS `attributes`,
            `raw`.`stock_uom`,
            ROUND(`raw`.`price_list_rate`, 2) AS `price_list_rate`,
            `raw`.`pricing_rule`,
            `tPR`.`discount_percentage` AS `discount_percentage`,
            ROUND(((100 - IFNULL(`tPR`.`discount_percentage`, 0))/100) * `raw`.`price_list_rate`, 2) AS `discounted_rate`
        FROM 
            (SELECT 
              `tabItem`.`item_code` AS `item_code`,
              `tabItem`.`item_name` AS `item_name`,
              `tabItem`.`item_group` AS `item_group`,
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
                      OR `tabPricing Rule Item Group`.`item_group` = `tabItem`.`item_group`
                      OR `tabPricing Rule Item Group`.`item_group` = "Alle Artikelgruppen")
               ORDER BY `tabPricing Rule`.`priority` DESC
               LIMIT 1) AS `pricing_rule`
            FROM `tabItem`
            WHERE `tabItem`.`item_code` = "{item_code}"
              OR `tabItem`.`variant_of` = "{item_code}"
            ) AS `raw`
        LEFT JOIN `tabPricing Rule` AS `tPR` ON `tPR`.`name` = `raw`.`pricing_rule`
        JOIN `tabItem Variant Attribute` ON `raw`.`item_code` = `tabItem Variant Attribute`.`parent`
        GROUP BY `raw`.`item_code`
    """.format(customer=customer, item_code=item_code)
    data = frappe.db.sql(sql_query, as_dict=True)
    return data

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    from frappe.auth import LoginManager
    lm = LoginManager()
    lm.authenticate(usr, pwd)
    return frappe.local.session
