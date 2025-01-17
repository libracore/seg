# Copyright (c) 2022-2025, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
from nc_py_api import Nextcloud
from frappe.utils.password import get_decrypted_password
from frappe.desk.form.load import get_attachments
import time
from frappe.model.document import Document
from frappe.utils import cint

PATHS = {
    'Item': {
        'general': "Allgemein",
        'procurement': "Einkauf"
    },
    'Customer': {
        'lables': "Etiketten",
        'visualisation': "Visualisierungen",
        'documents': "Dokumente",
        'general': "Allgemein"
    },
    'Supplier': {
        'general': "Allgemein",
        'procurement': "Einkauf"
    }
}

def get_path(doctype, target):
    return PATHS[doctype][target]
    
"""
This is the authentication function
"""
def get_client():
    settings = frappe.get_doc("SEG Settings", "SEG Settings")
    password = get_decrypted_password("SEG Settings", "SEG Settings", "cloud_password")
    nc = Nextcloud(
        nextcloud_url=settings.cloud_hostname, 
        nc_auth_user=settings.cloud_user, 
        nc_auth_pass=password
    )
    return nc

"""
This function will create a new folder with the required structure
"""
def create_folder(doctype, name):
    if cint(frappe.get_value("SEG Settings", "SEG Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    
    storage_path = get_storage_path(doctype, name)
    
    create_path(client, storage_path)
    for k, v in PATHS[doctype]:
        # create child folders
        create_path(client, os.path.join(storage_path, PATHS[doctype][k]))
    
    return

    
def get_storage_path(doctype, name):
    storage_folder = get_base_path()

    if not storage_folder:
        frappe.throw("Please configure the projects folder under SEG Settings", "Configuration missing")
        
    return os.path.join(storage_folder, doctype, name)

def get_base_path():
    storage_folder = frappe.get_value("SEG Settings", "SEG Settings", "storage_folder")
    return storage_folder
    
def create_path(client, path):
    if cint(frappe.get_value("SEG Settings", "SEG Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    # create folder
    try:
        client.files.mkdir(path)
    except Exception as err:
        frappe.throw("{0}: {1}".format(path, err), "Create project folder (NextCloud")
    return

    
"""
Write the file (local file path) to nextcloud
"""
def upload_from_local_file(doctype, name, target, file_name):
    if cint(frappe.get_value("SEG Settings", "SEG Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    storage_path = get_storaget_path(doctype, name)
    
    client.files.upload_stream(os.path.join(storage_path, target, file_name.split("/")[-1]), file_name)

    return

""" 
Extract the physical path from a file record
"""
def get_physical_path(file_name):
    file_url = frappe.get_value("File", file_name, "file_url")     # something like /private/files/myfile.pdf
    
    base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])
    
    return "{0}{1}".format(base_path, file_url)
    
"""
Write all attachments to nextcloud
"""
def upload_attachments(dt, dn):
    attachments = get_attachments(dt, dn)
    for a in attachments:
        physical_file_name = get_physical_path(a.get('file_name'))
        upload_from_local_file(dt, dn, PATHS[dt]['general'], physical_file_name)
    return
