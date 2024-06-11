import datetime
import os.path
import sqlite3
import unittest

from Serwisy import GIOS, Stacja, Sensor, Odczyt, DB


class TestGIOS(unittest.TestCase):
    """
    Klasa zawierająca testy dla klasy GIOS.
    """

    def setUp(self):
        """
        Metoda konfigurująca testy.
        """
        self.gios = GIOS()

    def test_stacje(self):
        """
        Testuje funkcję stacje() klasy GIOS.
        """
        stacje = self.gios.stacje()

        self.assertTrue(len(stacje) > 0)
        self.assertFalse(any(_.miasto == '' for _ in stacje))

    def test_sensory(self):
        """
        Testuje funkcję sensory(id_stacji) klasy GIOS.
        """
        sensory = self.gios.sensory(515)

        self.assertTrue(len(sensory) > 0)
        self.assertFalse(any(_.typ == '' for _ in sensory))

    def test_odczyty(self):
        """
        Testuje funkcję odczyty(id_sensora) klasy GIOS.
        """
        odczyty = self.gios.odczyty(3492)

        self.assertTrue(len(odczyty) > 0)
        self.assertFalse(any(isinstance(_.data, datetime.datetime) == False for _ in odczyty))

class TestDB(unittest.TestCase):
    """
    Klasa zawierająca testy dla klasy DB.
    """

    TEST_STACJA = Stacja(-1, -1.99, -1.99, 'Miasto', 'Ulica', 'Miasto, Ulica')
    TEST_SENSOR = Sensor(-1, 'Sensor')
    TEST_ODCZYT = Odczyt(datetime.datetime.now(), -1.99)

    def setUp(self):
        """
        Metoda konfigurująca testy.
        """
        self.db = DB()

    def test(self):
        """
        Testuje funkcje klasy DB.
        """
        self.assertTrue(os.path.exists(DB.PLIK))

        komunikacja = True

        try:
            self.db.__fetch__("Stacja")
        except:
            komunikacja = False

        self.assertTrue(komunikacja)

        self.db.zapisz(TestDB.TEST_STACJA, TestDB.TEST_SENSOR, [TestDB.TEST_ODCZYT])

        try:
            stacje = self.db.stacje()
            sensory = self.db.sensory(TestDB.TEST_STACJA.id)
            odczyty = self.db.odczyty(TestDB.TEST_SENSOR.id)

            self.assertTrue(any(_.id == TestDB.TEST_STACJA.id for _ in stacje))
            self.assertTrue(any(_.id == TestDB.TEST_SENSOR.id for _ in sensory))
            self.assertTrue(any(_.wartosc == TestDB.TEST_ODCZYT.wartosc for _ in odczyty))
        finally:
            with sqlite3.connect(DB.PLIK) as db:
                self.assertTrue(db.execute(f'delete from Stacja where id={TestDB.TEST_STACJA.id}').rowcount)
                self.assertTrue(db.execute(f'delete from Sensor where id={TestDB.TEST_SENSOR.id}').rowcount)
                self.assertTrue(db.execute(f'delete from Odczyt where wartosc={TestDB.TEST_ODCZYT.wartosc}').rowcount)
