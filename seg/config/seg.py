from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Auftragsbearbeitung"),
            "icon": "fa fa-users",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Customer",
                       "label": _("Customer"),
                       "description": _("Customer")
                   },
                   {
                       "type": "doctype",
                       "name": "Quotation",
                       "label": _("Quotation"),
                       "description": _("Quotation")
                   },
                   {
                       "type": "doctype",
                       "name": "Sales Order",
                       "label": _("Sales Order"),
                       "description": _("Sales Order")
                   },
                   {
                       "type": "doctype",
                       "name": "Delivery Note",
                       "label": _("Delivery Note"),
                       "description": _("Delivery Note")
                   },
                   {
                       "type": "doctype",
                       "name": "Sales Invoice",
                       "label": _("Sales Invoice"),
                       "description": _("Sales Invoice")
                   },
                   {
                       "type": "doctype",
                       "name": "Payment Entry",
                       "label": _("Payment Entry"),
                       "description": _("Payment Entry")
                   },
                   {
                       "type": "doctype",
                       "name": "Payment Reminder",
                       "label": _("Payment Reminder"),
                       "description": _("Payment Reminder")
                   }
            ]
        },
        {
            "label": _("Einkauf"),
            "icon": "fa fa-users",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Supplier",
                       "label": _("Supplier"),
                       "description": _("Supplier")
                   },
                   {
                       "type": "doctype",
                       "name": "Purchase Order",
                       "label": _("Purchase Order"),
                       "description": _("Purchase Order")
                   },
                   {
                       "type": "doctype",
                       "name": "Purchase Receipt",
                       "label": _("Purchase Receipt"),
                       "description": _("Purchase Receipt")
                   },
                   {
                       "type": "doctype",
                       "name": "Purchase Invoice",
                       "label": _("Purchase Invoice"),
                       "description": _("Purchase Invoice")
                   },
                   {
                       "type": "doctype",
                       "name": "Payment Proposal",
                       "label": _("Payment Proposal"),
                       "description": _("Payment Proposal")
                   }
            ]
        },
        {
            "label": _("Projects"),
            "icon": "fa fa-users",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Project",
                       "label": _("Project"),
                       "description": _("Project")
                   }
            ]
        },
        {
            "label": _("Stock"),
            "icon": "fa fa-users",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Item",
                       "label": _("Item"),
                       "description": _("Item")
                   },
                   {
                       "type": "doctype",
                       "name": "Stock Entry",
                       "label": _("Stock Entry"),
                       "description": _("Stock Entry")
                   }
            ]
        },
        {
            "label": _("Banking"),
            "icon": "fa fa-money",
            "items": [
                   {
                       "type": "page",
                       "name": "bank_wizard",
                       "label": _("Bank Wizard"),
                       "description": _("Bank Wizard")
                   },
                   {
                       "type": "doctype",
                       "name": "Payment Proposal",
                       "label": _("Payment Proposal"),
                       "description": _("Payment Proposal")
                   },
                   {
                        "type": "report",
                        "name": "General Ledger",
                        "label": _("General Ledger"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Balance Sheet",
                        "label": _("Balance Sheet"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Profit and Loss Statement",
                        "label": _("Profit and Loss Statement"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    }
            ]
        },
        {
            "label": _("Reports"),
            "icon": "fa fa-bank",
            "items": [
                    {
                       "type": "doctype",
                       "name": "Sales Report",
                       "label": _("Sales Report"),
                       "description": _("Sales Report")
                    },
                    {
                        "type": "report",
                        "name": "SEG Preisliste",
                        "label": _("Preisliste"),
                        "doctype": "Item Price",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Kundenbindung",
                        "label": _("Kundenbindung"),
                        "doctype": "Customer",
                        "is_query_report": True
                    }
            ]
        },
        {
            "label": _("Webshop"),
            "icon": "fa fa-users",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Coupon",
                       "label": _("Coupon"),
                       "description": _("Coupon")
                   },
                   {
                       "type": "doctype",
                       "name": "Visualisation",
                       "label": _("Visualisation"),
                       "description": _("Visualisation")
                   },
                   {
                       "type": "doctype",
                       "name": "Webshop Settings",
                       "label": _("Webshop Settings"),
                       "description": _("Webshop Settings")
                   },
                   {
                       "type": "doctype",
                       "name": "Datatrans Settings",
                       "label": _("Datatrans Settings"),
                       "description": _("Datatrans Settings")                   
                   },
                   {
                       "type": "doctype",
                       "name": "Webshop Log",
                       "label": _("Webshop Log"),
                       "description": _("Webshop Log")                   
                   }
            ]
        }
]
