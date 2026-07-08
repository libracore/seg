// Copyright (c) 2026, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Overview"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": (function() {
                                let year = frappe.datetime.get_today().split("-")[0];
                                return year + "-01-01";
                            })(),
            "reqd": 1
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname":"employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Sales Person"
        },
        {
            "fieldname":"item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname":"depth",
            "label": __("Depth"),
            "fieldtype": "Select",
            "options": "5 - Item Group\n4 - Product Group\n3 - Product Subcategory\n2 - Product Category"
        }
    ],
    onload: function(report) {
        report.page.add_inner_button(__("Berichtsinformationen"), function() {
            show_report_information();
        });
        
        report.page.add_inner_button(__("Aktuellen Bericht herunterladen"), function() {
            download_pdf();
        });
    }
};

function show_report_information() {
    let message = `<b>Priorität (Spalte 2):</b><br>
                    Zeigt die Priorität der jeweiligen Artikelgruppe (für Preisregeln).<br><br>
                    <b>Artikelgruppe (3):</b><br>
                    Zeigt den Namen der Artikelgruppe, auf welche sich die ganze Zeile bezieht.<br><br>
                    <b>Nettobetrag (4):</b><br>
                    Zeigt den Nettoumsatz der jeweiligen Artikelgruppe und aller dessen Unterartikelgruppen. Wird berechnet aus allen Positionen von gebuchten Lieferscheinen abzüglich die Rückvergütung welche prozentual im Kunden hinterlegt ist.<br><br>
                    <b>EK Total (5):</b><br>
                    Zeigt den Totalen Einkaufspreis welcher für die in dieser Zeile enthaltenen Positionen bezahlt wurde basierend auf der Valuation Rate(falls keine vorhanden ist, wird der letzte Einkaufspreis verwendet.<br><br>
                    <b>DB auf EK in CHF (6):</b><br>
                    Zeigt den Deckungsbeitrag in CHF: Nettobetrag - EK Tota.l<br><br>
                    <b>DB auf EK in % (7):</b><br>
                    Zeigt den Deckungsbeitrag in % bezogen auf den Nettobetrag: Deckungsbeitrag * 100 / Nettobetrag.<br><br>
                    <b>SEG-EK Total (8):</b><br>
                    Zeigt den Totalen Einkaufspreis welcher für die in dieser Zeile enthaltenen Positionen bezahlt wurde basierend auf dem SEG-EK welcher im Artikel hinterlegt ist.
                    <b>DB auf SEG-EK in CHF (9):</b><br>
                    Zeigt den Deckungsbeitrag auf den SEG-EK in CHF: Nettobetrag - SEG-EK Total.<br><br>
                    <b>DB auf SEG EK in % (10):</b><br>
                    Zeigt den Deckungsbeitrag in % bezogen auf den Nettobetrag: Deckungsbeitrag SEG-EK * 100 / Nettobetrag.<br><br>
                    ---------------------------------<br><br>
                    <b>Datumsfilter</b><br>
                    Filter die Lieferscheine nach einer Datumrange.<br><br>
                    <b>Mitarbeiterfilter</b><br>
                    Filtert die Lieferscheine nach dem Mitarbeiter welcher im hinterlegten Kunden als Verkaufsteam hinterlegt ist.<br><br>
                    <b>Artikelgruppenfilter</b><br>
                    Filtert nach der angegeben Artikelgruppe und allen Unterartikelgruppen davon.<br><br>
                    <b>Tiefefilter</b><br>
                    Hier kann angegeben bis zu welcher Tiefe die Artikelgruppen anzeigt werden.
                    `
    frappe.msgprint(message, "Berichtsinformationen");
}

function download_pdf() {
    frappe.call({
        'method': 'seg.seg.report.sales_overview.sales_overview.send_report',
        'args': {
            'download': true
        },
        'callback': function(response) {
            if (response.message) {
                window.open(response.message, "_blank");
            }
        }
    });
}
