import csv
import pathlib

import gspread
import gspread.exceptions
import oauth2client.service_account

from . import config as configmod

workbook_name = configmod.config["FOUNDATIONLIVE_GOOGLESHEETS_WORKBOOK_NAME"]
credentials_path = pathlib.Path(
    pathlib.Path(configmod.config["FOUNDATIONLIVE_GOOGLESHEETS_AUTH_JSON_FILE_PATH"])
)


def main(csv_file):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = (
        oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scopes
        )
    )
    client = gspread.authorize(creds)
    workbook = client.open(workbook_name)
    sheet_title = "sheet1"

    workbook.values_update(
        sheet_title,
        params={"valueInputOption": "USER_ENTERED"},
        body={"values": list(csv.reader(csv_file.splitlines()))},
    )


if __name__ == "__main__":
    main()
