# Copyright (c) 2022-2025, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
#from nc_py_api import Nextcloud        # requires Py3.9 or higher :-(
from webdav3.client import Client
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
    #nc = Nextcloud(
    #    nextcloud_url=settings.cloud_hostname, 
    #    nc_auth_user=settings.cloud_user, 
    #    nc_auth_pass=password
    #)
    
    options = {
        'webdav_hostname': "{0}/remote.php".format(settings.cloud_hostname),
        'webdav_root': "files/",
        'webdav_login': settings.cloud_user,
        'webdav_password': password
    }
    nc = Client(options)

    return nc

"""
Initialise
"""
def initialise():
    if cint(frappe.get_value("SEG Settings", "SEG Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    
    storage_folder = get_base_path()
    client.mkdir(storage_folder)
    for k,v in PATHS.items():
        client.mkdir(os.path.join(storage_folder, k))
        
    return
    
"""
This function will create a new folder with the required structure
"""
def create_folder(doctype, name):
    if cint(frappe.get_value("SEG Settings", "SEG Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    
    storage_path = get_storage_path(doctype, name)
    
    create_path(client, storage_path)
    for k, v in PATHS[doctype].items():
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
        #client.files.mkdir(path)
        if not client.check(path):
            client.mkdir(path)
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
    target_path = os.path.join(storage_path, target)
    
    #client.files.upload_stream(os.path.join(storage_path, target, file_name.split("/")[-1]), file_name)
    if client.check(os.path.join(storage_path, target)):
        client.upload_sync(os.path.join(target_path, file_name.split("/")[-1]), file_name)
    else:
        # try to create the requested folder
        try:
            create_path(client, target_path)
            client.upload_sync(os.path.join(target_path, file_name.split("/")[-1]), file_name)
        except:
            frappe.throw("Unable to upload {0} to {1}".format(file_name, target_path))

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
