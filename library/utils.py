from datetime import datetime, date
import xlsxwriter


def make_excel(file_path, data):
    x_book = xlsxwriter.Workbook(file_path)
    x_sheet = x_book.add_worksheet()
    try:
        for row, data_row in enumerate(data, 0):
            for col, value in enumerate(data_row):
                if isinstance(value, datetime):
                    value = value.strftime('%d-%m-%Y %H:%M:%S')
                    x_sheet.write(row, col, value)
                x_sheet.write(row, col, value)
    except Exception as err:
        print(err)

    x_book.close()
