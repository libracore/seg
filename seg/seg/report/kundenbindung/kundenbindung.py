# Copyright (c) 2020-2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextswiss.scripts.crm_tools import get_primary_customer_contact

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)

    return columns, data
    
def get_columns():
    return [

      
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        #{"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 130},
        {"label": _("Customer"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 120},
        {"label": _("Letzte Lieferung"), "fieldname": "delivery_date", "fieldtype": "Date", "width": 100},
        {"label": _("Umsatz PY"), "fieldname": "revenue_py", "fieldtype": "Curreny", "width": 100},
        {"label": _("Umsatz YTD"), "fieldname": "revenue_ytd", "fieldtype": "Currency", "width": 100},
        {"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 100},
        {"label": _("Phone"), "fieldname": "phone", "fieldtype": "Data", "width": 100},
        {"label": _("First name"), "fieldname": "first_name", "fieldtype": "Data", "width": 100},
        {"label": _("Last name"), "fieldname": "last_name", "fieldtype": "Data", "width": 100},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def has_role(user, role):
    sql_query = """SELECT `role` FROM `tabHas Role` WHERE `parent` = '{user}' AND `parenttype` = "User" AND `role` = '{role}';""".format(role=role, user=user)
    data = frappe.db.sql(sql_query, as_dict=True)
    if len(data) > 0:
        return True
    else:
        return False

def get_data(filters):
    if not has_role(frappe.session.user, "Sales Manager"):
        restriction = " WHERE `tabCustomer`.`owner` = '{0}'".format(frappe.session.user)
    else:
        restriction = ""
    conditions = ""
    if filters.customer_group:
        conditions += """ AND `raw`.`customer_group` = "{customer_group}" """.format(customer_group=filters.customer_group)
        
    sql_query = """
        SELECT 
          `customer` AS `customer`,
          `customer_group` AS `customer_group`,
          /*`first_name` AS `first_name`,
          `last_name` AS `last_name`,
          `email` AS `email`, */
          `delivery_date` AS `delivery_date`,
          `revenue_py` AS `revenue_py`,
          `revenue_ytd` AS `revenue_ytd`
        FROM 
        (SELECT 
          `tabCustomer`.`name` AS `customer`,
          `tabCustomer`.`customer_group` AS `customer_group`,
          /* `tabContact`.`first_name` AS `first_name`, 
          `tabContact`.`last_name` AS `last_name`, 
          `tabContact`.`email_id` AS `email`, */
          (SELECT MAX(`posting_date`) 
           FROM `tabDelivery Note` 
           WHERE `tabDelivery Note`.`customer` = `tabCustomer`.`name` 
             AND `tabDelivery Note`.`docstatus` = 1) AS `delivery_date`,
          (SELECT SUM(`base_net_total`) 
           FROM `tabSales Invoice` 
           WHERE `tabSales Invoice`.`customer` = `tabCustomer`.`name` 
             AND `tabSales Invoice`.`docstatus` = 1
             AND `tabSales Invoice`.`posting_date` >= CONCAT((YEAR(CURDATE()) - 1), "-01-01")
             AND `tabSales Invoice`.`posting_date` <= CONCAT((YEAR(CURDATE()) - 1), "-12-31")) AS `revenue_py`,
          (SELECT SUM(`base_net_total`) 
           FROM `tabSales Invoice` 
           WHERE `tabSales Invoice`.`customer` = `tabCustomer`.`name` 
             AND `tabSales Invoice`.`docstatus` = 1
             AND `tabSales Invoice`.`posting_date` >= CONCAT(YEAR(CURDATE()), "-01-01")
             AND `tabSales Invoice`.`posting_date` <= CONCAT(YEAR(CURDATE()), "-12-31")) AS `revenue_ytd`
         FROM `tabCustomer`
         /* LEFT JOIN `tabDynamic Link` ON (`tabDynamic Link`.`link_name` = `tabCustomer`.`name` AND `tabDynamic Link`.`parenttype` = "Contact")
         LEFT JOIN `tabContact` ON `tabContact`.`name` = `tabDynamic Link`.`parent` */
         {restriction}
         GROUP BY `tabCustomer`.`name`) AS `raw`
        WHERE 
            `raw`.`delivery_date` IS NOT NULL
            {conditions}
        ORDER BY `raw`.`delivery_date` DESC;
      """.format(restriction=restriction, conditions=conditions)

    data = frappe.db.sql(sql_query, as_dict=1)

    # fetch primary contact
    for d in data:
        contact = get_primary_customer_contact(d.get("customer"))
        d['phone'] = contact.phone
        d['email'] = contact.email_id
        d['first_name'] = contact.first_name
        d['last_name'] = contact.last_name
        
    return data
