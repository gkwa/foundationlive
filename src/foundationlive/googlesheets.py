import csv
import pathlib

import gspread
import gspread.exceptions
import oauth2client.service_account

creds_fname = "foundationlive-381012-3f86434e1aa2.json"
workbook_name = "Copy of streambox / taylor / timesheet"
csv_path = pathlib.Path("/Users/mtm/pdev/taylormonacelli/foundationlive/view_csv.csv")

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
