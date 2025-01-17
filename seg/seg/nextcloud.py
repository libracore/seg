# Copyright (c) 2022-2024, libracore and Contributors
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
        'documents': "Dokumente"
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
    
    create_path(client, project_path)
    # create child folders
    create_path(client, os.path.join(project_path, PATHS['admin']))
    create_path(client, os.path.join(project_path, PATHS['quotation']))
    create_path(client, os.path.join(project_path, PATHS['order']))
    create_path(client, os.path.join(project_path, PATHS['invoice']))
    create_path(client, os.path.join(project_path, PATHS['drilling']))
    create_path(client, os.path.join(project_path, PATHS['plan']))
    create_path(client, os.path.join(project_path, PATHS['road']))
    create_path(client, os.path.join(project_path, PATHS['subprojects']))
    create_path(client, os.path.join(project_path, PATHS['subprojects_heim']))
    create_path(client, os.path.join(project_path, PATHS['subprojects_geomill']))
    create_path(client, os.path.join(project_path, PATHS['supplier']))
    create_path(client, os.path.join(project_path, PATHS['supplier_ews']))
    create_path(client, os.path.join(project_path, PATHS['supplier_mud']))
    create_path(client, os.path.join(project_path, PATHS['supplier_other']))
    create_path(client, os.path.join(project_path, PATHS['incidents']))
    create_path(client, os.path.join(project_path, PATHS['memo']))
    
    check_upload_quotation(project)
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
def upload_from_local_file(doctype, target, file_name):
    if cint(frappe.get_value("Heim Settings", "Heim Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    project_path = get_project_path(project)
    if client.check(os.path.join(project_path, target)):
        client.upload_sync(os.path.join(project_path, target, file_name.split("/")[-1]), file_name)
    else:
        # try to create the requested folder
        try:
            create_path(client, os.path.join(project_path, target))
            client.upload_sync(os.path.join(project_path, target, file_name.split("/")[-1]), file_name)
        except:
            # fallback to root (for migration projects)
            client.upload_sync(os.path.join(project_path, file_name.split("/")[-1]), file_name)

    return

"""
Write the a local file (local file path) to the nextcloud base path (00_Projekte)
"""
def write_file_to_base_path(file_name):
    if cint(frappe.get_value("Heim Settings", "Heim Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    base_path = get_base_path()
    target = os.path.join(base_path, file_name.split("/")[-1])
    client.upload_sync(target, file_name)
    return

"""
Delete a file from nextcloud
"""
def delete_project_file(project, file_name, target=PATHS['drilling']):
    if cint(frappe.get_value("Heim Settings", "Heim Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)
        
    client = get_client()
    project_path = get_project_path(project)
    if client.check(os.path.join(project_path, target)):
        client.clean(os.path.join(project_path, target, file_name.split("/")[-1]))

    return
    
"""
This function gets the cloud link to a project
"""
@frappe.whitelist()
def get_cloud_url(project):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    # only use base project folder (for split projects the first one
    project = project[:8] if len(project) >= 8 else project
    return "{0}/index.php/apps/files/?dir=/{1}/{2}".format(settings.cloud_hostname, settings.projects_folder, project)

""" 
Extract the physical path from a file record
"""
def get_physical_path(file_name):
    file_url = frappe.get_value("File", file_name, "file_url")     # something like /private/files/myfile.pdf
    
    base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])
    
    return "{0}{1}".format(base_path, file_url)
    
"""
Hook from File: upload specific files to nextcloud
"""
def upload_file(self, event):
    if cint(frappe.get_value("Heim Settings", "Heim Settings", "nextcloud_enabled")) == 0:
        return      # skip if nextcloud is disabled (develop environments)

    if self.attached_to_doctype == "Bohranzeige":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        physical_file_name = get_physical_path(self.name)
        write_project_file_from_local_file (project, physical_file_name, PATHS['drilling'])
    
    elif self.attached_to_doctype == "Purchase Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            if frappe.get_value("Purchase Order", self.attached_to_name, "supplier") in ("L-80011", "L-80061", "L-80154"):
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_ews'])
            else:
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_other'])
    
    elif self.attached_to_doctype == "Purchase Receipt":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            if frappe.get_value("Purchase Receipt", self.attached_to_name, "supplier") in ("L-80011", "L-80061", "L-80154"):
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_ews'])
            else:
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_other'])
                
    elif self.attached_to_doctype == "Quotation":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['quotation'])
            
    elif self.attached_to_doctype == "Sales Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['order'])
            
    elif self.attached_to_doctype == "Sales Invoice":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['invoice'])
    
    elif self.attached_to_doctype == "Project":
        project = self.attached_to_name
        # mark file allocation
        pending_file = frappe.get_doc({
            'doctype': "Pending File Allocation",
            'project': project,
            'file_id': self.name,
            'file_url': self.file_url
        })
        pending_file.insert(ignore_permissions=True)
        frappe.db.commit()
        
        physical_file_name = get_physical_path(self.name)
        write_project_file_from_local_file (project, physical_file_name, PATHS['drilling'])
    
    elif self.attached_to_doctype == "Request for Public Area Use":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['road'])
        
    elif self.attached_to_doctype == "Subcontracting Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['subprojects'])
    
    elif self.attached_to_doctype == "Subcontracting Order Finish":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['subprojects_heim'])
            
    elif self.attached_to_doctype == "Water Supply Registration":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['drilling'])
    
    elif self.attached_to_doctype == "Construction Site Description":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['subprojects'])
            
    return

