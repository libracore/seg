# Copyright (c) 2017-2026, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint, flt, sbool, getdate
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
from erpnext.setup.utils import get_exchange_rate
import json
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

@frappe.whitelist()
def get_entry_warehouse_items():
    #Get Entry Warehouse
    entry_warehouse = get_entry_warehouse()
    
    #Get all Items in Entry Warehouse
    items = frappe.get_all("Bin", filters={'warehouse': entry_warehouse,  'actual_qty': [">", 0]}, fields=["item_code", "actual_qty"])
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
        response = [{
                    'item_code': item_information[0].get('item_code'),
                    'picture': item_information[0].get('image') or "",
                    'content': {
                        'qty_on_entry_wh': item_information[0].get('qty_on_entry_wh'),
                        'item_name': item_information[0].get('item_name'),
                        'locations': get_item_locations(item_information[0].get('item_code'))
                    }}]
        return response
    return None

@frappe.whitelist()
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
    return warehouse_dict
    
def get_item_warehouse(item):
    warehouses = frappe.db.sql("""
                                SELECT
                                    `tabBin`.`item_code` AS `item_code`,
                                    `tabBin`.`warehouse` AS `warehouse`,
                                    `tabBin`.`actual_qty` AS `qty`,
                                    `tabWarehouse`.`warehouse_type` AS `warehouse_type`,
                                    `tabWarehouse`.`warehouse_size` AS `warehouse_size`
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
                                    ) AS `total`,
                                    `tabWarehouse`.`warehouse_size` AS `warehouse_size`
                                FROM
                                    `tabWarehouse`
                                WHERE
                                    `disabled` = 0
                                ORDER BY
                                    CASE `warehouse_type`
                                        WHEN 'BP' THEN 1
                                        WHEN 'LP' THEN 2
                                        WHEN 'KP' THEN 3
                                        ELSE 4
                                    END;
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
    
    stock_entry = create_single_stock_entry("Material Transfer", item, qty, source_warehouse, target_warehouse)
    
    return {'success': True, 'error': None}
    
def create_single_stock_entry(entry_type, item, qty, source_warehouse=None, target_warehouse=None):
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
        supplier_condition = """AND `tabPurchase Order`.`supplier` = '{0}'""".format(supplier)
    
    order_condition = """"""
    if order:
        order_condition = """AND `tabPurchase Order`.`name` = '{0}'""".format(order)
    
    #Get orders
    open_orders = frappe.db.sql("""
                                SELECT
                                    `tabPurchase Order`.`name`,
                                    DATE_FORMAT(`tabPurchase Order`.`transaction_date`, '%d.%m.%Y') AS `transaction_date`,
                                    DATE_FORMAT(`tabPurchase Order`.`schedule_date`, '%d.%m.%Y') AS `formatted_schedule_date`,
                                    `tabPurchase Order`.`supplier`,
                                    COUNT(
                                        CASE
                                            WHEN `tabPurchase Order Item`.`received_qty`
                                                 < `tabPurchase Order Item`.`qty`
                                            THEN 1
                                        END
                                    ) AS `open_items`
                                FROM
                                    `tabPurchase Order`
                                LEFT JOIN
                                    `tabPurchase Order Item` ON `tabPurchase Order Item`.`parent` = `tabPurchase Order`.`name`
                                WHERE
                                    `tabPurchase Order`.`per_received` < 100
                                AND
                                    `tabPurchase Order`.`docstatus` = 1
                                AND
                                    `tabPurchase Order`.`status` != 'Closed'
                                {supplier_condition}
                                {order_condition}
                                GROUP BY
                                    `tabPurchase Order`.`name`
                                ORDER BY
                                    `tabPurchase Order`.`schedule_date` ASC;""".format(supplier_condition=supplier_condition, order_condition=order_condition), as_dict=True)
    
    return open_orders

#Get Items from Open Order
@frappe.whitelist()
def get_order_items(order, item=False):
    item_condition = """"""
    if item:
        item_condition = """AND `tabPurchase Order Item`.`item_code` = '{0}'""".format(item)

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
                                `tabPurchase Order Item`.`parent` = %(po)s
                            {item_condition};""".format(item_condition=item_condition), {'po': order}, as_dict=True)
    
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

