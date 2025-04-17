# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "seg"
app_title = "SEG"
app_publisher = "libracore AG"
app_description = "ERPNext Apps for SEG"
app_icon = "octicon octicon-file-directory"
app_color = "red"
app_email = "info@libracore.com"
app_license = "AGPL"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/seg/css/seg.css"
]

# app_include_js = "/assets/seg/js/seg.js"
app_include_js = [
    "/assets/seg/js/seg_common.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/seg/css/seg.css"
# web_include_js = "/assets/seg/js/seg.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Delivery Note" : "public/js/delivery_note.js",
    "Sales Invoice" : "public/js/sales_invoice.js",
    "Pricing Rule"  : "public/js/pricing_rule.js",
    "Customer"      : "public/js/customer.js",
    "Sales Order"   : "public/js/sales_order.js",
    "Item"          : "public/js/item.js",
    "Supplier"      : "public/js/supplier.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Quotation"     :"public/js/quotation.js",
    "Payment Reminder" :"public/js/payment_reminder.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "seg.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "seg.install.before_install"
# after_install = "seg.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "seg.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#   "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Address": {
        "autoname": "seg.seg.utils.object_autoname"
    },
    "Contact": {
        "autoname": "seg.seg.utils.object_autoname"
    },
    "Customer": {
        "before_insert": "seg.seg.customer.set_allow_invoice",
        "after_insert": "seg.seg.nextcloud.after_insert_handler",
        "after_rename": "seg.seg.nextcloud.after_rename_handler"
    },
    "Sales Invoice": {
        "on_submit": "seg.seg.utils.create_journal_entry",
        "on_cancel": "seg.seg.utils.create_journal_entry"
    },
    "Item": {
        "after_insert": [
            "seg.seg.utils.set_french_attributes", 
            "seg.seg.nextcloud.after_insert_handler"
        ],
        "after_rename": "seg.seg.nextcloud.after_rename_handler",
        "before_save": "seg.seg.purchasing.set_supplier_on_prices"
    },
    "Supplier": {
        "after_insert": "seg.seg.nextcloud.after_insert_handler",
        "after_rename": "seg.seg.nextcloud.after_rename_handler"
    },
    "Item Price": {
        "before_save": "seg.seg.purchasing.set_price_supplier"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
#   "all": [
#       "seg.tasks.all"
#   ],
    "daily": [
        "seg.seg.utils.convert_credits_to_advances",
        "seg.seg.purchasing.update_default_supplier"
    ]
#   "hourly": [
#       "seg.tasks.hourly"
#   ],
#   "weekly": [
#       "seg.tasks.weekly"
#   ]
#   "monthly": [
#       "seg.tasks.monthly"
#   ]
}

# Testing
# -------

# before_tests = "seg.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#   "frappe.desk.doctype.event.event.get_events": "seg.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#   "Task": "seg.task.get_dashboard_data"
# }

