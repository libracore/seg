import frappe
from frappe import _

def execute():
    frappe.reload_doc("ERPNextSwiss", "doctype", "Payment Reminder")
    
    payment_reminder = frappe.db.sql("""
                                SELECT
                                    `name`,
                                    `customer`
                                FROM
                                    `tabPayment Reminder`""", as_dict=True)
    
    for reminder in payment_reminder:
        customer_group = frappe.get_value("Customer", reminder.get('customer'), "customer_group")
        cust_group = frappe.db.set_value("Payment Reminder", reminder.get('name'), "customer_group", customer_group)
    
    frappe.db.commit()
    return
