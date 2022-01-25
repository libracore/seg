# Copyright (c) 2017-2022, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt
#
# Open API for headless shops

import frappe

@frappe.whitelist(allow_guest=True)
def get_item_groups():
    # grab root node
    root_node = frappe.db.sql("""SELECT `name` FROM `tabItem Group` 
        WHERE (`parent_item_group` IS NULL OR `parent_item_group` = "");""", 
        as_dict=True)[0]['name']
    return get_child_group(root_node)
    
def get_child_group(item_group):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1, 'show_in_website': 1},
        fields=['name'])
    for s in sub_groups:
        sg = {}
        sg[s['name']] = get_child_group(s['name'])
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0, 'show_in_website': 1},
        fields=['name'])
    for n in nodes:
        groups.append(n['name'])
    return groups