@frappe.whitelist()
def store_everything(order, submit):
    #get entry warehouse
    entry_warehouse = get_entry_warehouse()
    #create purchase receipt
    purchase_receipt = make_purchase_receipt(order)
    #update items with seg price values
    updated_items = get_updated_seg_prices(purchase_receipt.get('items'), purchase_receipt.get('buying_price_list'), purchase_receipt.get('currency'))
    purchase_receipt.set("items", updated_items)
    #set entry warehouse
    for item in purchase_receipt.items:
        item.warehouse = entry_warehouse
    #insert receipt
    try:
        purchase_receipt.insert()
        #Directly Submit with standard Freight Costs
        if sbool(submit):
            #Update SEG Totals and add Freight Costs/Exchange Fees
            purchase_receipt = calcualte_seg_totals(purchase_receipt)
            purchase_receipt.submit()
            return {'success': True, 'error': None, 'message': "Wareneingang {0} wurde erfolgreich gebucht.".format(purchase_receipt.name) }
        return {'success': True, 'error': None, 'message': "Wareneingang {0} wurde erfolgreich erstellt.".format(purchase_receipt.name) }
    except Exception as Err:
        frappe.log_error("Stock Entry Issue", "Error in Stock Entry from Stock Management App: {0}".format(Err))
        frappe.throw("Es ist ein Fehler beim erstellen der Lagerbuchung aufgetreten, Material wurde nicht umgebucht. Es wurde ein Fehlerbericht erstellt.")


def get_updated_seg_prices(items, price_list, currency):
    if currency != "CHF":
        exchange_rate = get_exchange_rate(currency, "CHF")
    for item in items:
        item_price = frappe.get_all(
            "Item Price",
            filters={
                        'item_code': item.get('item_code'),
                        'price_list': price_list,
                        'supplier': ""},
            fields=["name"]
            )

        
        if len(item_price) > 0:
            item_price_doc = frappe.get_doc("Item Price", item_price[0])
            item.freight_costs = item_price_doc.get('freight_costs') or 0
            item.currency_exchange_fees = item_price_doc.get('currency_exchange_fee') or 0
            if currency != "CHF":
                price_with_fee = item.get('rate') + (item.get('rate') / 100 * item_price_doc.get('currency_exchange_fee') or 0)
                price_in_chf = price_with_fee * exchange_rate
            else:
                price_in_chf = item.get('rate')
            seg_purchase_price = price_in_chf + item_price_doc.get('freight_costs') or 0
            item.seg_purchase_price = seg_purchase_price
            item.seg_amount = seg_purchase_price * item.qty
    return items

#Translate Barcode to Item Code
@frappe.whitelist()
def get_item_code(barcode):
    frappe.log_error("barcode", barcode)
    item = frappe.get_all("Item Barcode", filters={'barcode': barcode,'barcode_type': "EAN"}, fields=["parent"])
    frappe.log_error("item", item)
    if len(item) > 0:
        item_dict = get_single_item_basic_information(item[0].parent)
        frappe.log_error("item_dict", item_dict)
        return item_dict
    else:
        return None

@frappe.whitelist()
def get_single_item_basic_information(item):
    item_information = frappe.get_all("Item", {'name': item}, ['item_code', 'item_name', 'image'])
    
    if len(item_information) > 0:
        response = [{
                    'item_code': item_information[0].get('item_code'),
                    'picture': item_information[0].get('image') or "",
                    'content': {
                        'item_name': item_information[0].get('item_name')
                    }}]
        return response
    return None

#Return Items Dict by Warehouse
@frappe.whitelist()
def get_item_information_by_warehouse(warehouse):
    #CHeck if Entry Warehouse
    if warehouse == "entry_warehouse":
        warehouse = get_entry_warehouse()
    
    #Get all Items in Entry Warehouse
    items = frappe.get_all("Bin", filters={'warehouse': warehouse,  'actual_qty': [">", 0]}, fields=["item_code", "actual_qty"])
    
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

