# Copyright (c) 2017-2022, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt
#
# Open API for headless shops

import frappe
import json
from datetime import date

@frappe.whitelist()
def get_user_image(user):
    return frappe.get_value("User", user, "user_image")

@frappe.whitelist()
def get_matching_variant(item_code, old_selection, new_selection):
    attributes = json.loads(new_selection)
    for a in json.loads(old_selection):
        # refine search, add attribute
        for k,v in a.items():
            if k not in attributes:
                attributes[k] = v
        # check if there are multiple variants matching
        matches = get_next_attribute_and_values(item_code, attributes)
        if len(matches['filtered_items']) == 1:
            # leave with this variant code
            return list(matches['filtered_items'])[0]
    # nothing found
    return None

@frappe.whitelist()
def get_prices(item_code, user):
    from erpnext.controllers.website_list_for_contact import get_customers_suppliers
    if user:
        customers, suppliers = get_customers_suppliers("Sales Invoice", user)
        if len(customers) > 0:
            customer = customers[0]
        else:
            customer  = "None"
    else:
        customer = "None"
    sql_query = """SELECT 
            `raw`.`item_code`,
            `raw`.`item_name`,
            `raw`.`item_group`,
            GROUP_CONCAT(`tabItem Variant Attribute`.`attribute_value`) AS `attributes`,
            `raw`.`stock_uom`,
            ROUND(`raw`.`price_list_rate`, 2) AS `price_list_rate`,
            `raw`.`pricing_rule`,
            `tPR`.`discount_percentage` AS `discount_percentage`,
            ROUND(((100 - IFNULL(`tPR`.`discount_percentage`, 0))/100) * `raw`.`price_list_rate`, 2) AS `discounted_rate`
        FROM 
            (SELECT 
              `tabItem`.`item_code` AS `item_code`,
              `tabItem`.`item_name` AS `item_name`,
              `tabItem`.`item_group` AS `item_group`,
              `tabItem`.`last_purchase_rate` AS `last_purchase_rate`,
              CONCAT(ROUND(`tabItem`.`weight_per_unit`, 1), " ", `tabItem`.`weight_uom`) AS `stock_uom`,
              (SELECT `tabItem Price`.`price_list_rate` 
               FROM `tabItem Price` 
               WHERE `tabItem Price`.`item_code` = `tabItem`.`item_code`
                 AND `tabItem Price`.`price_list` = "Standard-Vertrieb") AS `price_list_rate`,
              (SELECT `tabPricing Rule`.`name`
               FROM `tabPricing Rule`
               LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule Item Code`.`parent` = `tabPricing Rule`.`name`
               LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule Item Group`.`parent` = `tabPricing Rule`.`name`
               WHERE `tabPricing Rule`.`selling` = 1
                 AND `tabPricing Rule`.`customer` = "{customer}"
                 AND `tabPricing Rule`.`disable` = 0
                 AND (`tabPricing Rule Item Code`.`item_code` = `tabItem`.`item_code`
                      OR `tabPricing Rule Item Group`.`item_group` = `tabItem`.`item_group`
                      OR `tabPricing Rule Item Group`.`item_group` = "Alle Artikelgruppen")
               ORDER BY `tabPricing Rule`.`priority` DESC
               LIMIT 1) AS `pricing_rule`
            FROM `tabItem`
            WHERE `tabItem`.`item_code` = "{item_code}"
              OR `tabItem`.`variant_of` = "{item_code}"
            ) AS `raw`
        LEFT JOIN `tabPricing Rule` AS `tPR` ON `tPR`.`name` = `raw`.`pricing_rule`
        LEFT JOIN `tabItem Variant Attribute` ON `raw`.`item_code` = `tabItem Variant Attribute`.`parent`
        GROUP BY `raw`.`item_code`
    """.format(customer=customer, item_code=item_code)
    data = frappe.db.sql(sql_query, as_dict=True)
    return data

@frappe.whitelist(allow_guest=True)
def get_public_prices(item_code):
    return get_prices(item_code, None)

