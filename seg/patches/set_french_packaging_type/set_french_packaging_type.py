import frappe

def execute():
    frappe.reload_doc("seg", "doctype", "Item")
    success = True
    errors = []
    items = frappe.db.sql("""
                            SELECT
                                `name`
                            FROM
                                `tabItem`""", as_dict=True)
    
    for item in items:
        try:
            item_doc = frappe.get_doc("Item", item.get('name'))
            if item_doc.packaging_type == "Karton":
                frappe.db.set_value("Item", item.get('name'), "packaging_type_fr", "Carton")
            elif item_doc.packaging_type == "Palette":
                frappe.db.set_value("Item", item.get('name'), "packaging_type_fr", "Palette")
        except Exception as Err:
            success = False
            errors.append([item.get('name'), str(Err)])
            pass
    
    if not success:
        frappe.log_error(errors, "Packaging type errors")
        
    return
