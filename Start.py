from collections import OrderedDict

import haversine
import customtkinter
import tkintermapview

from geopy import Nominatim
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import Serwisy

TRYB_ONLINE = 'Online'
TRYB_OFFLINE = 'Offline'

CACHE = [
    None,   # Serwis
    None,   # Stacje
    None,   # Sensory
    None,   # Miasto    - uzytkownik
    None,   # Promien   - uzytkownik
    None,   # Stacja    - uzytkownik
    None,   # Sensor    - uzytkownik
]

def tryb_callback(wartosc):
    CACHE[0] = Serwisy.GIOS() if wartosc == TRYB_ONLINE else Serwisy.DB()
    komunikatLabel.configure(text='Online - dane pobierane z GIOS' if wartosc is TRYB_ONLINE else 'Offline - dane historyczne (DB)', bg_color='green' if wartosc is TRYB_ONLINE else 'darkred')
    trybSegmentedButton.set(wartosc)

def promien_callback(value):
    promienLabel.configure(text=f'{int(value)} km')
    CACHE[4] = int(promienSlider.get())

def szukaj_callback():
    CACHE[3] = szukajTextbox.get("1.0", customtkinter.END).strip()

    if not CACHE[3]: return

    try: CACHE[1] = CACHE[0].stacje()
    except:
        sugeruj_offline()
        return

    CACHE[5] = CACHE[6] = None

    odswiez_widok()

def stacja_callback(wartosc):
    if not wartosc: return

    CACHE[5] = next((_ for _ in CACHE[1] if _.nazwa == wartosc), None)

    CACHE[2] = CACHE[0].sensory(CACHE[5].id)

    pomiarComboBox.configure(values=[_.typ for _ in CACHE[2]])

def pomiar_callback(wartosc):
    if not wartosc: return

    CACHE[6] = next((_ for _ in CACHE[2] if _.typ == wartosc), None)

def sugeruj_offline():
    okno = customtkinter.CTkToplevel(master=app, fg_color='darkred')
    okno.title(f'Błąd ... ')
    okno.resizable(False, False)

    def offline_callback():
        okno.destroy()
        okno.update()

        tryb_callback(TRYB_OFFLINE)

    wiadomoscLabel = customtkinter.CTkLabel(master=okno, text='Coś poszło nie tak ...', fg_color='darkred')
    wiadomoscLabel.grid(row = 0, column = 0, padx = 90, pady = 60, sticky = 'w')

    offlineButton = customtkinter.CTkButton(master=okno, text='przejdź do Offline', fg_color='black', command=offline_callback)
    offlineButton.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = 's')

    okno.grab_set()
    okno.focus_set()

    okno.bell()

def raport_callback():
    if not CACHE[5] or not CACHE[6]: return

    dane = {_.data : _.wartosc for _ in CACHE[0].odczyty(CACHE[6].id)}
    dane = OrderedDict(reversed(list(dane.items())))

    def generuj_wykres(fig, ax, daneX, daneY):
        ax.clear()
        ax.plot(daneX, daneY, marker='o')
        fig.patch.set_facecolor('#242424')
        ax.set_facecolor('#242424')
        for text_obj in ax.get_xticklabels() + ax.get_yticklabels():
            text_obj.set_color('white')
        ax.spines['bottom'].set_color('#242424')
        ax.spines['top'].set_color('#242424')
        ax.spines['left'].set_color('#242424')
        ax.spines['right'].set_color('#242424')
        ax.tick_params(axis='x', colors='#242424')
        ax.tick_params(axis='y', colors='white')

        canvas.draw()

    def zakres_callback(_):
        od = int(odSlider.get())
        do = int(doSlider.get())

        generuj_wykres(fig, ax, list(dane.keys())[od:do], list(dane.values())[od:do])

        zakresLabel.configure(text=f'{list(dane.keys())[od]} ~ {list(dane.keys())[do]}')

    def zapisz_callback():
        Serwisy.DB().zapisz(CACHE[5], CACHE[6], CACHE[0].odczyty(CACHE[6].id))
        zapiszButton.configure(fg_color='darkgreen', state=customtkinter.DISABLED)

    okno = customtkinter.CTkToplevel(master=app)
    okno.title(f' {CACHE[5].nazwa} : {CACHE[6].typ}')
    okno.resizable(False, False)

    fig, ax = plt.subplots(figsize=(12, 8))

    canvas = FigureCanvasTkAgg(fig, master=okno)
    canvas.get_tk_widget().grid(row = 0, column = 0, sticky='nsew')

    okno.grab_set()
    okno.focus_set()

    zapiszButton = customtkinter.CTkButton(master=okno, text='💾 Zapisz (DB)', command=zapisz_callback)
    if isinstance(CACHE[0], Serwisy.GIOS): zapiszButton.grid(row = 0, column = 0, padx=20, sticky = 'ne')

    odSlider = customtkinter.CTkSlider(master=okno, from_=0, to=len(dane.items()) - 1, width=40, button_color='white', button_hover_color='white')
    odSlider.grid(row = 0, column = 0, padx = 20, pady = 10, sticky = 'sw')
    odSlider.set(0)

    zakresLabel = customtkinter.CTkLabel(master=okno, text='')
    zakresLabel.grid(row = 0, column = 0, padx = 20, pady = 0, sticky = 's')

    doSlider = customtkinter.CTkSlider(master=okno, from_=0, to=len(dane.items()) - 1, width=40, button_color='white', button_hover_color='white')
    doSlider.grid(row=0, column=0, padx = 20, pady = 10, sticky = 'se')
    doSlider.set(len(dane.items()))

    odSlider.configure(command=zakres_callback)
    doSlider.configure(command=zakres_callback)

    zakres_callback(None)