@frappe.whitelist()
def create_stock_entry(items, entry_type):
    items = json.loads(items)
    frappe.log_error("items", items)
    stock_entry = frappe.new_doc("Stock Entry")

    stock_entry.stock_entry_type = entry_type
    
    for item in items:
        stock_entry.append("items", {
            'item_code': item.get('item_code'),
            'qty': item.get('qty'),
            's_warehouse': item.get('from_warehouse'),
            't_warehouse': item.get('to_warehouse')
        })
    
    try:
        stock_entry.insert()
        stock_entry.submit()
        return {'stock_entry': stock_entry.name, 'success': 1}
    except Exception as Err:
        frappe.log_error("Stock Entry Issue", "Error in Stock Entry from Stock Management App: {0}".format(Err))
        return {'stock_entry': stock_entry.name, 'success': 1, 'error': "Es ist ein Fehler beim erstellen der Lagerbuchung aufgetreten, Material wurde nicht umgebucht. Es wurde ein Fehlerbericht erstellt."}


#Get Open Picking Lists
@frappe.whitelist()
def get_open_picking_lists(customer, picking_list):
    #Prepare condition
    customer_condition = """"""
    if customer:
        customer_condition = """AND `tabPicking List`.`customer` = '{0}'""".format(customer)
    
    picking_list_condition = """"""
    if picking_list:
        picking_list_condition = """AND `tabPicking List`.`name` = '{0}'""".format(picking_list)
    
    #Get orders
    open_picking_lists = frappe.db.sql("""
                                SELECT
                                    `tabPicking List`.`name` AS `name`,
                                    DATE_FORMAT(`tabPicking List`.`schedule_date`, '%d.%m.%Y') AS `formatted_schedule_date`,
                                    `tabPicking List`.`customer_name` AS `customer_name`,
                                    `tabPicking List`.`sales_order` AS `sales_order`,
                                    COUNT(
                                        CASE
                                            WHEN `tabPicking List Item`.`picked_qty`
                                                 < `tabPicking List Item`.`qty`
                                            THEN 1
                                        END
                                    ) AS `open_items`
                                FROM
                                    `tabPicking List`
                                LEFT JOIN
                                    `tabPicking List Item` ON `tabPicking List Item`.`parent` = `tabPicking List`.`name`
                                WHERE
                                    `tabPicking List`.`status` = 'Open'
                                AND
                                    `tabPicking List`.`docstatus` = 1
                                {customer_condition}
                                {picking_list_condition}
                                GROUP BY
                                    `tabPicking List`.`name`
                                ORDER BY
                                    `tabPicking List`.`schedule_date` ASC;""".format(customer_condition=customer_condition, picking_list_condition=picking_list_condition), as_dict=True)
    
    return open_picking_lists

#Get all Items for Picking List
@frappe.whitelist()
def get_picking_list_items(picking_list, item=False):
    #Prepare Item condition
    item_condition = """"""
    if item:
        item_condition = """AND `tabPicking List Item`.`item_code` = '{0}'""".format(item)
    
    items = frappe.db.sql("""
                            SELECT
                                `tabPicking List Item`.`name` AS `pl_detail`,
                                `tabPicking List Item`.`item_code` AS `item_code`,
                                `tabPicking List Item`.`item_name` AS `item_name`,
                                (`tabPicking List Item`.`qty` - `tabPicking List Item`.`picked_qty`) AS `qty`,
                                `tabItem`.`image` AS `image`,
                                `tabPicking List Item`.`so_detail` AS `so_detail`
                            FROM
                                `tabPicking List Item`
                            LEFT JOIN
                                `tabItem` ON `tabItem`.`name` = `tabPicking List Item`.`item_code`
                            WHERE
                                `tabPicking List Item`.`parent` = %(pl)s
                            {item_condition};""".format(item_condition=item_condition), {'pl': picking_list}, as_dict=True)
    
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
                                'stored_qty': 0,
                                'warehouses': []
                            }}
                
                response.append(item_response)
    else:
        response = None
        return response
    return response

