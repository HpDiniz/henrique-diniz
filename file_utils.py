from typing import Any
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
