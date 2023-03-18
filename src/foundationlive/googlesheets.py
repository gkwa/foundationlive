import csv
import os
import pathlib

import gspread
import gspread.exceptions
import oauth2client.service_account


def get_var(keyname: str):
    value = os.getenv(keyname, None)
    if not value:
        raise ValueError(keyname)
    return value


workbook_name = get_var("FOUNDATIONLIVE_GOOGLESHEETS_WORKBOOK_NAME")
creds_fname = get_var("FOUNDATIONLIVE_GOOGLESHEETS_AUTH_JSON_FILENAME")
csv_path = pathlib.Path("view_csv.csv")
creds_path = pathlib.Path(creds_fname)


def main():
    credentials_path = creds_path

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
        body={"values": list(csv.reader(open(csv_path)))},
    )


if __name__ == "__main__":
    main()
