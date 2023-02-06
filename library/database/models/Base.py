from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import inspect
Base = declarative_base()


# class Base(DeclarativeBase):
#     abstract = True
#
#     def __str__(self):
#         model = self.__class__.name
#         table = inspect(self.__class__)
#         primary_key_columns = table.primary_key.columns
#         values = {
#             column.name: getattr(self, self._column_name_map[column.name])
#             for column in primary_key_columns
#         }
#         values_str = " ".join(
#             f"{name}={value!r}" for name, value in values.items())
#         return f"<{model} {values_str}>"
