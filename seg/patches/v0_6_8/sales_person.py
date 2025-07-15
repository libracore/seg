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
        sales_person = frappe.get_value("Customer", reminder.get('customer'), "customer_group")
        sal_per = frappe.db.set_value("Payment Reminder", reminder.get('name'), "sales_person", sales_person)
    
    frappe.db.commit()
    return