"""
Write all attachments to nextcloud
"""
def upload_attachments(dt, dn, project):
    attachments = get_attachments(dt, dn)
    for a in attachments:
        physical_file_name = get_physical_path(a.get('file_name'))
        write_project_file_from_local_file (project, physical_file_name, PATHS['admin'])
    return

# runs on a project update (hooks)
def upload_project_file(project, event):
    pending_uploads = frappe.db.sql("""
        SELECT `name`, `project`, `file_id`, `file_url`
        FROM `tabPending File Allocation`
        WHERE `project` = "{project}"; """.format(project=project.name), as_dict=True)
    
    if len(pending_uploads) == 0:
        return
        
    for p in pending_uploads:
        physical_file_name = get_physical_path(p.get("file_id"))
        # check if this is a plan
        plan_matches = frappe.db.sql("""
            SELECT `parent`
            FROM `tabConstruction Site Description Plan`
            WHERE `parenttype` = "Project"
              AND `parent` = "{project}"
              AND `file` = "{file_url}";""".format(project=project.name, file_url=p.get("file_url")), 
              as_dict=True)
        if len(plan_matches) > 0:
            # process as plan
            write_project_file_from_local_file (project.name, physical_file_name, PATHS['plan'])
            # remove from drilling
            delete_project_file(project.name, physical_file_name, target=PATHS['drilling'])
        else:
            # check if it is a permit
            permit_matches = frappe.db.sql("""
                SELECT `parent`, `permit`
                FROM `tabProject Permit`
                WHERE `parenttype` = "Project"
                  AND `parent` = "{project}"
                  AND `file` = "{file_url}";""".format(project=project.name, file_url=p.get("file_url")), 
                  as_dict=True)
            if len(permit_matches) > 0:
                # process as permit
                # define altering target for road blocks
                if permit_matches[0].permit == "Strassensperrung":
                    target = PATHS['road']
                    write_project_file_from_local_file (project.name, physical_file_name, target)
                    # remove from drilling
                    delete_project_file(project.name, physical_file_name, target=PATHS['drilling'])
    
    # clean up
    pending_uploads = frappe.db.sql("""
        DELETE
        FROM `tabPending File Allocation`
        WHERE `project` = "{project}"; """.format(project=project.name))
        
    return
    
def get_file_id(project, event, subtable, url=None):
    if not url:
        if subtable == "plans":
            url = project.plans[-1].file
        elif subtable == "permits":
            url = project.permits[-1].file
    sql_query = frappe.db.sql("""
        SELECT `name`
        FROM `tabFile`
        WHERE `file_url` = '{0}'""".format(url), as_dict=True)
    if len(sql_query) > 0:
        file_id = sql_query[0]['name']
        return file_id
    else:
        return None
