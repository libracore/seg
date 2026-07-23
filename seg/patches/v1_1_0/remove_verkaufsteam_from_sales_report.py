import frappe

def execute():
    frappe.db.set_value("Sales Person", "Verkaufsteam", "no_sales_report", 1)
    frappe.db.commit()
