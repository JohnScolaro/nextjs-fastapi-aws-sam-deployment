import os
import shutil
from typing import Any, Callable, Iterator

from backend.tabs.tabs import Tab
from backend.utils.environment_variables import EnvironmentVariableManager
from stravalib.model import DetailedActivity

Image = Any


class ImageTab(Tab):
    def __init__(
        self,
        name: str,
        detailed: bool,
        description: str,
        create_images_function: Callable[[Iterator[DetailedActivity], str], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(name, detailed, **kwargs)
        self.description = description
        self.create_images_function = create_images_function

    def get_plot_function(self) -> Callable[[Iterator[DetailedActivity], str], None]:
        return self.create_images_function

    def get_type(self) -> str:
        return "plot_tab"

    def get_local_image_path(self) -> str:
        return os.path.join(os.getcwd(), "local_image_dir", self.get_key())

    def retrieve_frontend_data(
        self, evm: EnvironmentVariableManager, athlete_id: int
    ) -> Any:
        raise NotImplementedError

    def backend_processing_hook(
        self,
        activity_iterator: Iterator[DetailedActivity],
        evm: EnvironmentVariableManager,
        athlete_id: int,
    ) -> None:
        # Create a directory:
        path = self.get_local_image_path()
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            # Make the images
            self.create_images_function(activity_iterator, path)
            # Add the images to an S3 bucket.
            files = os.listdir(path)
            for file in files:
                # upload_file(athlete_id, self.get_key(), os.path.join(path, file))
                a = 1

        except Exception as e:
            # Ensure that if there is an error, the tmp file gets removed anyway.
            shutil.rmtree(path)
            raise e
