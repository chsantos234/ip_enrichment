from pycti import OpenCTIApiClient, StixCyberObservable
from ip_enrichment.config import (
    OPENCTI_URL,
    OPENCTI_TOKEN
)


class OpenCTIManager:
    def __init__(self):
        self.client = OpenCTIApiClient(
            url=OPENCTI_URL,
            token=OPENCTI_TOKEN
        )

        self.observable = StixCyberObservable(self.client)

    ########################
    # ------- Client -------
    ########################

    def post_label(self,
        label_value: str,
        label_color: str
    ) -> dict | None:
        """
        Create a label in OpenCTI.
        """
        return self.client.label.create(
            value=label_value,
            color=label_color
        )
    

    ########################
    # ---- Observables ----
    ########################

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

    def get_observable_by_value(self, #TODO: fix
        value: str
    ) -> dict | None:
        """
        Retrieve observable by value.
        """
        return self.observable.read(
            filters=[{"key": "value", "values": [value]}]
        )

    def get_observable_by_stix_id(self,
        stix_id: str
    ) -> dict | None:
        """
        Retrieve observable by STIX ID.
        """
        return self.observable.read(
            id=stix_id
        )