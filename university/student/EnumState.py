from enum import Enum


class StateModelEnum(Enum):
    # TODO Refactor the state model to use Enum, instead of strings for better readability and maintainability
    CONNECTION_INVITATION = "CONNECTION INVITATION"
    OFFER_SENT = "OFFER SENT"
    CREDENTIAL_ISSUED = "CREDENTIAL ISSUED"
    # Add other states as needed