# deprecated, will be dropped in future versions; refer to shop module
@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    from frappe.auth import LoginManager
    lm = LoginManager()
    lm.authenticate(usr, pwd)
    lm.login()
    return frappe.local.session
    
@frappe.whitelist(allow_guest=True)
def get_item_groups():
    # grab root node
    root_node = frappe.db.sql("""SELECT `name` FROM `tabItem Group` 
        WHERE (`parent_item_group` IS NULL OR `parent_item_group` = "");""", 
        as_dict=True)[0]['name']
    return get_child_group(root_node)
    
def get_child_group(item_group):
    groups = []
    sub_groups = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 1, 'show_in_website': 1},
        fields=['name'])
    for s in sub_groups:
        sg = {}
        sg[s['name']] = get_child_group(s['name'])
        groups.append(sg)
    nodes = frappe.get_all("Item Group", 
        filters={'parent_item_group': item_group, 'is_group': 0, 'show_in_website': 1},
        fields=['name'])
    for n in nodes:
        groups.append(n['name'])
    return groups

@frappe.whitelist(allow_guest=True)
def get_top_products():
    top_products = frappe.db.sql("""
        SELECT `item_code`, `item_name`, `image`
        FROM `tabItem`
        WHERE `show_in_website` = 1
        ORDER BY `weightage` DESC
        LIMIT 20;""", as_dict=True)
    return top_products

@frappe.whitelist(allow_guest=True)
def get_products_by_item_group(item_group, show_variants=False):
    if show_variants:
        condition = ""
    else:
        condition = "AND `variant_of` IS NULL"
    products = frappe.db.sql("""
        SELECT `item_code`, `item_name`, `image`
        FROM `tabItem`
        WHERE `show_in_website` = 1
          AND `item_group` = "{item_group}"
          {condition}
        ORDER BY `weightage` DESC
        LIMIT 20;""".format(item_group=item_group, condition=condition), as_dict=True)
    return products
    
@frappe.whitelist(allow_guest=True)
def register_newsletter(name, email):
    status = "unkonwn"
    error = None
    try:
        new_contact = frappe.get_doc({
            'doctype': 'Contact',
            'first_name': name,
            'email_id': email,
            'email_ids': [
                {'email_id': email, 'is_primary': 1}
            ],
            'unsubscribed': 0
        })
        new_contact.insert(ignore_permissions=True)
        frappe.db.commit()
        status = "success"
    except Exception as err:
        status = "failed"
        error = err
    return {'status': status, 'error': error}

@frappe.whitelist(allow_guest=True)
def search_products(keyword, offset=0):
    products = frappe.db.sql("""
        SELECT `item_code`, `item_name`, `image`
        FROM `tabItem`
        WHERE `show_in_website` = 1
          AND (`item_code` LIKE "%{keyword}%"
               OR `item_name` LIKE "%{keyword}%"
               OR `description` LIKE "%{keyword}%")
        ORDER BY `weightage` DESC
        LIMIT 20
        OFFSET {offset};""".format(keyword=keyword, offset=offset), as_dict=True)
    return products

