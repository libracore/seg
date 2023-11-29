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

    # Get all existing pricing rules
    existing_pricing_rules = get_existing_pricing_rules(new_pricing_rule.customer, new_pricing_rule.name, new_pricing_rule.apply_on)
    
    for rule in existing_pricing_rules:
        # Check if the new pricing rule conflicts with any existing rule
        conflict_message = conflicts(new_pricing_rule, rule, new_pricing_rule.apply_on)
        if conflict_message:
            new_pricing_rule.disable = 1
            new_pricing_rule.save(ignore_permissions=True)

            frappe.msgprint(
                msg= conflict_message + "<br><br> <b>This Pricing Rule will be disable until Conflict is solved.</b>",
                title='Pricing Rule Conflict!',
                indicator='red'
            )
    
def get_existing_pricing_rules(customer, new_pricing_rule, apply_on):

    if apply_on == 'Item Group':
        pr_sql_apply_on = """
            `tabPricing Rule Item Group`.`item_group`
            FROM `tabPricing Rule`
            LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule`.`name` = `tabPricing Rule Item Group`.`parent`"""
    elif apply_on == 'Item Code': 
        pr_sql_apply_on = """
            `tabPricing Rule Item Code`.`item_code`
            FROM `tabPricing Rule`
            LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule`.`name` = `tabPricing Rule Item Code`.`parent`"""
            
    sql_query = """
        SELECT `tabPricing Rule`.`name`,
        `tabPricing Rule`.`priority`,
        `tabPricing Rule`.`customer`,
        {pr_sql_apply_on}
        WHERE `tabPricing Rule`.`customer` = '{customer}'
        AND `tabPricing Rule`.`name` != '{name}'
    """.format(customer=customer, name=new_pricing_rule, pr_sql_apply_on=pr_sql_apply_on)
    
    existing_pricing_rules = frappe.db.sql(sql_query, as_dict=True)
    return existing_pricing_rules
    
def conflicts(rule1, rule2, apply_on):
    rule2 = frappe.parse_json(rule2)
    
    if apply_on == 'Item Group':
        rule1_item_group = rule1.item_groups[0].item_group
        
        # Check if the item group is not a parent or child group. If not, check if they have the same item group
        if not is_parent_or_child_group(rule1_item_group, rule2['item_group']) and not is_parent_or_child_group(rule2['item_group'], rule1_item_group):
            # Check for conflicts based on the item group already having a PR
            if rule1_item_group == rule2['item_group']:
                return f"The new rule <a href='#Form/Pricing Rule/{rule1.name}'><b>{rule1.name}</b></a> conflicts with existing rule <a href='#Form/Pricing Rule/{rule2['name']}'><b>{rule2['name']}</b></a> due to the both having the same Item Group." 
        else:
            # Check for conflicts based on priority due to item group hierarchy
            if rule1.priority == rule2['priority']:
                return f"The new rule <a href='#Form/Pricing Rule/{rule1.name}'><b>{rule1.name}</b></a> conflicts with existing rule <a href='#Form/Pricing Rule/{rule2['name']}'><b>{rule2['name']}</b></a> due to the both having the same Priority within the same items group hierarchy."

    elif apply_on == 'Item Code':
        rule1_item_code = rule1.items[0].item_code
        
        # Check for conflicts based on the item code already having a PR
        if rule1_item_code == rule2['item_code']:
            return f"The new rule <a href='#Form/Pricing Rule/{rule1.name}'><b>{rule1.name}</b></a> conflicts with existing rule <a href='#Form/Pricing Rule/{rule2['name']}'><b>{rule2['name']}</b></a> due to the both having the same Item Code."
    return None

def is_parent_or_child_group(parent_group, child_group):
    if parent_group is not None and child_group is not None: 
        # Check if child_group is a child or descendant of parent_group
        parent_child_relationship = frappe.get_all(
            'Item Group',
            filters={'name': parent_group, 'parent_item_group': child_group},
            fields=['name']
        )
        return bool(parent_child_relationship)
