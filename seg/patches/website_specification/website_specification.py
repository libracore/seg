import frappe

def execute():
    frappe.db.sql("""INSERT INTO `tabItem Custom Website Specification`
                        (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `custom_label`, `custom_description`, `custom_label_fr`, `custom_description_fr`)
                        SELECT `name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `label`, `description`, `label_fr`, `description_fr` FROM `tabItem Website Specification`;""")
