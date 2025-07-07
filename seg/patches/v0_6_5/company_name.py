import frappe
from frappe import _

def execute():
    frappe.reload_doc("Contacts", "doctype", "Contact")
    
    contacts = frappe.db.sql("""SELECT
                                        `tabContact`.`name`
                                    FROM
                                        `tabContact`
                                    INNER JOIN
                                        `tabDynamic Link` ON `tabContact`.`name` = `tabDynamic Link`.`parent`""", as_dict=True)
    
    for contact in contacts:
        contact_doc = frappe.get_doc("Contact", contact.get('name'))
        
        for link in contact_doc.links:
            link.link_title = frappe.get_value(link.get('link_doctype'), link.get('link_name'), "{0}_name".format(link.get('link_doctype').lower()))
            
        contact_doc.company_name = contact_doc.links[0].get('link_title')
        try:
            contact_doc.save()
        except Exception as err:
            frappe.log_error(err, "Contact Patch Error")
    
    frappe.db.commit()
    return
