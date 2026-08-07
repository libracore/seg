# Copyright (c) 2017-2026, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
from seg.seg.purchasing import get_updated_seg_prices

@frappe.whitelist()
def get_entry_warehouse_items():
    #Get Entry Warehouse
    entry_warehouse = get_entry_warehouse()
    
    #Get all Items in Entry Warehouse
    items = frappe.get_all("Bin", filters={'warehouse': entry_warehouse,  'actual_qty': [">", 0]}, fields=["item_code", "actual_qty"])
    frappe.log_error("items", items)
    #Prepare response
    if len(items) > 0:
        response = []
        for item in items:
            #Get Item Doc
            item_doc = frappe.get_doc("Item", item.get('item_code'))
            
            #Add Information for this item to response
            item_response = {
                        'item_code': item.get('item_code'),
                        'picture': item_doc.get('image') or "",
                        'content': {
                            'qty': item.get('actual_qty'),
                            'item_name': item_doc.get('item_name'),
                            'locations': get_item_locations(item.get('item_code')),
                            'stored_qty': 0
                        }}
        
            response.append(item_response)
    else:
        response = None
    
    return response

def get_item_locations(item_code):
    #Get all Item Locations
    warehouses = frappe.get_all("Bin", filters={"item_code": item_code}, fields=["warehouse", "actual_qty"])
    
    #Return Information String
    if len(warehouses) > 0:
        wh_info = ""
        for index, wh in enumerate(warehouses):
            if index == 0:
                wh_info += "{0}({1})".format(wh.get('warehouse'), cint(wh.get('actual_qty')))
            else:
                wh_info += ", {0}({1})".format(wh.get('warehouse'), cint(wh.get('actual_qty')))
    else:
        wh_info = None
    
    return wh_info

@frappe.whitelist()
def get_single_item_information(item):
    #Get Entry Warehouse
    entry_warehouse = get_entry_warehouse()
    frappe.log_error("entry_warehouse", entry_warehouse)
    item_information = frappe.db.sql("""
                                    SELECT
                                        `tabItem`.`item_code` AS `item_code`,
                                        `tabItem`.`item_name` AS `item_name`,
                                        `tabItem`.`image` AS `image`,
                                        `tabBin`.`actual_qty` AS `qty_on_entry_wh`
                                    FROM
                                        `tabItem`
                                    LEFT JOIN
                                        `tabBin` ON `tabItem`.`item_code` = `tabBin`.`item_code`
                                    WHERE
                                        `tabItem`.`item_code` = %(item)s
                                    AND
                                        `tabBin`.`warehouse` = %(warehouse)s;""", {'item': item, 'warehouse': entry_warehouse}, as_dict=True)
    if len(item_information) > 0:
        frappe.log_error("item_information", item_information)
        response = [{
                    'item_code': item_information[0].get('item_code'),
                    'picture': item_information[0].get('image') or "",
                    'content': {
                        'qty_on_entry_wh': item_information[0].get('qty_on_entry_wh'),
                        'item_name': item_information[0].get('item_name'),
                        'locations': get_item_locations(item_information[0].get('item_code'))
                    }}]
        frappe.log_error("Item Information", response)
        return response
    return None

def get_entry_warehouse():
    entry_warehouse = frappe.db.get_single_value("SEG Settings", "entry_warehouse")
    return entry_warehouse

@frappe.whitelist()
def get_warehouse_overview(item):
    #Get all Warehouses for specific Item
    item_warehouses = get_item_warehouse(item)
    
    #Get all Free Warehouses
    free_warehouses = get_free_warehouse()
    
    #return dict with all warehouses
    warehouse_dict = {'item_warehouses': item_warehouses, 'free_warehouses': free_warehouses}
    frappe.log_error("warehouse_dict", warehouse_dict)
    return warehouse_dict
    
def get_item_warehouse(item):
    warehouses = frappe.db.sql("""
                                SELECT
                                    `tabBin`.`item_code` AS `item_code`,
                                    `tabBin`.`warehouse`,
                                    `tabWarehouse`.`warehouse_type`
                                    
                                FROM
                                    `tabBin`
                                LEFT JOIN
                                    `tabWarehouse` ON `tabWarehouse`.`name` = `tabBin`.`warehouse`
                                WHERE
                                    `item_code` = %(item)s
                                AND
                                    `actual_qty` > 0;""", {'item': item}, as_dict=True)
    
    return warehouses

