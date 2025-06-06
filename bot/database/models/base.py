import datetime
from typing import Annotated

from sqlalchemy import text, ARRAY, Integer, BigInteger
from sqlalchemy.orm import DeclarativeBase, mapped_column, declarative_base

int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True, unique=True, autoincrement=False)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


class Base(DeclarativeBase):
    repr_cols_num: int = 3  # print first columns
    repr_cols: tuple = ()  # extra printed columns

    type_annotation_map = {
        list[int]: ARRAY(Integer)
    }

    def __repr__(self) -> str:
        cols = [
            f"{col}={getattr(self, col)}"
            for idx, col in enumerate(self.__table__.columns.keys())
            if col in self.repr_cols or idx < self.repr_cols_num
        ]
        return f"<{self.__class__.__name__} {', '.join(cols)}>"