def odswiez_widok():
    stacjaComboBox.set('')
    pomiarComboBox.set('')
    mapaMapView.delete_all_marker()

    stacje = []

    if isinstance(CACHE[0], Serwisy.GIOS):
        try:
            centrumMiasta = Nominatim(user_agent='http').geocode(CACHE[3])
        except:
            sugeruj_offline()
            return

        centrumMiastaLat = float(centrumMiasta.latitude)
        centrumMiastaLng = float(centrumMiasta.longitude)

        stacje = [_ for _ in CACHE[1] if _.miasto == CACHE[3] or haversine.haversine((centrumMiastaLat, centrumMiastaLng),(_.latitude, _.longitude), unit=haversine.Unit.KILOMETERS) <= (CACHE[4] if CACHE[4] else 0)]
    else:
        stacje = [_ for _ in CACHE[1] if _.miasto == CACHE[3]]

    stacjaComboBox.configure(values=[_.nazwa for _ in stacje])
    pomiarComboBox.configure(values=[''])

    [mapaMapView.set_marker(_.latitude, _.longitude, text=_.nazwa) for _ in stacje]

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.title(' Pomiary (Agata Jaworska)')
app.resizable(False, False)

konfiguracjaFrame = customtkinter.CTkFrame(master=app)
konfiguracjaFrame.grid(row=0, column=0)

trybLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='Tryb')
trybLabel.grid(row=0, column=0, padx= 20, pady= 20, sticky='w')

trybSegmentedButton = customtkinter.CTkSegmentedButton(master=konfiguracjaFrame, values=[TRYB_ONLINE, TRYB_OFFLINE], command=tryb_callback)
trybSegmentedButton.grid(row=0, column=1, padx= 20, pady= 20, sticky='we')
trybSegmentedButton.set('Online')

komunikatLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='')
komunikatLabel.grid(row=1, column=0, columnspan=2, padx= 0, pady= 20, sticky='we')

szukajLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='Szukaj')
szukajLabel.grid(row=2, column=0, padx= 20, pady= 20, sticky='w')

szukajTextbox = customtkinter.CTkTextbox(master=konfiguracjaFrame, height=szukajLabel.winfo_height())
szukajTextbox.grid(row=2, column=1, padx= 20, pady= 20, sticky='w')

szukajButton = customtkinter.CTkButton(master=szukajTextbox, text='🔍', width=30, corner_radius=0, command=szukaj_callback)
szukajButton.place(relx = 1, rely = 0.5, anchor = 'e')

promienLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='0 km')
promienLabel.grid(row=4, column=0, padx= 20, pady= 20, sticky='w')

promienSlider = customtkinter.CTkSlider(master=konfiguracjaFrame, from_=0, to=90, command=promien_callback)
promienSlider.grid(row=4, column=1, padx= 20, pady= 20, sticky='we')
promienSlider.set(0)

stacjaLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='Stacja')
stacjaLabel.grid(row=5, column=0, padx= 20, pady= 20, sticky='w')

stacjaComboBox = customtkinter.CTkComboBox(master=konfiguracjaFrame, values=[''], command=stacja_callback)
stacjaComboBox.grid(row=5, column=1, padx=20, pady=20, sticky='we')

pomiarLabel = customtkinter.CTkLabel(master=konfiguracjaFrame, text='Pomiar')
pomiarLabel.grid(row=6, column=0, padx= 20, pady= 20, sticky='w')

pomiarComboBox = customtkinter.CTkComboBox(master=konfiguracjaFrame, values=[''], command=pomiar_callback)
pomiarComboBox.grid(row=6, column=1, padx=20, pady=20, sticky='we')

mapaMapView = tkintermapview.TkinterMapView(app, width=konfiguracjaFrame.winfo_width() * 2)
mapaMapView.grid(row=0, column=1, sticky='nsew')
mapaMapView.set_position(51.6874541, 19.633368)
mapaMapView.set_zoom(7)

raportButton = customtkinter.CTkButton(master=app, text='Raport', state=customtkinter.NORMAL, bg_color='red', fg_color='black', text_color='white', command=raport_callback)
raportButton.grid(row = 0, column = 1, padx= 20, pady= 20, sticky= 's')

app.wm_attributes('-transparentcolor','red')

tryb_callback(TRYB_ONLINE)

app.mainloop()