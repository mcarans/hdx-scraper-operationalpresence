import json
from logging import getLogger
from typing import Optional, Iterable, List, Tuple

import gspread
from hdx.api.configuration import Configuration

logger = getLogger(__name__)


class Sheet:
    iso3_ind = 0
    automated_dataset_ind = 1
    automated_resource_ind = 2
    automated_format_ind = 3
    dataset_ind = 4
    resource_ind = 5
    format_ind = 6
    headers = ["Country ISO3", "Automated Dataset", "Automated Resource", "Automated Format", "Dataset", "Resource", "Format", "Sheet", "Headers", "AdminLevel", "Adm Column", "Org Name Column", "Org Acronym Column", "Org Type Column", "Sector Column"]

    def __init__(self, configuration: Configuration, gsheet_auth: Optional[str] = None):
        self.configuration = configuration
        self.spreadsheet_rows = {}
        self.sheet = None
        if gsheet_auth:
            self.read_existing(gsheet_auth)

    def read_existing(self, gsheet_auth: str) -> None:
        try:
            info = json.loads(gsheet_auth)
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            gc = gspread.service_account_from_dict(info, scopes=scopes)
            logger.info("Opening operational presence datasets gsheet")
            self.spreadsheet = gc.open_by_url(
                self.configuration["spreadsheet"]
            )
            self.sheet = self.spreadsheet.get_worksheet(0)
            gsheet_rows = self.sheet.get_values()
            for row in gsheet_rows[1:]:
                countryiso3 = row[self.iso3_ind]
                self.spreadsheet_rows[countryiso3] = row
        except Exception as ex:
            logger.error(ex)

    def add_update_row(
        self, countryiso3: str, dataset_name: str, resource_name: str, resource_format: str,
    ) -> None:
        row = self.spreadsheet_rows.get(countryiso3)
        if row is None:
            row = [countryiso3, dataset_name, resource_name, resource_format]
            self.spreadsheet_rows[countryiso3] = row
        else:
            current_dataset = row[self.automated_dataset_ind]
            if current_dataset != dataset_name:
                logger.info(f"{countryiso3}: Updating dataset from {current_dataset} to {dataset_name}")
                row[self.automated_dataset_ind] = dataset_name
            current_resource = row[self.automated_resource_ind]
            if current_resource != resource_name:
                logger.info(f"{countryiso3}: Updating resource from {current_resource} to {resource_name}")
                row[self.automated_resource_ind] = resource_name
                row[self.automated_format_ind] = resource_format

    def write(self, countryiso3s: List) -> None:
        if self.sheet is None:
            return
        rows = [self.headers]
        for countryiso3 in sorted(self.spreadsheet_rows):
            row = self.spreadsheet_rows[countryiso3]
            if countryiso3 not in countryiso3s:
                row[self.automated_dataset_ind] = ""
                row[self.automated_resource_ind] = ""
            rows.append(row)
        self.sheet.clear()
        self.sheet.update("A1", rows)

    def get_countries(self) -> Iterable[str]:
        return self.spreadsheet_rows.keys()

    def get_dataset_resource(self, countryiso3: str) -> Tuple[str, str, str]:
        row = self.spreadsheet_rows[countryiso3]
        automated_dataset = row[self.automated_dataset_ind]
        dataset = row[self.dataset_ind]
        if dataset:
            logger.info(f"Using override dataset {dataset} instead of {automated_dataset} for {countryiso3}")
        else:
            dataset = automated_dataset
        automated_resource = row[self.automated_resource_ind]
        resource = row[self.resource_ind]
        if resource:
            logger.info(f"Using override resource {resource} instead of {automated_resource} for {countryiso3}")
        else:
            resource = automated_resource
        format = row[self.format_ind]
        automated_format = row[self.automated_format_ind]
        if format:
            logger.info(f"Using override format {format} instead of {automated_format} for {countryiso3}")
        else:
            format = automated_format
        return dataset, resource, format
