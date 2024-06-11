import sqlite3

import datetime

import requests

from abc import ABC, abstractmethod

from Modele import Stacja, Sensor, Odczyt

class Serwis(ABC):

    @abstractmethod
    def stacje(self) -> list[Stacja]:
        """
        Pobiera listę stacji.

        """
        pass

    @abstractmethod
    def sensory(self, stacjaId: int) -> list[Sensor]:
        """
        Pobiera listę sensorów dla danej stacji.
        """
        pass

    @abstractmethod
    def odczyty(self, sensorId: int) -> list[Odczyt]:
        """
        Pobiera listę odczytów dla danego sensora.
        """
        pass

class GIOS(Serwis):
    """
    Implementacja serwisu GIOS.
    """

    def stacje(self) -> list[Stacja]:
        """
        Pobiera listę stacji z serwisu GIOS.
        """

        json = requests.get('https://api.gios.gov.pl/pjp-api/rest/station/findAll').json()

        return [Stacja(int(_["id"]), float(_["gegrLat"]), float(_["gegrLon"]), _["city"]["name"], _["addressStreet"],_['stationName']) for _ in json]

    def sensory(self, stacjaId: int) -> list[Sensor]:
        """
        Pobiera listę sensorów dla danej stacji z serwisu GIOS.
        """

        json = requests.get(f'https://api.gios.gov.pl/pjp-api/rest/station/sensors/{stacjaId}').json()

        if not json.__str__().strip(): return []

        return [Sensor(int(_["id"]), _["param"]["paramCode"]) for _ in json]

    def odczyty(self, sensorId: int) -> list[Odczyt]:
        """
        Pobiera listę odczytów dla danego sensora z serwisu GIOS.
        """

        json = requests.get(f'https://api.gios.gov.pl/pjp-api/rest/data/getData/{sensorId}').json()

        if not json["key"] or not json["values"]: return []

        return [Odczyt(datetime.datetime.strptime(_["date"], "%Y-%m-%d %H:%M:%S"), float(_["value"])) for _ in [_ for _ in json["values"] if _['value'] is not None]]

class DB(Serwis):
    """
    Implementacja lokalnej bazy danych.
    """

    PLIK = 'Offline.db'

    def stacje(self) -> list[Stacja]:
        """
        Pobiera listę stacji z lokalnej bazy danych.
        """

        return [Stacja(*_) for _ in self.__fetch__('Stacja')]

    def sensory(self, stacjaId: int) -> list[Sensor]:
        """
        Pobiera listę sensorów dla danej stacji z lokalnej bazy danych.
        """

        return [Sensor(int(_[0]), _[2]) for _ in self.__fetch__('Sensor') if int(_[1]) == stacjaId]

    def odczyty(self, sensorId: int) -> list[Odczyt]:
        """
        Pobiera listę odczytów dla danego sensora z lokalnej bazy danych.
        """

        return [Odczyt(datetime.datetime.strptime(str(_[0]).split(';')[1], "%Y-%m-%d %H:%M:%S"), float(_[1])) for _ in self.__fetch__('Odczyt') if int(str(_[0]).split(';')[0]) == sensorId]

    def zapisz(self, stacja: Stacja, sensor: Sensor, odczyty: list[Odczyt]):
        """
        Zapisuje dane do lokalnej bazy danych.
        """
        with sqlite3.connect(DB.PLIK) as db:
            try: db.execute('''INSERT INTO Stacja (id, latitude, longitude, miasto, ulica, nazwa) VALUES (?, ?, ?, ?, ?, ?)''', (stacja.id, stacja.latitude, stacja.longitude, stacja.miasto, stacja.ulica, stacja.nazwa))
            except: pass # nieistotne, stacja może już istnieć w bazie, szybciej tak niż sprawdzać czy istnieje

            try: db.execute('''INSERT INTO Sensor (id, stacja_id, typ) VALUES (?, ?, ?)''', (sensor.id, stacja.id, sensor.typ))
            except: pass # nieistotne, sensor może już istnieć w bazie, szybciej tak niż sprawdzać czy istnieje

            for _ in odczyty:
                try:db.cursor().execute('''INSERT INTO Odczyt (sensor_id_oraz_data, wartosc) VALUES (?, ?)''', (f'{sensor.id};{_.data.strftime("%Y-%m-%d %H:%M:%S")}', _.wartosc))
                except: pass # nieistotne, dane mogą już istnieć w bazie, szybciej tak niż sprawdzać czy istnieją

            db.commit()

    def __fetch__(self, tabela: str) -> list:
        """
        Pobiera dane z lokalnej bazy danych.
        """
        with sqlite3.connect(DB.PLIK) as db: return db.cursor().execute(f'select * from {tabela}').fetchall()