@frappe.whitelist(allow_guest=True)
def get_item_details(item_code):
    item_details = frappe.db.sql("""
        SELECT
            `tabItem`.`item_code` AS `item_code`,
            `tabItem`.`item_name` AS `item_name`,
            `tabItem`.`description` AS `description`,
            `tabItem`.`web_long_description` AS `web_long_description`,
            `tabItem`.`website_content` AS `website_content`,
            `tabItem`.`has_variants` AS `has_variants`,
            `tabItem`.`image` AS `image`,
            `tabItem`.`website_image` AS `website_image`,
            `tabItem`.`verpackungseinheit` AS `packaging_unit`,
            `tabItem`.`voc` AS `voc`,
            `tabItem`.`stock_uom` AS `stock_uom`,
            `tabItem`.`density` AS `density`,
            `tabItem`.`weight_per_unit` AS `weight_per_unit`,
            `tabItem`.`weight_uom` AS `weight_uom`
        FROM `tabItem`
        WHERE `tabItem`.`item_code` = "{item_code}"
          AND `tabItem`.`show_in_website` = 1;
    """.format(item_code=item_code), as_dict=True)
    if len(item_details) > 0:
        more_images = frappe.db.sql("""
            SELECT
                `description`,
                `image`
            FROM `tabItem Image`
            WHERE `parent` = "{item_code}";
        """.format(item_code=item_code), as_dict=True)
        item_details[0]['more_images'] = more_images
        
        related_items = frappe.db.sql("""
            SELECT 
                `tabItem`.`item_code`, 
                `tabItem`.`item_name`, 
                `tabItem`.`image`
            FROM `tabRelated Item`
            LEFT JOIN `tabItem` ON `tabItem`.`item_code` = `tabRelated Item`.`item_code`
            WHERE `tabRelated Item`.`parent` = "{item_code}";
        """.format(item_code=item_code), as_dict=True)
        item_details[0]['related_items'] = related_items
        
        variants = frappe.db.sql("""
            SELECT 
                `tabItem`.`item_code`
            FROM `tabItem`
            WHERE `tabItem`.`variant_of` = "{item_code}";
        """.format(item_code=item_code), as_dict=True)
        for v in variants:
            variant_attributes = frappe.db.sql("""
                SELECT 
                    `tabItem Variant Attribute`.`attribute`,
                    `tabItem Variant Attribute`.`attribute_value`
                FROM `tabItem Variant Attribute`
                WHERE `tabItem Variant Attribute`.`parent` = "{item_code}";
            """.format(item_code=v['item_code']), as_dict=True)
            v['attributes'] = variant_attributes
        item_details[0]['variants'] = variants
        
        variant_attributes = frappe.db.sql("""
            SELECT 
                `tabItem Variant Attribute`.`attribute`
            FROM `tabItem Variant Attribute`
            WHERE `tabItem Variant Attribute`.`parent` = "{item_code}";
        """.format(item_code=item_code), as_dict=True)
        item_details[0]['variant_attributes'] = variant_attributes
    return item_details

@frappe.whitelist()
def get_addresses():
    addresses = frappe.db.sql("""
        SELECT 
            `tabAddress`.`name`,
            `tabAddress`.`address_type`,
            `tabAddress`.`address_line1`,
            `tabAddress`.`address_line2`,
            `tabAddress`.`pincode`,
            `tabAddress`.`city`,
            `tabAddress`.`country`,
            `tabAddress`.`is_primary_address`,
            `tabAddress`.`is_shipping_address`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabDynamic Link` AS `tA1` ON `tA1`.`parenttype` = "Address" 
                                       AND `tA1`.`link_doctype` = "Customer" 
                                       AND `tA1`.`link_name` = `tC1`.`link_name`
        LEFT JOIN `tabAddress` ON `tabAddress`.`name` = `tA1`.`parent`
        WHERE `tabContact`.`user` = "{user}";
    """.format(user=frappe.session.user), as_dict=True)
    return addresses

def get_session_customers():
    # fetch customers for this user
    customers = frappe.db.sql("""
        SELECT 
            `tC1`.`link_name` AS `customer`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        WHERE `tabContact`.`user` = "{user}";
    """.format(user=frappe.session.user), as_dict=True)
    return customers
    
@frappe.whitelist()
def create_address(address_line1, pincode, city, address_type="Shipping", address_line2=None, country="Schweiz"):
    error = None
    # fetch customers for this user
    customers = get_session_customers()
    customer_links = []
    for c in customers:
        customer_links.append({'link_doctype': 'Customer', 'link_name': c['customer']})
    # create new address
    new_address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': "{0} {1} {2}".format(customers[0]['customer'], address_line1, city),
        'address_type': address_type,
        'address_line1': address_line1,
        'address_line2': address_line2,
        'pincode': pincode,
        'city': city,
        'country': country,
        'links': customer_links
    })
    
    try:
        new_address.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as err:
        error = err
    return {'error': error, 'name': new_address.name or None}

