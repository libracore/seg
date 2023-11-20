# Copyright (c) 2017-2023, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

# customisation for total weight calculation
import frappe
import json
import six
from erpnext.portal.product_configurator.utils import get_next_attribute_and_values
from seg.seg.doctype.sales_report.sales_report import update_last_purchase_rates
from datetime import datetime

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
    
