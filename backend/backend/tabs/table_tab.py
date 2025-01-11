import dataclasses
import json
from typing import Any, Callable, Iterator, Literal, Optional

import pandas as pd
from backend.tabs.tabs import Tab
from backend.utils.environment_variables import EnvironmentVariableManager
from stravalib.model import DetailedActivity

ColumnTypes = Literal["string", "link"]


@dataclasses.dataclass
class LinkCell:
    url: str
    text: str


class TableTab(Tab):
    def __init__(
        self,
        name: str,
        detailed: bool,
        description: str,
        table_function: Optional[
            Callable[[Iterator[DetailedActivity]], pd.DataFrame]
        ] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, detailed, **kwargs)
        self.description = description
        self.table_function = table_function

    def get_table_dataframe(
        self, activities: Iterator[DetailedActivity]
    ) -> pd.DataFrame:
        if self.table_function is None:
            raise Exception("Table tab has no function to generate a table.")
        return self.table_function(activities)

    def get_table_column_types(self) -> dict[str, ColumnTypes]:
        return {}

    def has_column_headings(self):
        return True

    def get_columns(self, df: pd.DataFrame) -> list[dict[str, str]]:
        column_types = self.get_table_column_types()

        # Default column types are "string" for all columns UNLESS there is a
        # single instance of a LinkCell in that column.
        cols: list[dict[str, str]] = []
        for col in df.columns:
            col_type = "string"
            if any(isinstance(obj, LinkCell) for obj in df[col]):
                col_type = "link"

            cols.append(
                {"column_name": col, "column_type": column_types.get(col, col_type)}
            )

        return cols

    def get_table_data(self, activities: Iterator[DetailedActivity]) -> dict[str, Any]:
        df = self.get_table_dataframe(activities)

        def serialise_linkcells(
            linkcell: Optional[LinkCell],
        ) -> Optional[dict[str, Any]]:
            if linkcell is not None:
                return dataclasses.asdict(linkcell)
            else:
                return None

        columns = self.get_columns(df)
        for column_dict in columns:
            column_name = column_dict["column_name"]
            column_type = column_dict["column_type"]
            if column_type == "link":
                df[column_name] = df[column_name].apply(serialise_linkcells)

        return {
            "table_data": df.to_dict(orient="list"),
            "show_headings": self.has_column_headings(),
            "columns": columns,
        }

    def get_type(self) -> str:
        return "table_tab"

    def retrieve_frontend_data(
        self, evm: EnvironmentVariableManager, athlete_id: int
    ) -> Any:
        # table_string = get_object(athlete_id, self.get_key(), "table.json")
        # return json.loads(table_string)
        return ""

    def backend_processing_hook(
        self,
        activity_iterator: Iterator[DetailedActivity],
        evm: EnvironmentVariableManager,
        athlete_id: int,
    ) -> None:
        # If we aren't using S3, just leave it for the frontend hook to generate.
        table_data = self.get_table_data(activity_iterator)
        table_json_string = json.dumps(table_data)

        raise NotImplementedError
        # save_table_json(athlete_id, self.get_key(), table_json_string)
