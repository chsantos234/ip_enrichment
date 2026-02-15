from pycti import OpenCTIApiClient, StixCyberObservable
from dotenv import dotenv_values


class OpenCTIManager:
    def __init__(self, env_path: str = ".env"):
        config = dotenv_values(env_path)

        self.client = OpenCTIApiClient(
            url=config["OPENCTI_URL"],
            token=config["OPENCTI_TOKEN"]
        )

        self.observable = StixCyberObservable(self.client)


    def post_label(self,
        label_value: str,
        label_color: str
    ) -> dict:
        """
        Create a label in OpenCTI.
        """
        return self.client.label.create(
            value=label_value,
            color=label_color
        )


    def put_observable(self,
        observable_input: dict,
        labels: list[str] | None = None,
        update: bool = True
    ) -> dict | None:
        """
        Create or update an observable.
        """
        return self.observable.create(
            observableData=observable_input,
            objectLabel=labels or [],
            update=update
        )


    def get_observable_by_value(self,
        value: str
    ) -> dict | None:
        """
        Retrieve observable by value.
        """
        return self.observable.read(
            filters=[{"key": "value", "values": [value]}]
        )
