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
                   }
            ]
        },
        {
            "label": _("Auftragsbearbeitung"),
            "icon": "fa fa-users",
            "items": [
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
                        "type": "report",
                        "name": "Preisliste",
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
        }
]
