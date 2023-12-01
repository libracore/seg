# Copyright (c) 2021-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json

# Custom Server Script for Pricing Rule Validation
@frappe.whitelist()
def validate_pricing_rule(new_pr_name):
    # Get info on new pricing rule
    new_pricing_rule = frappe.get_doc("Pricing Rule", new_pr_name)

    # Get if a conflict exist within an already existen pricing rule
    conflict_for_pricing_rule = get_conflicts_for_pricing_rules(new_pricing_rule.customer, new_pricing_rule)

    if conflict_for_pricing_rule:
        new_pricing_rule.disable = 1
        new_pricing_rule.save(ignore_permissions=True)

        frappe.msgprint(
            msg= conflict_for_pricing_rule + "<br><br> <b>This Pricing Rule will be disable until Conflict is solved.</b>",
            title='Pricing Rule Conflict!',
            indicator='red'
        )

def get_conflicts_for_pricing_rules(customer, new_pricing_rule):
    pr_sql_same_priority = None
    conflict_same_category = None
    conflict_same_priority = None
    
    # Get sql conditions for Pricing Rules base on Item Groups 
    if new_pricing_rule.apply_on == 'Item Group':
        item_group = frappe.get_doc("Item Group", new_pricing_rule.item_groups[0].item_group)
        pr_sql_apply_on = """
            `tabPricing Rule Item Group`.`item_group`
            FROM `tabPricing Rule`
            LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule`.`name` = `tabPricing Rule Item Group`.`parent`
            LEFT JOIN `tabItem Group` ON `tabItem Group`.`name` = `tabPricing Rule Item Group`.`item_group` """
        pr_sql_same_category = """ AND `tabPricing Rule Item Group`.`item_group` = '{item_group}' """.format(item_group=item_group.name)
        pr_sql_same_priority = """ 
            AND ((
                `tabItem Group`.`lft` < '{lft}' AND `tabItem Group`.`rgt` > '{rgt}'
                AND (
                    '{lft}' BETWEEN `tabItem Group`.`lft` AND `tabItem Group`.`rgt`
                    AND '{rgt}' BETWEEN `tabItem Group`.`lft` AND `tabItem Group`.`rgt`
                )
            ) OR (`tabItem Group`.`lft` > '{lft}' AND `tabItem Group`.`rgt` < '{rgt}'))
            AND `tabPricing Rule`.`priority` = '{priority}'
            ORDER BY ABS('{lft}' - `tabItem Group`.`lft`) ASC
            LIMIT 1 """.format(lft=item_group.lft, rgt=item_group.rgt, priority=new_pricing_rule.priority)

    # Get sql conditions for Pricing Rules base on Item Codes 
    elif new_pricing_rule.apply_on == 'Item Code': 
        pr_sql_apply_on = """
            `tabPricing Rule Item Code`.`item_code`
            FROM `tabPricing Rule`
            LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule`.`name` = `tabPricing Rule Item Code`.`parent`"""
        pr_sql_same_category = """ AND `tabPricing Rule Item Code`.`item_code` = '{item_code}' """.format(item_code=new_pricing_rule.items[0].item_code)

    # Main sql
    sql_query = """
        SELECT `tabPricing Rule`.`name`,
        `tabPricing Rule`.`priority`,
        `tabPricing Rule`.`customer`,
        {pr_sql_apply_on}
        WHERE `tabPricing Rule`.`customer` = '{customer}'
        AND `tabPricing Rule`.`name` != '{name}'
        AND `tabPricing Rule`.`disable` = 0
    """.format(customer=new_pricing_rule.customer, name=new_pricing_rule.name, pr_sql_apply_on=pr_sql_apply_on)
    
    if pr_sql_same_priority is not None:
        sql_query += pr_sql_same_priority
        conflict_same_priority = frappe.db.sql(sql_query, as_dict=True)
        
        if conflict_same_priority:
            print("Conflic! Same priority <br> {0}".format(conflict_same_priority))
            return f"The new rule <a href='#Form/Pricing Rule/{new_pricing_rule.name}'><b>{new_pricing_rule.name}</b></a> conflicts with existing rule <a href='#Form/Pricing Rule/{conflict_same_priority[0].name}'><b>{conflict_same_priority[0].name}</b></a> due to the both having the same Priority within the same items group hierarchy."
    else:
        sql_query += pr_sql_same_category
        conflict_same_category = frappe.db.sql(sql_query, as_dict=True)
        
        if conflict_same_category:
            print("Conflic! Same category <br> {0}".format(conflict_same_category))
            return f"The new rule <a href='#Form/Pricing Rule/{new_pricing_rule.name}'><b>{new_pricing_rule.name}</b></a> conflicts with existing rule <a href='#Form/Pricing Rule/{conflict_same_category[0].name}'><b>{conflict_same_category[0].name}</b></a> due to the both having the same {new_pricing_rule.apply_on}."
