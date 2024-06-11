import datetime

class Stacja:
    """
    Reprezentuje stację pomiarową.

    """

    def __init__(self, id: int, latitude: float, longitude: float, miasto: str, ulica: str, nazwa: str):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.miasto = miasto
        self.ulica = ulica
        self.nazwa = nazwa

class Sensor:
    """
    Reprezentuje sensor pomiarowy.
    """

    def __init__(self, id: int, typ: str):
        self.id = id
        self.typ = typ

class Odczyt:
    """
    Reprezentuje pojedynczy odczyt z sensora.
    """

    def __init__(self, data: datetime, wartosc: float):
        self.data = data
        self.wartosc = wartosc