@frappe.whitelist()
def update_address(name, address_line1, pincode, city, address_line2=None, country="Schweiz"):
    error = None
    # fetch customers for this user
    customers = get_session_customers()
    address = frappe.get_doc("Address", name)
    permitted = False
    for l in address.links:
        for c in customers:
            if l.link_name == c['customer']:
                permitted = True
    if permitted:
        # update address
        address.address_line1 = address_line1
        address.address_line2 = address_line2
        address.pincode = pincode
        address.city = city
        address.country = country
        try:
            address.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as err:
            error = err
    else:
        error = "Permission error"
    return {'error': error, 'name': address.name or None}

@frappe.whitelist()
def delete_address(name):
    error = None
    # fetch customers for this user
    customers = get_session_customers()
    address = frappe.get_doc("Address", name)
    permitted = False
    for l in address.links:
        for c in customers:
            if l.link_name == c['customer']:
                permitted = True
    if permitted:
        # delete address: drop links
        address.links = []
        try:
            address.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as err:
            error = err
    else:
        error = "Permission error"
    return {'error': error}
    
@frappe.whitelist()
def get_delivery_notes(commission=None):
    conditions = ""
    if commission:
        conditions = """ AND `tabDelivery Note`.`commission` LIKE "%{commission}%" """.format(commission=commission)
    delivery_notes = frappe.db.sql("""
        SELECT 
            `tabDelivery Note`.`name` AS `delivery_note`,
            `tabDelivery Note`.`posting_date` AS `date`,
            `tabDelivery Note`.`commission` AS `commission`,
            `tabDelivery Note`.`grand_total` AS `grand_total`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabDelivery Note` ON `tabDelivery Note`.`customer` = `tC1`.`link_name`
        WHERE `tabContact`.`user` = "{user}"
          AND `tabDelivery Note`.`docstatus` = 1
          {conditions}
        ORDER BY `tabDelivery Note`.`posting_date` DESC;
    """.format(user=frappe.session.user, conditions=conditions), as_dict=True)
    return delivery_notes

@frappe.whitelist()
def get_sales_invoices(commission=None):
    conditions = ""
    if commission:
        conditions = """ AND `tabSales Invoice`.`commission` LIKE "%{commission}%" """.format(commission=commission)
    sales_invoices = frappe.db.sql("""
        SELECT 
            `tabSales Invoice`.`name` AS `sales_invoice`,
            `tabSales Invoice`.`posting_date` AS `date`,
            `tabSales Invoice`.`due_date` AS `due_date`,
            `tabSales Invoice`.`commission` AS `commission`,
            `tabSales Invoice`.`grand_total` AS `grand_total`,
            `tabSales Invoice`.`outstanding_amount` AS `grand_total`,
            `tabSales Invoice`.`status` AS `status`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabSales Invoice` ON `tabSales Invoice`.`customer` = `tC1`.`link_name`
        WHERE `tabContact`.`user` = "{user}"
          AND `tabSales Invoice`.`docstatus` = 1
          {conditions}
        ORDER BY `tabSales Invoice`.`posting_date` DESC;
    """.format(user=frappe.session.user, conditions=conditions), as_dict=True)
    return sales_invoices

@frappe.whitelist()
def get_profile():
    profile = frappe.db.sql("""
        SELECT 
            `tabCustomer`.`image` AS `image`,
            `tabCustomer`.`name` AS `customer_name`,
            `tabContact`.`first_name` AS `first_name`,
            `tabContact`.`last_name` AS `last_name`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabCustomer` ON `tabCustomer`.`name` = `tC1`.`link_name`
        WHERE `tabContact`.`user` = "{user}";
    """.format(user=frappe.session.user), as_dict=True)
    return profile

@frappe.whitelist()
def get_coupon(coupon):
    coupons = frappe.db.sql("""
        SELECT `discount`
        FROM `tabCoupon`
        WHERE `code` = "{coupon}";
    """.format(coupon=coupon), as_dict=True)
    return coupons

