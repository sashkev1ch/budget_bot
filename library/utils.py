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


def i_execute(func):

    # passing self, because functions from classes
    def execute_with_exception(self, *args, **kwargs):
        err = None
        try:
            result = func(self, *args, **kwargs)
        except Exception as error:
            print(f"decorator: function: {func.__name__} exception: {error}")
            result = None
            err = error

        return result, err

    return execute_with_exception
