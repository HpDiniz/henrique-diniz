import os
import zipfile
from typing import Any, List
from RPA.Excel.Files import Files


class FileUtils(Files):
    """
    Extends Files functionality with additional file manipulation utilities.
    """

    def __init__(self):
        """
        Initializes FileUtils by invoking the constructor of the base class Files.
        """
        super().__init__()

    def create_excel_file_from_json(self, json: Any, path: str, tab_name: str = 'Result'):
        """
        Creates an Excel file from a JSON object.

        This method creates a new Excel file at the specified path and writes the JSON data
        into a worksheet with the given tab name.

        Args:
            json (Any): JSON data to be written to the Excel file.
            path (str): Path where the Excel file will be created.
            tab_name (str, optional): Name of the worksheet/tab where the JSON data will be written. Defaults to 'Result'.

        Returns:
            None
        """

        self.create_workbook(path=path)
        self.create_worksheet(name=tab_name, content=json, header=True)
        self.save_workbook(path=path)

    def create_zip_from_files(self, zip_path: str, files: List):

        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for file in files:
                zip_file.write(file, os.path.basename(file))

    def delete_files_from_folder(self, path: str):
        """
        Deletes all files within a folder.

        Args:
        - path (str): The path to the folder.

        Returns:
            None
        """

        if not os.path.isdir(path):
            return

        files = os.listdir(path)

        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def delete_file(self, path: str):
        """
        Delete a file from the file system.

        Args:
            path (str): The path to the file to be deleted.

        Returns:
            None
        """
        os.remove(path)

    def get_megabytes_size_of_directory(self, path: str) -> float:
        """
        Calculate the total size of a directory in megabytes.

        Args:
            path (str): The path to the directory.

        Returns:
            float: The total size of the directory in megabytes.
        """
        total_size_bytes = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size_bytes += os.path.getsize(filepath)
        total_size_mb = total_size_bytes / (1024 * 1024)
        return total_size_mb
