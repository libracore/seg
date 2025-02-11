# Copyright (c) 2013-2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from seg.seg.pricing_rule_validation import validate_pricing_rule
from frappe.utils.data import cint


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Item"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 75},
        {"label": _("Price list rate"), "fieldname": "price_list_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Pricing Rule"), "fieldname": "pricing_rule", "fieldtype": "Link", "options": "Pricing Rule", "width": 120},
        {"label": _("Discount"), "fieldname": "discount_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Rate"), "fieldname": "discounted_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("DB1"), "fieldname": "db1", "fieldtype": "Currency", "width": 100},
        {"label": _("DB1 [%]"), "fieldname": "db1_percent", "fieldtype": "Percent", "width": 100}
    ]

def get_data(filters):
    if not filters.item_group:
        filters.item_group = "%"
    sql_query = """SELECT
          `aggr`.`item_code`,
          `aggr`.`item_name`,
          `aggr`.`item_group`,
          `aggr`.`stock_uom`,
          `aggr`.`price_list_rate`,
          `aggr`.`pricing_rule`,
          `aggr`.`discount_percentage`,
          `aggr`.`discounted_rate`,
          `aggr`.`db1`,
          ((`aggr`.`db1` / `aggr`.`discounted_rate`) * 100) AS `db1_percent`
          FROM (SELECT
          `raw`.`item_code`,
          `raw`.`item_name`,
          `raw`.`item_group`,
          `raw`.`stock_uom`,
          `raw`.`price_list_rate`,
          `raw`.`pricing_rule`,
          `tPR`.`discount_percentage` AS `discount_percentage`,
          ((100 - `tPR`.`discount_percentage`)/100) * `raw`.`price_list_rate` AS `discounted_rate`,
          ((((100 - `tPR`.`discount_percentage`)/100) * `raw`.`price_list_rate`) - `raw`.`last_purchase_rate`) AS `db1`
        FROM (
        SELECT
          `item`.`item_code` AS `item_code`,
          `item`.`item_name` AS `item_name`,
          `item`.`item_group` AS `item_group`,
          IF(`item`.`last_purchase_rate` = 0, `item`.`valuation_rate`, `item`.`last_purchase_rate`) AS `last_purchase_rate`,
          CONCAT(ROUND(`item`.`weight_per_unit`, 1), " ", `item`.`weight_uom`) AS `stock_uom`,
          (SELECT `tabItem Price`.`price_list_rate`
           FROM `tabItem Price`
           WHERE `tabItem Price`.`item_code` = `item`.`item_code`
             AND `tabItem Price`.`price_list` = "Standard-Vertrieb") AS `price_list_rate`,
          (SELECT `tabPricing Rule`.`name`
           FROM `tabPricing Rule`
           LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule Item Code`.`parent` = `tabPricing Rule`.`name`
           LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule Item Group`.`parent` = `tabPricing Rule`.`name`
           LEFT JOIN `tabItem Group` ON `tabItem Group`.`name` = `tabPricing Rule Item Group`.`item_group`
           WHERE `tabPricing Rule`.`selling` = 1
             AND `tabPricing Rule`.`customer` = "{customer}"
             AND `tabPricing Rule`.`disable` = 0
             AND (`tabPricing Rule Item Code`.`item_code` = `item`.`item_code`
                  OR (SELECT `grp`.`lft` FROM `tabItem Group` AS `grp` WHERE `grp`.`name` = `item`.`item_group`)
                      BETWEEN `tabItem Group`.`lft` AND `tabItem Group`.`rgt`
                )
           ORDER BY `tabPricing Rule`.`priority` DESC
           LIMIT 1) AS `pricing_rule`
        FROM `tabItem` AS `item`
        WHERE
          `item`.`is_sales_item` = 1
          AND `item`.`disabled` = 0
          AND `item`.`has_variants` = 0
          AND `item`.`item_group` LIKE "{item_group}") AS `raw`
        LEFT JOIN `tabPricing Rule` AS `tPR` ON `tPR`.`name` = `raw`.`pricing_rule`
        ) AS `aggr`;""".format(customer=filters.customer, item_group=filters.item_group)
    data = frappe.db.sql(sql_query, as_list=True)
    return data

@frappe.whitelist()
def create_pricing_rule(customer, discount_percentage, product_category=None, product_subcategory=None, product_group=None, item_group=None, item_code=None, ignore_permissions=False):
    # check if a similar set exists already
    
    if product_category:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "Product Category"}, "rule_priority")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio, 'item_group': product_category}, fields=['name'])
    elif product_subcategory:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "Product Subcategory"}, "rule_priority")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio, 'item_group': product_subcategory}, fields=['name'])
    elif product_group:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "Product Group"}, "rule_priority")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio, 'item_group': product_group}, fields=['name'])
    elif item_group:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "Item Group"}, "rule_priority")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio, 'item_group': item_group}, fields=['name'])
    elif item_code:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "Item"}, "rule_priority")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio, 'item_code': item_code}, fields=['name'])
    else:
        target_prio = frappe.get_value("Item Group Priority", {'rule_type': "General"}, "rule_priority")
        frappe.log_error(target_prio, "target_prio General")
        matches = frappe.get_all("Pricing Rule", filters={'customer': customer, 'priority': target_prio}, fields=['name'])
    
    if not target_prio:
        frappe.throw("Please define priority in SEG Settings")
    elif cint(target_prio) > 20:
        frappe.throw("Priority can not be higher than 20, please check SEG Settings")
    
    if matches and len(matches) > 0:
        # update discount of existing rule
        pricing_rule = frappe.get_doc("Pricing Rule", matches[0]['name'])
        pricing_rule.discount_percentage = discount_percentage
        pr = pricing_rule.save(ignore_permissions=ignore_permissions)
    else:
        # create new pricing rule
        pricing_rule = frappe.get_doc({
            'doctype': "Pricing Rule",
            'selling': 1,
            'applicable_for': 'Customer',
            'customer': customer,
            'price_or_discount': 'Discount Percentage',
            'discount_percentage': discount_percentage,
            'priority': target_prio,
            'price_or_product_discount': 'Price'
         })
        if product_category or product_subcategory or product_group or item_group:
            pricing_rule.title = ("{c} {g} ({d})".format(c=customer, g=product_category or product_subcategory or product_group or item_group, d=discount_percentage)).replace(",", "")
            pricing_rule.apply_on = "Item Group"
            pricing_rule.item_group = product_category or product_subcategory or product_group or item_group
            pricing_rule.append("item_groups", {
                'item_group': product_category or product_subcategory or product_group or item_group
            })
        elif item_code:
            pricing_rule.title = ("{c} {i} ({d})".format(c=customer, i=item_code, d=discount_percentage)).replace(",", "")
            pricing_rule.apply_on = "Item Code"
            pricing_rule.item_code = item_code
            pricing_rule.append("items", {
                'item_code': item_code
            })
        else:
            pricing_rule.title = ("{c} Basis ({d})".format(c=customer, d=discount_percentage)).replace(",", "")
            pricing_rule.apply_on = "Item Group"
            pricing_rule.item_group = "Alle Artikelgruppen"
            pricing_rule.append("item_groups", {
                'item_group': pricing_rule.item_group
            })
        pr = pricing_rule.insert(ignore_permissions=ignore_permissions)

    validate_pricing_rule(pr.name)
    return pr.name