def get_free_warehouse():
    warehouses = frappe.db.sql("""
                                SELECT
                                    `tabWarehouse`.`name` AS `warehouse`,
                                    `tabWarehouse`.`warehouse_type` AS `warehouse_type`,
                                    IFNULL(
                                        (
                                            SELECT SUM(`actual_qty`)
                                            FROM `tabBin`
                                            WHERE `tabBin`.`warehouse` = `tabWarehouse`.`name`
                                        ),
                                        0
                                    ) AS `total`
                                FROM
                                    `tabWarehouse`
                                WHERE
                                    `disabled` = 0;
                            """, as_dict=True)
    empty_wh = []
    if len(warehouses) > 0:
        for wh in warehouses:
            if not wh.get('total') or wh.get('total') < 1:
                empty_wh.append(wh)
    
    return empty_wh

#Create Stock Entries from "Eingangslager"
@frappe.whitelist()
def create_enter_stock_entry(item, target_warehouse, qty):
    #Check Parameter
    if not frappe.db.exists("Item", item):
        return {'success': False, 'error': "Artikel existiert nicht."}
    
    if not frappe.db.exists("Warehouse", target_warehouse):
        return {'success': False, 'error': "Lagerplatz existiert nicht."}
    
    #Get Sorce Warehouse (Eingangslager)
    source_warehouse = get_entry_warehouse()
    
    stock_entry = create_stock_entry("Material Transfer", item, qty, source_warehouse, target_warehouse)
    
    return {'success': True, 'error': None}
    
def create_stock_entry(entry_type, item, qty, source_warehouse=None, target_warehouse=None):
    stock_entry = frappe.new_doc("Stock Entry")

    stock_entry.stock_entry_type = entry_type

    stock_entry.append("items", {
        'item_code': item,
        'qty': qty,
        's_warehouse': source_warehouse,
        't_warehouse': target_warehouse
    })
    
    try:
        stock_entry.insert()
        stock_entry.submit()
        return stock_entry.name
    except Exception as Err:
        frappe.log_error("Stock Entry Issue", "Error in Stock Entry from Stock Management App: {0}".format(Err))
        frappe.throw("Es ist ein Fehler beim erstellen der Lagerbuchung aufgetreten, Material wurde nicht umgebucht. Es wurde ein Fehlerbericht erstellt.")

#Get Open Orders for Purchase Receipt
@frappe.whitelist()
def get_open_orders(supplier, order):
    #Prepare condition
    supplier_condition = """"""
    if supplier:
        supplier_condition = """AND `supplier` = '{0}'""".format(supplier)
    
    order_condition = """"""
    if order:
        order_condition = """AND `name` = '{0}'""".format(order)
    
    #Get orders
    open_orders = frappe.db.sql("""
                                SELECT
                                    `name`,
                                    DATE_FORMAT(transaction_date, '%d.%m.%Y') AS `transaction_date`,
                                    DATE_FORMAT(schedule_date, '%d.%m.%Y') AS `formatted_schedule_date`,
                                    `supplier`
                                FROM
                                    `tabPurchase Order`
                                WHERE
                                    `per_received` < 100
                                AND
                                    `docstatus` = 1
                                AND
                                    `status` != 'Closed'
                                {supplier_condition}
                                {order_condition}
                                ORDER BY
                                    `schedule_date` ASC;""".format(supplier_condition=supplier_condition, order_condition=order_condition), as_dict=True)
    
    return open_orders

#Get Items from Open Order
@frappe.whitelist()
def get_order_items(order):
    frappe.log_error("order", order)
    items = frappe.db.sql("""
                            SELECT
                                `tabPurchase Order Item`.`item_code` AS `item_code`,
                                `tabPurchase Order Item`.`item_name` AS `item_name`,
                                (`tabPurchase Order Item`.`qty` - `tabPurchase Order Item`.`received_qty`) AS `qty`,
                                `tabItem`.`image` AS `image`
                            FROM
                                `tabPurchase Order Item`
                            LEFT JOIN
                                `tabItem` ON `tabItem`.`name` = `tabPurchase Order Item`.`item_code`
                            WHERE
                                `tabPurchase Order Item`.`parent` = %(po)s;""", {'po': order}, as_dict=True)
    frappe.log_error("items", items)
        #Prepare response
    if len(items) > 0:
        response = []
        for item in items:
            #Add Information for this item to response
            if item.get('qty') > 0:
                item_response = {
                            'item_code': item.get('item_code'),
                            'picture': item.get('image') or "",
                            'content': {
                                'qty': item.get('qty'),
                                'item_name': item.get('item_name'),
                                'locations': get_item_locations(item.get('item_code')),
                                'stored_qty': 0
                            }}
                
                response.append(item_response)
    else:
        response = None
    
    return response
    
    return items

@frappe.whitelist()
def store_everything(order):
    purchase_receipt = make_purchase_receipt(order)
    # ~ get_updated_seg_prices ->
