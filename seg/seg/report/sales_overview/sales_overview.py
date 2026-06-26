# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import cint
from frappe.utils.pdf import get_pdf
from frappe.utils import add_days, getdate, formatdate, add_years

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
    #get header and filter data
    today = frappe.utils.data.today()
    monday = add_days(today, -4)
    actual_year = getdate(today).year
    last_year = actual_year - 1
    
    #Collect header data
    header_data = {'actual_date': formatdate(today, "dd.MM.yyyy"), 'from_date': formatdate(monday, "dd.MM.yyyy"), 'to_date': formatdate(today, "dd.MM.yyyy"), 'actual_year': actual_year, 'previous_year': last_year}
    filter_data = {'actual_date': today, 'from_date': monday, 'to_date': today, 'actual_year': actual_year, 'previous_year': last_year, 'depth': '3 - Product Subcategory'}
    
    #Create PDF for Company
    overview = create_pdf(header_data, None)
    
    #Create and send PDF for each Employee
    sales_persons = frappe.get_list("Sales Person", filters={'enabled': 1}, fields=["name", "employee"])
    for sales_person in sales_persons:
        specific_overview = create_pdf(header_data, sales_person.get('name'))
        
        #Get User E-Mail
        
        #Send E-Mail with Overview for User and Company

def create_pdf(header_data, employee):
    #Get Item Groups
    display_groups = get_display_groups("Alle Artikelgruppen", header_data.get('depth'))
    
    #Get all data for each Item Group
    master_data = []
    for item_group in display_groups:
        item_group_data = get_item_group_data(header_data, item_group, employee)
        master_data.append(item_group_data)
    
    
    overview_html = frappe.render_template("seg/seg/report/sales_overview/sales_overview.html", {'data': master_data, 'header_data': header_data})
    rendered_html = frappe.render_template("seg/templates/pages/print.html", {'html': overview_html})
    pdf = get_pdf(rendered_html, options={"orientation": "Landscape"})
    # ~ frappe.local.response.filename = "overview.pdf"
    # ~ frappe.local.response.filecontent = pdf
    # ~ frappe.local.response.type = "download"
    
    if not employee:
        file_name = "sales_overview_seg.pdf"
    else:
        person = map_employee(employee)
        file_name = "sales_overview_{0}.pdf".format(person)
    
    #Check if File ist already existing, replace it, otherwise create e new one
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
    
def get_item_group_data(header_data, item_group, employee)
    #Prepare Employee condition
    if employee:
        employee_condition = """AND `tabSales Team`.`sales_person` = '{0}'""".format(employee)
    else:
        employee_condition = """"""
    
    item_groups = [item_group]
    item_groups = get_child_groups(item_group, item_groups)
    
    #Collect Item Group, Priority, Net Turnover for current Week, DB for Current Week
    main_data = get_pdf_data(header_data.get('from_date'), header_data.get('to_date'), item_group, item_groups, employee_condition)
    
    #Collect Year To Date Data
    first_day_of_year = "{0}-01-01".format(header_data.get('actual_year'))
    year_to_date = get_pdf_data(first_day_of_year, header_data.get('to_date'), item_group, item_groups, employee_condition)
    
    #Collect Year To Date Data from Last Year
    first_day_previous_year = "{0}-01-01".format(header_data.get('previous_year'))
    today_previous_year = add_years(header_data.get('to_date'), -1)
    prev_year_to_date = get_pdf_data(first_day_previous_year, today_previous_year, item_group, item_groups, employee_condition)
    
    #Collect weekly average
    # ~ weeks = header_data.get('to_date').isocalendar().week
    # ~ weekly_average = 
    # ~ weekly_average_prev_year = 
    
    #Prepare complete data for Item Group
    return_data = {
                    'item_group_prio': main_data.get('item_group_prio'),
                    'item_group': main_data.get('item_group'),
                    'net_turnover': main_data.get('net_turnover'),
                    'db_seg_price': main_data.get('db_seg_price'),
                    'net_year_to_date': year_to_date.get('net_turnover'),
                    'db_year_to_date': year_to_date.get('db_seg_price'),
                    'net_year_to_date_last': prev_year_to_date.get('net_turnover'),
                    'db_year_to_date_last': prev_year_to_date.get('db_seg_price'),
                    'net_week_average': 0,
                    'net_week_average_last': 0
                }
    
    return return_data

def get_pdf_data(from_date, to_date, item_group, item_groups, employee_condition):
    data = frappe.db.sql("""
                            SELECT 
                                %(item_group)s AS `item_group`,
                                SUM((`tabDelivery Note Item`.`net_amount`) * ((100 - `tabCustomer`.`rueckverguetung`) / 100)) AS `net_turnover`,
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
                            ;""".format(employee_condition=employee_condition), {'item_group': item_group, 'from_date': from_date, 'to_date': to_date, 'item_groups': tuple(item_groups)}, as_dict=True)
    
    #Add Item Group Prio
    data[0]['item_group_prio'] = cint(frappe.get_value("Item Group", dp, "item_group_priority"))
    
    return data
