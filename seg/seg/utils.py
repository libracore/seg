# Copyright (c) 2017-2023, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

# customisation for total weight calculation
import frappe
import json
import six
from erpnext.portal.product_configurator.utils import get_next_attribute_and_values
from seg.seg.doctype.sales_report.sales_report import update_last_purchase_rates
from datetime import datetime
from frappe.utils import cint

naming_patterns = {
    'Address': {
        'prefix': "A-",
        'length': 5
    },
    'Contact': {
        'prefix': "C-",
        'length': 5
    }
}

@frappe.whitelist()
def get_total_weight(items, qtys, kgperL=1.5):
    total_weight = 0
    if isinstance(items, six.string_types):
        items = json.loads(items)
    if isinstance(qtys, six.string_types):
        qtys = json.loads(qtys)
    i = 0
    while i < len(items):
        doc = frappe.get_doc("Item", items[i])
        if doc != None:
            if doc.weight_per_unit > 0 and doc.has_weight:
                if doc.weight_uom == "kg":
                    total_weight += qtys[i] * doc.weight_per_unit
                elif doc.weight_uom == "L":
                    # make sure, tabItem contains custom field (float) density!
                    total_weight += qtys[i] * doc.density * doc.weight_per_unit
        i += 1
    return { 'total_weight': total_weight }

@frappe.whitelist()
def convert_material(source_item, target_item, warehouse, qty):
    issue = create_stock_entry("Material Issue", [{'item_code': source_item}], warehouse, qty)
    base_rate = issue.items[0].basic_rate
    create_stock_entry("Material Receipt", [{'item_code': target_item}], warehouse, qty, base_rate)
    return
    
def create_stock_entry(stock_entry_type, items, warehouse, qty, base_rate=None):
    doc = frappe.get_doc({
        'doctype': "Stock Entry",
        'stock_entry_type': stock_entry_type,
        'to_warehouse': warehouse,
        'from_warehouse': warehouse
    })
    for i in items:
        doc.append('items', {
            'item_code': i['item_code'],
            'qty': qty,
            'basic_rate': base_rate
        })
    doc = doc.insert()
    doc.submit()
    if stock_entry_type == "Material Receipt":
        update_last_purchase_rates(doc.name)
    return doc

def convert_credits_to_advances():
    invoices_with_credits = frappe.get_all("Sales Invoice",
        filters=[['outstanding_amount', '<', 0], ['docstatus', '=', 1]],
        fields=['name']
    )
    
    for invoice in invoices_with_credits:
        transfer_credit(invoice.get("name"))
        
    return
    
def transfer_credit(sales_invoice_name):
    sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
    outstanding_amount = (-1) * sales_invoice.outstanding_amount
    if outstanding_amount <= 0:
        return
    
    debit_account = sales_invoice.debit_to
    jv = frappe.get_doc({
        'doctype': "Journal Entry",
        'posting_date': datetime.now(),
        'accounts': [
            {
                'account': debit_account,
                'party_type': "Customer",
                'party': sales_invoice.customer,
                'debit_in_account_currency': outstanding_amount,
                'reference_type': "Sales Invoice",
                'reference_name': sales_invoice_name
            },
            {
                'account': debit_account,
                'party_type': "Customer",
                'party': sales_invoice.customer,
                'credit_in_account_currency': outstanding_amount,
                'is_advance': "Yes"
            }
        ],
        'user_remarks': "Umbuchung von {0}".format(sales_invoice_name),
        'company': sales_invoice.company
    })
    jv.insert()
    jv.submit()
    frappe.db.commit()
    
def object_autoname(self, method):
    if self.doctype not in ["Address", "Contact"]:
        frappe.throw("Custom autoname is not implemented for this doctype.", "Not implemented")
        
    self.name = get_next_number(self)
    return
    