#Create Pruchase Receipt for single Item to directly store it
@frappe.whitelist()
def create_single_receipt(item_code, target_warehouse, qty, order, submit=False):
    frappe.log_error("purchase_receipt", "item: {0}<br>wh: {1}<br>qty: {2}<br>order: {3}".format(item_code, target_warehouse, qty, order))
    #create purchase receipt
    purchase_receipt = make_purchase_receipt(order)
    
    #Remove other items and set qty
    for item in purchase_receipt.items:
        if item.item_code == item_code:
            item.qty = flt(qty)
            item.warehouse = target_warehouse
        else:
            item.qty = 0
    
    purchase_receipt.items = [
        item for item in purchase_receipt.items
        if item.qty > 0
    ]
    
    
    #update items with seg price values
    updated_items = get_updated_seg_prices(purchase_receipt.get('items'), purchase_receipt.get('buying_price_list'), purchase_receipt.get('currency'))
    purchase_receipt.set("items", updated_items)
    
    #insert receipt
    try:
        purchase_receipt.insert()
        if sbool(submit):
            #Update SEG Totals and add Freight Costs/Exchange Fees
            purchase_receipt = calcualte_seg_totals(purchase_receipt)
            purchase_receipt.submit()
            return {'success': True, 'error': None, 'message': "Wareneingang {0} wurde erfolgreich gebucht.".format(purchase_receipt.name) }
        return {'success': True, 'error': None, 'message': "Wareneingang {0} wurde erfolgreich erstellt.".format(purchase_receipt.name) }
    except Exception as Err:
        frappe.log_error("Stock Entry Issue", "Error in Stock Entry from Stock Management App: {0}".format(Err))
        frappe.throw("Es ist ein Fehler beim erstellen der Lagerbuchung aufgetreten, Material wurde nicht umgebucht. Es wurde ein Fehlerbericht erstellt.")


def calcualte_seg_totals(purchase_receipt):
    #get SEG Setting and exchange rates
    seg_settings = frappe.get_doc("SEG Settings", "SEG Settings")
    if purchase_receipt.currency != "CHF":
        exchange_to_chf = get_exchange_rate(purchase_receipt.currency, "CHF")
        if not exchange_to_chf:
            frappe.log_error("Exchange Rate missing", "While Creating a Purchase Receipt via Stock Management App Currency Exchange could not be found for Purchase Receipt {0}".format(purchase_receipt.name))
            frappe.throw("Kein Wechselkurs gefunden, bitte Wareneingang prüfen. Ein Fehlerbericht wurde erstellt.")
        exchange_from_chf = 1 / exchange_to_chf
    
    #initialize total values
    total = 0
    freight_costs = 0
    exchange_fees = 0
    
    for item in purchase_receipt.get('items'):
        total += item.get('seg_amount')
        freight_costs += item.get('freight_costs') * item.get('qty')
        exchange_fees += (item.get('amount') / 100) * item.get('currency_exchange_fees')

    #Set Seg Total
    purchase_receipt.seg_total = total
    
    #Add Freight Costs to Taxes
    if freight_costs > 0:
        #Exchange Freight Costs from CHF to Document Currency
        if purchase_receipt.currency != "CHF":
            freight_costs = freight_costs * exchange_from_chf
        
        #Add Subtable Entry
        purchase_receipt.append("taxes", {
                                    'reference_doctype': "Abo Reminder",
                                    'charge_type': "Actual",
                                    'account_head': seg_settings.get('freight_account'),
                                    'tax_amount': freight_costs,
                                    'description': seg_settings.get('freight_description'),
                                    'freight_exchange': 1
                                })
    
    
    #Add Exchange Fees to Taxes
    if exchange_fees > 0:
        #Add Subtable Entry
        purchase_receipt.append("taxes", {
                                    'reference_doctype': "Abo Reminder",
                                    'charge_type': "Actual",
                                    'account_head': seg_settings.get('exchange_account'),
                                    'tax_amount': exchange_fees,
                                    'description': seg_settings.get('exchange_description'),
                                    'freight_exchange': 1
                                })
    
    return purchase_receipt

