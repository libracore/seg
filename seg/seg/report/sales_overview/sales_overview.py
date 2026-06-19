# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import cint
from frappe.utils.pdf import get_pdf

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Item Group Priority"), "fieldname": "item_group_prio", "fieldtype": "Int", "width": 50},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 130},
        {"label": _("Net Turnover"), "fieldname": "net_turnover", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Purchase Price"), "fieldname": "total_purchase", "fieldtype": "Currency", "width": 130},
        {"label": _("DB on Purchase Price CHF"), "fieldname": "db_purchase_price_chf", "fieldtype": "Currency", "width": 130},
        {"label": _("DB on Purchase Price %"), "fieldname": "db_purchase_price", "fieldtype": "Percent", "width": 130},
        {"label": _("Total SEG Purchase Price"), "fieldname": "total_seg_purchase", "fieldtype": "Currency", "width": 130},
        {"label": _("DB on SEG Purchase Price CHF"), "fieldname": "db_seg_price_chf", "fieldtype": "Currency", "width": 130},
        {"label": _("DB on SEG Purchase Price %"), "fieldname": "db_seg_price", "fieldtype": "Percent", "width": 130}
    ]
    return columns

def get_data(filters):
    #Prepare Employee condition
    if filters.get('employee'):
        employee_condition = """AND `tabSales Team`.`sales_person` = '{0}'""".format(filters.get('employee'))
    else:
        employee_condition = """"""
    
    #Get Item Groups
    if filters.get('item_group'):
        main_group = filters.get('item_group')
    else:
        main_group = "Alle Artikelgruppen"
    
    display_groups = get_display_groups(main_group, filters.get('depth')[4:] if filters.get('depth') else filters.get('depth'))
    
    #Collect Data
    datas = []
    for dp in display_groups:
        item_groups = [dp]
        item_groups = get_child_groups(dp, item_groups)
        
        data = frappe.db.sql("""
                                SELECT 
                                    %(item_group)s AS `item_group`,
                                    SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100)) AS `net_turnover`,
                                    SUM(`tabDelivery Note Item`.`qty` * IFNULL(`tabStock Ledger Entry`.`valuation_rate`, `tabItem`.`last_purchase_rate`)) AS `total_purchase`,
                                    (SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) - (SUM(`tabDelivery Note Item`.`qty` * IFNULL(`tabStock Ledger Entry`.`valuation_rate`, `tabItem`.`last_purchase_rate`))) AS `db_purchase_price_chf`,
                                    ((SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) - (SUM(`tabDelivery Note Item`.`qty` * IFNULL(`tabStock Ledger Entry`.`valuation_rate`, `tabItem`.`last_purchase_rate`)))) * 100 / (SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) AS `db_purchase_price`,
                                    SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`) AS `total_seg_purchase`,
                                    (SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) - SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`) AS `db_seg_price_chf`,
                                    ((SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) - SUM(`tabDelivery Note Item`.`qty` * `tabItem`.`seg_purchase_price`)) * 100 / (SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100))) AS `db_seg_price`
                                FROM
                                    `tabDelivery Note Item`
                                LEFT JOIN
                                    `tabItem` ON `tabItem`.`item_code` = `tabDelivery Note Item`.`item_code`
                                LEFT JOIN   
                                    `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
                                LEFT JOIN
                                    `tabSales Team` ON `tabDelivery Note`.`customer` = `tabSales Team`.`parent`
                                LEFT JOIN
                                    `tabCustomer` ON `tabDelivery Note`.`customer` = `tabCustomer`.`name`
                                LEFT JOIN
                                    `tabStock Ledger Entry` ON `tabStock Ledger Entry`.`voucher_no` = `tabDelivery Note`.`name` 
                                AND
                                    `tabStock Ledger Entry`.`voucher_detail_no` = `tabDelivery Note Item`.`name`
                                WHERE
                                    `tabDelivery Note`.`docstatus` = 1
                                AND
                                    `tabDelivery Note`.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
                                AND
                                    `tabItem`.`item_group` IN %(item_groups)s
                                {employee_condition}
                                ;""".format(employee_condition=employee_condition), {'item_group': dp, 'from_date': filters.get('from_date'), 'to_date': filters.get('to_date'), 'item_groups': tuple(item_groups), 'employee_condition': employee_condition}, as_dict=True)
        
        #Add Item Group Prio
        data[0]['item_group_prio'] = cint(frappe.get_value("Item Group", dp, "item_group_priority"))
        
        if len(data) > 0:
            datas.append(data[0])
    
    return datas

def get_display_groups(main_group, depth):
    #Get all group types to be displayed
    depth_sort = ["Product Category", "Product Subcategory", "Product Group", "Item Group"]
    display_types = []
    for g in depth_sort:
        display_types.append(g)
        if g == depth:
            break
    
    display_groups = [main_group]
    display_groups = get_child_display_groups(main_group, display_types, display_groups)
    
    return display_groups

def get_child_display_groups(item_group, display_types, display_groups):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for s in sub_groups:
        if s['item_group_type'] in display_types:
            display_groups.append(s['name'])
        sg = {}
        sg[s['name']] = get_child_display_groups(s['name'], display_types, display_groups)
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for n in nodes:
        if n['item_group_type'] in display_types:
            display_groups.append(n['name'])
    return display_groups

def get_child_groups(item_group, item_groups):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for s in sub_groups:
        item_groups.append(s['name'])
        sg = {}
        sg[s['name']] = get_child_groups(s['name'], item_groups)
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0},
        order_by='weightage desc',
        fields=['name', 'item_group_type'])
    for n in nodes:
        item_groups.append(n['name'])
    return item_groups

@frappe.whitelist()
def send_report():
    filters = {'from_date': '2026-01-01', 'to_date': '2026-06-18', 'employee': 'Christian Aeschlimann', 'depth': '3 - Product Subcategory'}
    data = get_data(filters)
    header_data = {'actual_date': "23.06.2026", 'from_date': "01.01.2025", 'to_date': "31.01.2025", 'actual_year': 2026, 'previous_year': 2025}
    overview_html = frappe.render_template("seg/seg/report/sales_overview/sales_overview.html", {'data': data, 'header_data': header_data})
    rendered_html = frappe.render_template("seg/templates/pages/print.html", {'html': overview_html})
    pdf = get_pdf(rendered_html, options={"orientation": "Landscape"})
    # ~ frappe.local.response.filename = "overview.pdf"
    # ~ frappe.local.response.filecontent = pdf
    # ~ frappe.local.response.type = "download"
    
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": "overview.pdf",
        "content": pdf,
        "is_private": 1
    })
    file_doc.save(ignore_permissions=True)

    return file_doc.file_url
    
# ~ def get_physical_path(file_name):
    # ~ base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])

    # ~ return "{0}private/files/{1}".format(base_path, file_name)

