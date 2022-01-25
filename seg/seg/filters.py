# Copyright (c) 2021-2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for supplier
def get_alternative_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabItem Alternative`.`item_code`, `tabItem Alternative`.`item_name`
           FROM `tabItem Alternative`
           WHERE `tabItem Alternative`.`alternative_item_code` = "{i}" AND 
             (`tabItem Alternative`.`item_name` LIKE "%{s}%"
              OR `tabItem Alternative`.`item_code` LIKE "%{s}%");
        """.format(i=filters['item_code'], s=txt))