@frappe.whitelist()
def filter_items_for_entry_wh(doctype, txt, searchfield, start, page_len, filters):
    #Get Entry Warehouse
    entry_warehouse = get_entry_warehouse()
    
    warehouse_items = frappe.db.sql("""
        SELECT
            `tabBin`.`item_code` AS `item_code`,
            `tabItem`.`item_name` AS `item_name`
        FROM
            `tabBin`
        LEFT JOIN
            `tabItem` ON `tabItem`.`name` = `tabBin`.`item_code`
        WHERE
            `tabBin`.`warehouse` = %(warehouse)s
        AND
            `tabBin`.`actual_qty` > 0
        AND 
            (`tabBin`.`item_code` LIKE %(txt)s OR `tabItem`.`item_name` LIKE %(txt)s)
        LIMIT
            %(start)s, %(page_len)s;""", {"txt": "%" + txt + "%", 'start': start, 'page_len': page_len, 'warehouse': entry_warehouse})
    
    return warehouse_items

@frappe.whitelist()
def create_sales_order(customer, items):
    #Prepare Items and get actual date
    items = json.loads(items)
    today = getdate()
    
    #Create Sales Order
    so_doc = frappe.get_doc({
        'doctype': "Sales Order",
        'customer': customer,
        'transporter': "Abgeholt",
        'picked_up': 1,
        'delivery_date': today
     })
    frappe.log_error("items", items)
    #Add Items
    for item in items:
        so_doc.append("items", {
                                'item_code': item.get('item_code'),
                                'qty': item.get('content').get('qty'),
                                'warehouse': item.get('content').get('warehouse'),
                                'delivery_date': today
                            })
    

    tax_template = frappe.get_doc("Sales Taxes and Charges Template", "MwSt, LSVA und VOC 2024 - SEG")
    so_doc.taxes_and_charges = tax_template.name
    so_doc.set("taxes", [])

    for tax in tax_template.taxes:
        new_tax = { 'charge_type': tax.charge_type,
                    'account_head': tax.account_head,
                    'description': tax.description,
                    'cost_center': tax.cost_center,
                    'rate': tax.rate }
        so_doc.append("taxes", new_tax)

    so_doc.calculate_taxes_and_totals()
    
    #Insert Sales Order
    try:
        so_doc.insert()
        return {'success': 1, 'name': so_doc.name}
    except Exception as Err:
        frappe.log_error("Stock Management App Error", "Es ist ein Fehler beim erstellen eines Auftrages entstanden:<br><br>".format(Err))
        return

@frappe.whitelist()
def create_delivery_note(picking_list, items):
    items = json.loads(items)
    #get Picking List and Sales Order
    picking_list_doc = frappe.get_doc("Picking List", picking_list)
    
    #Create Delivery Note
    delivery_note = make_delivery_note(source_name=picking_list_doc.get('sales_order'))
    
    #Set Mandatory Transporter
    if not delivery_note.get('transporter'):
        delivery_note.transporter = "Abgeholt"
    
    #Set Picking List
    delivery_note.picking_list = picking_list
    
    #Clear Items
    delivery_note.items = []
    
    #Add Items
    for item in items:
        for item_with_wh in item.get('content').get('warehouses'):
            delivery_note.append("items", {
                                    'item_code': item.get('item_code'),
                                    'qty': item_with_wh.get('qty'),
                                    'warehouse': item_with_wh.get('warehouse'),
                                    'pl_detail': item.get('content').get('pl_detail')
                                })
    
    #Insert Delivery Note
    try:
        delivery_note.insert()
        return {'success': 1, 'name': delivery_note.name}
    except Exception as Err:
        frappe.log_error("Stock Management Error", "EIn Fehler beim erstellen eines Lieferscheins ist aufgetreten:<br><br>{0}".format(Err))
        return {'success': 0}
    
    
