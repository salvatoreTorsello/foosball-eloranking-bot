import os
import requests
from datetime import datetime
from xml.etree import ElementTree
from bot.config import DB_PATH
from threading import Event
from time import sleep
from bot.services.db import Database

CLOUD_URI = os.getenv('CLOUD_URI') + '/remote.php/dav/files/' + os.getenv('CLOUD_USERNAME')
CLOUD_USERNAME = os.getenv('CLOUD_USERNAME')
CLOUD_PASSWORD = os.getenv('CLOUD_PASSOWRD')
CLOUD_BACKUP_DIR = os.getenv('CLOUD_BACKUP_DIR')


def upload() -> tuple:
    """Uploads a backup of the database to NextCloud.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # WebDAV path for the backup directory
    backup_dir_url = f"{CLOUD_URI}/{CLOUD_BACKUP_DIR}"

    # Ensure the directory exists; if not, create it
    try:
        response = requests.request('PROPFIND', backup_dir_url, auth=(CLOUD_USERNAME, CLOUD_PASSWORD), headers={'Depth': '1'})
        if response.status_code != 207:
            # If the directory doesn't exist, create it
            mkcol_response = requests.request('MKCOL', backup_dir_url, auth=(CLOUD_USERNAME, CLOUD_PASSWORD))
            if mkcol_response.status_code not in [201, 405]:  # 405 if it already exists
                return False, f"Error creating directory '{CLOUD_BACKUP_DIR}': {mkcol_response.status_code}"
    except Exception as e:
        return False, f"Error creating or accessing directory '{CLOUD_BACKUP_DIR}': {e}"

    # Upload the file
    try:
        remote_file_path = f"{backup_dir_url}/foosball_{datetime.now().isoformat()}.db"
        with open(DB_PATH, 'rb') as f:
            upload_response = requests.put(remote_file_path, data=f, auth=(CLOUD_USERNAME, CLOUD_PASSWORD))
        if upload_response.status_code in [201, 204]:  # 201 Created or 204 No Content for overwrite
            return True, f"File '{DB_PATH}' uploaded successfully to '{remote_file_path}'."
        else:
            return False, f"Failed to upload file '{DB_PATH}'. Status code: {upload_response.status_code}"
    except Exception as e:
        return False, f"Failed to upload file '{DB_PATH}': {e}"


def upload_th(stop: Event) -> None:
    """Thread function which performs database file backup every
    12 hours in thread safe approach.

    Args:
        stop (): lamba function to stop the thread
    """

    db = Database()
    while not stop.is_set():
        db.acquire_lock()
        success, result = upload()
        db.release_lock()
        print(f"Backup upload thread: {result}")    
        stop.wait(timeout=12*60*60)


def download_latest() -> tuple:
    """Downloads the latest backup of the database from NextCloud.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # WebDAV path for the backup directory
    backup_dir_url = f"{CLOUD_URI}/{CLOUD_BACKUP_DIR}"

    try:
        # List files in the directory using WebDAV PROPFIND
        response = requests.request('PROPFIND', backup_dir_url, auth=(CLOUD_USERNAME, CLOUD_PASSWORD), headers={'Depth': '1'})
        if response.status_code != 207:
            return False, f"Failed to list directory contents. Status code: {response.status_code}"

        # Parse the XML response to find file names
        tree = ElementTree.fromstring(response.content)
        files = []
        for elem in tree.findall('{DAV:}response'):
            href = elem.find('{DAV:}href').text
            isdir = elem.find('{DAV:}propstat/{DAV:}prop/{DAV:}resourcetype/{DAV:}collection') is not None
            if not isdir:
                file_name = os.path.basename(href)
                files.append(file_name)

        # Sort files alphabetically and get the latest one
        files.sort()
        latest_file = files[-1] if files else None

        if latest_file:
            # Prepare the download URL and local path
            download_url = f"{backup_dir_url}/{latest_file}"
            
            # Download the latest file
            download_response = requests.get(download_url, auth=(CLOUD_USERNAME, CLOUD_PASSWORD))
            if download_response.status_code == 200:
                with open(DB_PATH, 'wb') as f:
                    f.write(download_response.content)
                return True, f"File '{latest_file}' downloaded successfully to '{DB_PATH}'."
            else:
                return False, f"Failed to download file '{latest_file}'. Status code: {download_response.status_code}"
        else:
            return False, "No files found in the backup directory."

    except Exception as e:
        return False, f"Error retrieving or downloading file: {e}"
