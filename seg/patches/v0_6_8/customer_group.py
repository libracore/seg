import frappe
from frappe import _

def execute():
    frappe.reload_doc("ERPNextSwiss", "doctype", "Payment Reminder")
    
    payment_reminder = frappe.db.sql("""
                                SELECT
                                    `tabPayment Reminder`.`name` AS `name`,
                                    `tabCustomer`.`customer_group` AS `customer_group`
                                FROM
                                    `tabPayment Reminder`
                                LEFT JOIN
                                    `tabCustomer` ON `tabCustomer`.`name` = `tabPayment Reminder`.`customer` """, as_dict=True)
    
    for reminder in payment_reminder:
        cust_group = frappe.db.set_value("Payment Reminder", reminder.get('name'), "customer_group", reminder.get('customer_group'))
    
    frappe.db.commit()
    return
