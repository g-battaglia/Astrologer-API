from kerykeion import KrInstance
from json import loads


def filtrateAndGetDict(user: KrInstance):
    """
    This function is used to filter the data from the KrInstance object.

    Args:
        user (KrInstance): The KrInstance object to be filtered.

    Returns:
        dict: The filtered data.
    """
    return loads(user.json(dump=False))
