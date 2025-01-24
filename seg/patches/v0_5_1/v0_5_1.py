import frappe

def execute():
    frappe.reload_doc("Setup", "doctype", "UOM")
    uom_errors = []
    conversion_errors = []
    
    #get uoms without french translation
    uoms = frappe.db.sql("""
                            SELECT
                                `name`
                            FROM
                                `tabUOM`
                            WHERE
                                `uom_name_fr` IS NULL""", as_dict=True)
                                
    for uom in uoms:
        #get all conversions for each uom
        conversions = frappe.db.sql("""
                                    SELECT
                                        `name`
                                    FROM
                                        `tabUOM Conversion Factor`
                                    WHERE
                                        `from_uom` = '{uom}'
                                    OR
                                        `to_uom` = '{uom}'""".format(uom=uom.get('name')), as_dict=True)
        
        #if conversions available
        if len(conversions) > 0:
            for conversion in conversions:
                try:
                    frappe.delete_doc("UOM Conversion Factor", conversion.get('name'))
                except Exception as e:
                    conversion_errors.append("{0}".format(e))
                    
        try:
            frappe.delete_doc("UOM", uom.get('name'))
        except Exception as err:
            uom_errors.append("{0}".format(err))
    
    frappe.db.commit()
    frappe.log_error(uom_errors, "uom_errors")
    frappe.log_error(conversion_errors, "conversion_errors")
    return