@frappe.whitelist()
def get_visualisations():
    visualisations = frappe.db.sql("""
        SELECT 
            `tabVisualisation`.`project_name` AS `project_name`,
            `tabVisualisation`.`before_image` AS `before_image`,
            `tabVisualisation`.`after_image` AS `after_image`,
            `tabVisualisation`.`name` AS `visualisation`,
            `tabVisualisation`.`date` AS `date`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabVisualisation` ON `tabVisualisation`.`customer` = `tC1`.`link_name`
        WHERE `tabContact`.`user` = "{user}"
        ORDER BY `tabVisualisation`.`date` DESC;
    """.format(user=frappe.session.user), as_dict=True)
    return visualisations

@frappe.whitelist()
def place_order(shipping_address, items, commission=None, discount=0, paid=False):
    error = None
    so_ref = None
    # fetch customers for this user
    customers = get_session_customers()
    try:
        # create sales order
        sales_order = frappe.get_doc({
            'doctype': 'Sales Order',
            'customer': customers[0]['customer'],
            'commission': commission,
            'shipping_address_name': shipping_address,
            'apply_discount_on': 'Net Total',
            'additional_discount_percentage': float(discount),
            'delivery_date': date.today()
        })
        # create item records
        items = json.loads(items)
        for i in items:
            sales_order.append('items', {
                'item_code': i['item'],
                'qty': i['qty']
            })
        # taxes and charges
        taxes_and_charges = frappe.db.sql("""
            SELECT 
                `tabSales Taxes and Charges Template`.`name` AS `template`,
                `tabSales Taxes and Charges`.`charge_type` AS `charge_type`,
                `tabSales Taxes and Charges`.`account_head` AS `account_head`,
                `tabSales Taxes and Charges`.`rate` AS `rate`,
                `tabSales Taxes and Charges`.`row_id` AS `row_id`,
                `tabSales Taxes and Charges`.`description` AS `description`
            FROM `tabSales Taxes and Charges Template`
            JOIN `tabSales Taxes and Charges` ON `tabSales Taxes and Charges`.`parent` = `tabSales Taxes and Charges Template`.`name`
            WHERE `tabSales Taxes and Charges Template`.`is_default` = 1
            ORDER BY `tabSales Taxes and Charges`.`idx` ASC;
        """, as_dict=True)
        sales_order.taxes_and_charges = taxes_and_charges[0]['template']
        for t in taxes_and_charges:
            sales_order.append('taxes', {
                'charge_type': t['charge_type'],
                'account_head': t['account_head'],
                'rate': t['rate'],
                'row_id': t['row_id'],
                'description': t['description']
            })
        # payment
        if paid == "1":
            sales_order.po_no = "Bezahlt mit Stripe ({0})".format(date.today())
        # insert and submit
        sales_order.insert(ignore_permissions=True)
        sales_order.submit()
        frappe.db.commit()
        so_ref = sales_order.name
        # create payment
        #if paid == "1":
        #    payment = frappe.get_doc({
        #        'doctype': 'Payment Entry',
        #        'payment_type': 'Receive',
        #        'posting_date': date.today(),
        #        'party_type': 'Customer',
        #        'party': customers[0]['customer'],
        #        'paid_to': frappe.get_value("Webshop Settings", "Webshop Settings", 'stripe_account'),
        #        'paid_amount': sales_order.grand_total,
        #        'reference_no': sales_order.name,
        #        'reference_date': date.today(),
        #        'references': [{
        #            'reference_doctype': 'Sales Order',
        #            'reference_name': sales_order.name,
        #            'allocated_amount': sales_order.grand_total
        #        }]
        #    })
        #    payment.insert(ignore_permissions=True)
        #    payment.submit()
        #    frappe.db.commit()
    except Exception as err:
        error = err
        
    return {'error': error, 'sales_order': so_ref}
    
    
    