def get_next_number(self):
    if self.doctype not in ["Address", "Contact"]:
        frappe.throw("Custom autoname is not implemented for this doctype.", "Not implemented")
    
    last_name = frappe.db.sql("""
        SELECT `name`
        FROM `tab{dt}`
        WHERE `name` LIKE "{prefix}%"
        ORDER BY `name` DESC
        LIMIT 1;""".format(
        dt=self.doctype, 
        prefix=naming_patterns[self.doctype]['prefix']),
        as_dict=True)
    
    if len(last_name) == 0:
        next_number = 1
    else:
        prefix_length = len(naming_patterns[self.doctype]['prefix'])
        last_number = cint((last_name[0]['name'])[prefix_length:])
        next_number = last_number + 1
    
    next_number_string = "{0}{1}".format(
        (naming_patterns[self.doctype]['length'] * "0"),
        next_number)[((-1)*naming_patterns[self.doctype]['length']):]
    # prevent duplicates on naming series overload
    if next_number > cint(next_number_string):
        next_number_string = "{0}".format(next_number)
        
    return "{prefix}{n}".format(prefix=naming_patterns[self.doctype]['prefix'], n=next_number_string)

@frappe.whitelist()
def check_dn_discount(delivery_note):
    data = frappe.db.sql("""
                            SELECT `discount_amount`
                            FROM `tabDelivery Note`
                            WHERE `name` = '{dn}'""".format(dn=delivery_note), as_dict=True)
    
    if len(data) > 0:
        discount = data[0]['discount_amount']
        if discount > 0:
            return discount
        else:
            return False
    else:
        return False
        
@frappe.whitelist()
def check_for_lsva(customer):
    data = frappe.db.sql("""
                            SELECT `always_pick_up`
                            FROM `tabCustomer`
                            WHERE `name` = '{c}'""".format(c=customer), as_dict=True)
    
    pick_up = False
    if len(data) > 0 and data[0]['always_pick_up'] == 1:
        pick_up = True

    return pick_up
    
@frappe.whitelist()
def check_cash_discount(customer):
    cash_discount = False
    #get customer doc
    customer_doc = frappe.get_doc("Customer", customer)
    #check for skonto
    if customer_doc.has_cash_discount == 1:
        cash_discount = customer_doc.cash_discount
    #return skonto or False(if there is no skonto)
    return cash_discount
    
@frappe.whitelist()
def get_email_recipient_and_message(customer, doctype):
    recipient = frappe.db.get_value("Customer", customer, "preferred_invoice_email")

    html = frappe.db.get_value("Email Template", doctype, "response")
    
    return {
        'recipient': recipient,
        'message': html
        }
        
def create_journal_entry(self, event):
    if self.currency == "CHF" and not self.payment_method == "Rechnung":
        if event == "on_cancel":
            if self.autocreated_journal_entry:
                journal_entry = frappe.get_doc("Journal Entry", self.autocreated_journal_entry)
                journal_entry.cancel()
        else:
            suspense_account = frappe.db.sql("""
                                                SELECT
                                                    `default_account`
                                                FROM
                                                    `tabMode of Payment Account`
                                                WHERE
                                                    `parent` = '{payment_method}'""".format(payment_method=self.payment_method), as_dict=True)
            if len(suspense_account) > 0:
                journal_entry = frappe.get_doc({
                                                'doctype': "Journal Entry",
                                                'voucher_type': "Journal Entry",
                                                'posting_date': self.posting_date,
                                                'user_remark': "Diese Buchung wurde automatisch aus Rechnung {0} erstellt".format(self.name),
                                                'mode_of_payment': self.payment_method})
                                                
                journal_entry.append("accounts", {
                                                    'reference_doctype': "Journal Entry Account",
                                                    'account': self.debit_to,
                                                    'party_type': "Customer",
                                                    'party': self.customer,
                                                    'credit_in_account_currency': self.outstanding_amount,
                                                    'reference_type': "Sales Invoice",
                                                    'reference_name': self.name
                                                })
                                                
                journal_entry.append("accounts", {
                                                    'reference_doctype': "Journal Entry Account",
                                                    'account': suspense_account[0].get('default_account'),
                                                    'debit_in_account_currency': self.outstanding_amount
                                                })
                journal_entry.insert()
                journal_entry.submit()
                frappe.db.set_value("Sales Invoice", self.name, "autocreated_journal_entry", journal_entry.name)
                frappe.db.commit()
                return
            else:
                return
