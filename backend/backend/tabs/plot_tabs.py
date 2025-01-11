import json
from typing import Any, Callable, Iterator

import plotly
import plotly.graph_objects as go
from backend.tabs.tabs import Tab
from backend.utils.environment_variables import EnvironmentVariableManager

# from backend.utils.s3 import get_object
from stravalib.model import DetailedActivity


class PlotTab(Tab):
    def __init__(
        self,
        name: str,
        detailed: bool,
        description: str,
        plot_function: Callable[[Iterator[DetailedActivity]], go.Figure],
        **kwargs: Any,
    ) -> None:
        super().__init__(name, detailed, **kwargs)
        self.description = description
        self.plot_function = plot_function

    def get_plot_function(self) -> Callable[[Iterator[DetailedActivity]], go.Figure]:
        return self.plot_function

    def retrieve_frontend_data(
        self, evm: EnvironmentVariableManager, athlete_id: int
    ) -> Any:
        # chart_string = get_object(athlete_id, self.get_key(), "chart.json")
        chart_string = "a"
        return json.loads(chart_string)

    def backend_processing_hook(
        self,
        activity_iterator: Iterator[DetailedActivity],
        evm: EnvironmentVariableManager,
        athlete_id: int,
    ) -> None:
        # If we aren't using S3, just do nothing because it'll all happen on the frontend data retrieval hook.
        chart_data = self.get_chart_dict(activity_iterator)
        chart_json_string = json.dumps(chart_data, cls=plotly.utils.PlotlyJSONEncoder)
        raise NotImplementedError
        # save_chart_json(athlete_id, self.get_key(), chart_json_string)

    def get_chart_dict(self, activity_iterator: Iterator[DetailedActivity]) -> Any:
        fig = self.plot_function(activity_iterator)

        # Convert the chart figure to a dictionary which can be correctly serialised by flasks `jsonify`.
        # We can't just rely on jsonify, because it serialised datetimes incorrectly, so we use plotlys
        # json encoder to make a string, then read that back into a dictionary. This serialises all the
        # datetimes correctly.
        chart_json_string = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        chart_dict = json.loads(chart_json_string)
        return chart_dict

    def get_type(self) -> str:
        return "plot_tab"
