# Copyright (c) 2017-2022, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt
#
# Open API for headless shops

import frappe

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
