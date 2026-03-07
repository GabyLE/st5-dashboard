import random 
import math
import pandas as pd
import string
import ipaddress
from datetime import datetime, timedelta
import sys

EPS = 1e-9

def fix_weights(weights, label="na"):
    total = sum(weights)
    diff = 1.0 - total 
    if abs(diff) > EPS:
        print(f"WARNING: Fixed weights in dimension ({label}) with absolute delta of {diff:.2f}")
        delta = diff / len(weights) 
        for i in range(len(weights)):
            weights[i] /= total
        assert math.isclose(sum(weights), 1.0, rel_tol=EPS)

SURVEY_MAP_SECTOR = {"bran1": "Bau",
                     "bran2": "Dienstleistung",
                     "bran3": "Energie",
                     "bran4": "Gastgewerbe, Tourismus",
                     "bran5": "Handwerk",
                     "bran6": "Industrie, verarbeitendes Gewerbe",
                     "bran7": "Land- und Forstwirtschaft, Fischerei",
                     "bran8": "Transport und Verkehr"}

SURVEY_MAP_NUM_EMP = {"anzM1": "<= 10",
                      "anzM2": "<= 50",
                      "anzM3": "<= 100",
                      "anzM4": "<= 250",
                      "anzM5": "> 250"}

class NumberField:
    def __init__(self, start=0, end=sys.maxsize):
        self.start = start
        self.end = end

    def sample(self):
        result = random.randint(self.start, self.end)
        return result

class MultiOption:
    def __init__(self, options):
        self.options = options

    def sample(self):
        return random.choice(self.options)

class IncrementField:
    def __init__(self, start=0):
        self.counter = start

    def sample(self):
        result = self.counter
        self.counter += 1
        return result

class IpAddrField:
    def sample(self):
        rand_bits = random.getrandbits(32)
        ip_addr = ipaddress.IPv4Address(rand_bits)
        str_addr = str(ip_addr)
        return str_addr 

class DateField:
    def sample(self):
        start_date = datetime.now()
        rand_secs = random.randint(0, 30 * 24 * 60 * 60)
        rand_date = start_date + timedelta(seconds=rand_secs)
        str_date = rand_date.strftime("%Y-%m-%d %H:%M:%S")
        return str_date

class StringField:
    def __init__(self, length=8):
        self.length = length
        self.options = string.ascii_letters

    def sample(self):
        rand_letters = [random.choice(self.options) for _ in range(self.length)]
        rand_str = "".join(rand_letters)
        return rand_str

class LanguageField(MultiOption):
    def __init__(self):
        super().__init__(["de"])

class LikertField(MultiOption):
    def __init__(self, scale=5):
        super().__init__([i for i in range(1, scale + 1)])


class FixedField:
    def __init__(self, value):
        self.value = value

    def sample(self):
        return self.value



SURVEY_COL_SECTOR = ["In welcher Branche ist Ihr Unternehmen tätig?", 
                     "In welcher Branche ist Ihr Unternehmen tätig? [Sonstiges]",]

SURVEY_COL_NUM_EMP = "Wie viele Mitarbeitende sind in Ihrem Unternehmen beschäftigt?"
SURVEY_COL_ZIP = "Bitte geben Sie die ERSTEN ZWEI Ziffern der Postleitzahl Ihres Standortes bzw. Ihres Unternehmen an.  "

SURVEY_COL_SA_LAST_YEAR = "Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Das LETZTE Geschäftsjahr meines Unternehmens war sehr erfolgreich.]"
SURVEY_COL_SA_CURR_YEAR = "Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Das AKTUELLE Geschäftsjahr meines Unternehmens verläuft sehr erfolgreich.]"
SURVEY_COL_SA_SHORT_TERM = "Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  KURZFRISTIG sehr gut am Markt positioniert sein wird!]"
SURVEY_COL_SA_MID_TERM = "Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  MITTELFRISTIG sehr gut am Markt positioniert sein wird!]"
SURVEY_COL_SA_LONG_TERM = "Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  LANGFRISTIG sehr gut am Markt positioniert sein wird!]"


SURVEY_COLUMNS_AND_TYPES = [("Antwort ID", IncrementField()),
                            ("Datum Abgeschickt", DateField()),
                            ("Letzte Seite", FixedField(8)),
                            ("Start-Sprache", LanguageField()),
                            ("Zufallsstartwert", NumberField()),
                            ("Datum gestartet", DateField()),
                            ("Datum letzte Aktivität", DateField()),
                            ("IP-Adresse", IpAddrField()), 
                            ("Wie viele Mitarbeitende sind in Ihrem Unternehmen beschäftigt?", MultiOption(list(SURVEY_MAP_NUM_EMP.keys()))),
                            ("In welcher Branche ist Ihr Unternehmen tätig?", MultiOption(list(SURVEY_MAP_SECTOR.keys()))),
                            ("In welcher Branche ist Ihr Unternehmen tätig? [Sonstiges]", StringField(0)),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Das LETZTE Geschäftsjahr meines Unternehmens war sehr erfolgreich.]", LikertField()),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Das AKTUELLE Geschäftsjahr meines Unternehmens verläuft sehr erfolgreich.]", LikertField()),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich finde, dass unser Unternehmen AKTUELL sehr gut am Markt positioniert ist!]", LikertField()),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  KURZFRISTIG sehr gut am Markt positioniert sein wird!]", LikertField()),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  MITTELFRISTIG sehr gut am Markt positioniert sein wird!]", LikertField()),
                            ("Bitte geben Sie uns unten einen kurzen Einblick in den Erfolg Ihres Unternehmen und die Positionierung des Unternehmens im Vergleich zum Wettbewerb.  Antworten Sie hierzu bitte auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\".   [Ich bin optimistisch, dass unser Unternehmen  LANGFRISTIG sehr gut am Markt positioniert sein wird!]", LikertField()),
                            ("Bitte geben Sie die ERSTEN ZWEI Ziffern der Postleitzahl Ihres Standortes bzw. Ihres Unternehmen an.  ", NumberField(start=10, end=99)),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [Die Unternehmensführung meines Unternehmens unterstützt und fördert die digitale Transformation hin zu Industrie 5.0-Abläufen (z. B. Ressourceneffizienz-Programme, Ergonomieverbesserungsinitiativen).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [In meinem Unternehmen wird im Sinne von Industrie 5.0 eine Kultur der kontinuierlichen Verbesserung gefördert (z. B. durch digitales Ideenmanagement)]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [In meinem Unternehmen gibt es Arbeitsteams, die gezielt an der Umsetzung von Industrie 5.0-Abläufen arbeiten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [Die Mitarbeitenden meines Unternehmens verfügen über ausreichende digitale Kompetenzen zur Umsetzung von Industrie 5.0-Abläufen.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich bin mit dem Konzept von Industrie 5.0 vertraut.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich nehme die Auswirkungen wahr, die durch Industrie 5.0-Konzepte entstehen (z. B. Entlastung der Mitarbeitenden, Emissionsreduzierung, Resilienz gegenüber Lieferketten-Engpässen).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich sehe den Nutzen technologiegestützter Industrie 5.0-Abläufe für die Leistungsfähigkeit meines Unternehmens.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich fühle mich bereit, in meinem Unternehmen Technologien einzuführen, um die Abläufe im Sinne von Industrie 5.0 zu gestalten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über eine Strategie für die Digitalisierung, die auch zur Umsetzung von Industrie 5.0-Abläufen beiträgt.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über eine Roadmap für die Digitalisierung, die auch zur Umsetzung von Industrie 5.0-Abläufen beiträgt.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen berücksichtigt bei der Produkt- oder Dienstleistungsentwicklung die Bedürfnisse der Verbraucher:innen (z. B. durch Usability-Tests, Auswertung von Kundenfeedback-Daten).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen arbeitet mit externen Stakeholdern (z. B. Technologieunternehmen, Beratungsgesellschaften, Hochschulen und / oder Universitäten) zusammen, um Industrie 5.0-Abläufe zu entwickeln und umzusetzen.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen zeigt ein starkes Engagement für Nachhaltigkeit und Umweltschutz durch verantwortungsvolle Praktiken im Umgang mit natürlichen Ressourcen und bei der Reduzierung von Emissionen.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen investiert finanziell in Industrie 5.0-Abläufe (z. B. Investitionen in KI-gesteuerte Produktionslinien, Lieferketten-Monitoring-Systeme).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mit Hilfe digitaler Technologien gelingt es meinem Unternehmen, die Abläufe bei meinen Zuliefererbetrieben und Abnehmer:innen (Kund:innen) mit zu steuern, um die Erreichung resilienter und menschzentrierter Ziele zu unterstützen (z. B. gemeinsames Commitment zu ethischen Richtlinien und Transparenz in der Lieferkette).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Die Abläufe in meinem Unternehmens werden in Echtzeit überwacht und reagieren dynamisch auf Veränderungen, um die Resilienz von Produktions- oder Dienstleistungsprozessen zu fördern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt IT-gestützte Technologien für eine durchgängig nachhaltige und resiliente Planung und Steuerung (z. B. Absatzprognosen, Produktions-, Prozess-, Lager- und Logistikplanung).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt digitale Tools und Methoden ein, um Nachhaltigkeit, Resilienz und Menschzentrierung in den Abläufen zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mit Hilfe digitaler Technologien gelingt es meinem Unternehmen, mit anderen Unternehmen der gleichen Branche oder Produktionsstufe zu kooperieren, um die Erreichung resilienter und menschzentrierter Ziele zu unterstützen (z. B. gemeinsames Commitment zu ethischen Richtlinien, Transparenz, Nachhaltigkeitsziele).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Technologien zur Automatisierung und Effizienzsteigerung von Abläufen (z. B. durch automatisierte Datenauswertungen, robotergestützte Fertigung).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt Roboter zur Automatisierung von Abläufen (wie Reinigung oder Verpackung) und / oder autonome Fahrzeuge für Logistikaufgaben ein. Diese Systeme interagieren mit Menschen und der Umgebung, um Abläufe resilient und menschzentriert zu gestalten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Software, um Informationen zwischen den verschiedenen Unternehmensbereichen auszutauschen und Feedback zu erhalten, das für die Entscheidungsfindung in Abläufen relevant ist.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verwendet digitale bzw. digital lesbare Kennungen für Produktionsmittel (z. B. Produkte, Services, Teile, Werkzeuge oder Personal), um diese in den verschiedenen Bereichen des Unternehmens wie Produktionsstätten, Lager und Instandhaltung zu verfolgen. ]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt Sensoren, Aktoren und SPS-Steuerungen an Maschinen und Anlagen ein, um Abläufe nachhaltiger und resilient zu gestalten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über interoperable Kommunikationssysteme zum Informationsaustausch zwischen Maschinen, Systemen und Mitarbeitenden auf verschiedenen Hierarchieebenen mit dem Ziel, die Resilienz und Menschzentrierung  von Abläufen zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Plattformen, um in Echtzeit Informationen über die Leistung zwischen Produktions-, Servicestätten, Lieferant:innen und Lager auszutauschen und so die Abläufe im Sinne von Industrie 5.0 zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Plattformen, um mit den Kund:innen Informationen über die Leistung in Produktion oder Dienstleistung zu teilen und Unterstützung bei spezifischen Anfragen zu leisten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Augmented-Reality-Technologien, um Abläufe im Sinne von Industrie 5.0  zu verbessern (z. B. virtuelle Visualisierung von Problemen in Produktentwicklungsphasen, virtuelle Brillen zur Unterstützung der Mitarbeitenden bei Entscheidungen).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt 3D-Drucktechniken, um die Nachhaltigkeit von Abläufen zu verbessern (z. B. durch Reduzierung von Materialabfällen, Realisierung nachhaltiger Verpackungen und Senkung des Energieverbrauchs).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt mobile Geräte (z. B. Smartphones und Tablets) sowie tragbare Geräte (z. B. Smartwatches, Smartglasses und Smart Gloves), um Informationen über Abläufe abzurufen und in Echtzeit mit verschiedenen Systemen zu kommunizieren.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt fälschungssichere, digitale Datenspeicher, um die Lieferkette resilienter zu gestalten (z. B. durch Bereitstellung von Rückverfolgbarkeitsinformationen) und die Produktion zu optimieren (z. B. durch Zertifizierung von Nachhaltigkeitsindikatoren).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen erzeugt intelligente Produkte mit Sensoren und/oder Smart Services, die mit der Umgebung interagieren können, um Abläufe im Sinne von Industrie 5.0 zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Cloud-Computing-Systeme für die Fernverbindung und gemeinsame Nutzung von Hardware- (z. B. Geräte, Roboter) und Software-Ressourcen (z. B. Daten, Dokumente, Software), wodurch die Resilienz von Abläufen verbessert wird.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen speichert und ruft Informationen aus dem Cloud-Computing-Netzwerk ab, um die Resilienz von Abläufen zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Technologien für die drahtlose Kommunikation zwischen Maschinen, Robotern, IT-Systemen und Mitarbeitenden (z. B. Wi-Fi, 0.17 ZigBee und Bluetooth), die in der Lage sind, die Abläufe im Sinne von Industrie 5.0 zu verbessern.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen bietet Kund:innen und Lieferant:innen Produkte und / oder Dienstleistungen auf Basis von Webtechnologien an, die einen individuellen Mehrwert bieten (z. B. durch interaktive Kundenportale oder Produktkonfiguratoren).]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen ist in der Lage, Daten (von physischen Objekten und externen Datenquellen) in Echtzeit zu erfassen, zu speichern und zu verwalten, mit dem Ziel, technische Anlagen im Sinne von Industrie 5.0 zu verbessern.	]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Produktions- und Dienstleistungsdaten, um mögliche Szenarien zu simulieren und dabei verschiedene Lösungen (oder Probleme) in Prozessabläufen zu bewerten.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Technologien der künstlichen Intelligenz (z. B. Verarbeitung natürlicher Sprache, Spracherkennung, regelbasierte Systeme und Computer Vision), die zur Verbesserung von Produkten, Dienstleistungen und Abläufen nützlich sind.]", LikertField()),
                            ("Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt verschiedene IT-Sicherheitsmaßnahmen (z. B. Verschlüsselung, Authentifizierung und Autorisierung), die die Kommunikationssicherheit und den Datenschutz verbessern.]", LikertField()),
                            ("Gesamtzeit", NumberField(start=5 * 60, end=15 * 60)), 
                            ("Gruppenzeit: Allgemeine Fragen zum Unternehmen", NumberField(start=5 * 60, end=15 * 60)),
                            ("Fragenzeit: anzMA", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: branche", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: marktPosition", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: plz", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Menschen und Kultur für Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: menschKul", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Bewusstsein für die Prinzipien von Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: bewusstPrinz", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Digitale Strategien für Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: ustrat", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Wertschöpfungskette und Prozesse für Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: wertKette", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Intelligente Fertigungstechnologien für Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: smartTra", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Integration erweiterter technologischer Komponenten in die Abläufe und das Angebot Ihres Unternehmens", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: techProd", NumberField(start=5 * 60, end=15*60)),
                            ("Gruppenzeit: Nutzung etablierter digitaler Technologien für Industrie 5.0", NumberField(start=5 * 60, end=15*60)),
                            ("Fragenzeit: nutzEtabDigTech", NumberField(start=5 * 60, end=15*60))]

MM_ORIGINAL_DIM_NAMES = ["People and culture",
                         "Awareness on I5.0 production",
                         "Organizational strategy",
                         "Value chain and processes",
                         "Smart manufacturing technology",
                         "Technology based products and services",
                         "Industry 4.0 technologies"]

MM_DIM_NAMES = ["Menschen und Kultur für Industrie 5.0",
                "Bewusstsein für die Prinzipien von Industrie 5.0",
                "Digitale Strategien für Industrie 5.0",
                "Wertschöpfungskette und Prozesse für Industrie 5.0",
                "Intelligente Fertigungstechnologien für Industrie 5.0",
                "Integration erweiterter technologischer Komponenten in die Abläufe und das Angebot Ihres Unternehmens",
                "Nutzung etablierter digitaler Technologien für Industrie 5.0"]

assert len(MM_ORIGINAL_DIM_NAMES) == len(MM_DIM_NAMES) == 7, "Expected seven dimensions"

SURVEY_COLUMNS = [col_type_pair[0] for col_type_pair in SURVEY_COLUMNS_AND_TYPES]

MM_DIM1_TOPICS = ["Leadership support",
                  "Continuous improvement culture",
                  "Dedicated teams",
                  "Digital skills"]

MM_DIM2_TOPICS = ["Familiarity",
                  "Impact perception",
                  "Usefulness",
                  "Readiness for adoption"]

# NOTE: This is from the original paper
_MM_DIM3_TOPICS = ["Digital vision and roadmap"
                   "Customer integration",
                   "Collaboration",
                   "Zero paper strategy", # Sustainability commitment
                   "Financial investment",]

# NOTE: This is our adjustment
MM_DIM3_TOPICS = ["Digital vision",
                  "Digital strategy",
                  "Customer integration",
                  "Collaboration",
                  "Sustainability commitment",
                  "Financial investment",]

MM_DIM4_TOPICS = ["Digitalization of vertical  value chain",
                  "Real-time production  monitoring and control",
                  "End-to-end IT-enabled  planning and steering process",
                  "Digital production  equipment",
                  "Digitalization of horizontal  value chain",]

# NOTE:: We added efficiency item
MM_DIM5_TOPICS = ["Automation for efficiency",
                  "Autonomous and  collaborative robots",
                  "Software systems like  Enterprise Resource Planning  (ERP), Manufacturing Execution  System (MES), Customer  Relationship Management (CRM)  and Product Lifecycle  Management (PLM)",
                  "Identifiers like bar code, QR  code (Quick Response code), RFID  (radio frequency identification)  and RTLS (Real-Time Locating  System)",
                  "Sensors, actuators,  embedded systems and PLCs  (Programmable Logic Controller)",
                  "Machine to Machine (M2M)  and Human to Machine (H2M)  communication",
                  "Digital platforms for supplier  integration",
                  "Digital platforms for  customer integration",
                  "Augmented Reality (AR),  Virtual Reality (VR) and Mixed  Reality (MR)",]

MM_DIM6_TOPICS = ["Additive manufacturing  (AM), 3D Printing (3DP)",
                  "Mobile and wearable  devices",
                  "Blockchain Technology (BT)",
                  "Smart Product",]

MM_DIM7_TOPICS = ["Cloud Computing (CC)  network for resources sharing",
                  "Cloud Computing (CC)  network for data storing",
                  "Internet of Things (IoT)",
                  "Internet of Services (IoS)",
                  "Processing Big Data (BD) in  real-time",
                  "Simulation tools",
                  "Artificial Intelligence (AI),  Machine Learning (ML) and Deep  Learning (DL)",
                  "Industrial Cyber Security"]

MM_TOPICS = [*MM_DIM1_TOPICS,
             *MM_DIM2_TOPICS,
             *MM_DIM3_TOPICS,
             *MM_DIM4_TOPICS,
             *MM_DIM5_TOPICS,
             *MM_DIM6_TOPICS,
             *MM_DIM7_TOPICS]

MM_DIM1_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [Die Unternehmensführung meines Unternehmens unterstützt und fördert die digitale Transformation hin zu Industrie 5.0-Abläufen (z. B. Ressourceneffizienz-Programme, Ergonomieverbesserungsinitiativen).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [In meinem Unternehmen wird im Sinne von Industrie 5.0 eine Kultur der kontinuierlichen Verbesserung gefördert (z. B. durch digitales Ideenmanagement)]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [In meinem Unternehmen gibt es Arbeitsteams, die gezielt an der Umsetzung von Industrie 5.0-Abläufen arbeiten.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.   [Die Mitarbeitenden meines Unternehmens verfügen über ausreichende digitale Kompetenzen zur Umsetzung von Industrie 5.0-Abläufen.]"]

MM_DIM2_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich bin mit dem Konzept von Industrie 5.0 vertraut.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich nehme die Auswirkungen wahr, die durch Industrie 5.0-Konzepte entstehen (z. B. Entlastung der Mitarbeitenden, Emissionsreduzierung, Resilienz gegenüber Lieferketten-Engpässen).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich sehe den Nutzen technologiegestützter Industrie 5.0-Abläufe für die Leistungsfähigkeit meines Unternehmens.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Ich fühle mich bereit, in meinem Unternehmen Technologien einzuführen, um die Abläufe im Sinne von Industrie 5.0 zu gestalten.]",]

# NOTE: First difference roadmap and strategy are split. Zero paper strategy is replaced by sustainability in general
MM_DIM3_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über eine Strategie für die Digitalisierung, die auch zur Umsetzung von Industrie 5.0-Abläufen beiträgt.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über eine Roadmap für die Digitalisierung, die auch zur Umsetzung von Industrie 5.0-Abläufen beiträgt.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen berücksichtigt bei der Produkt- oder Dienstleistungsentwicklung die Bedürfnisse der Verbraucher:innen (z. B. durch Usability-Tests, Auswertung von Kundenfeedback-Daten).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen arbeitet mit externen Stakeholdern (z. B. Technologieunternehmen, Beratungsgesellschaften, Hochschulen und / oder Universitäten) zusammen, um Industrie 5.0-Abläufe zu entwickeln und umzusetzen.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen zeigt ein starkes Engagement für Nachhaltigkeit und Umweltschutz durch verantwortungsvolle Praktiken im Umgang mit natürlichen Ressourcen und bei der Reduzierung von Emissionen.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen investiert finanziell in Industrie 5.0-Abläufe (z. B. Investitionen in KI-gesteuerte Produktionslinien, Lieferketten-Monitoring-Systeme).]",]

MM_DIM4_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mit Hilfe digitaler Technologien gelingt es meinem Unternehmen, die Abläufe bei meinen Zuliefererbetrieben und Abnehmer:innen (Kund:innen) mit zu steuern, um die Erreichung resilienter und menschzentrierter Ziele zu unterstützen (z. B. gemeinsames Commitment zu ethischen Richtlinien und Transparenz in der Lieferkette).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Die Abläufe in meinem Unternehmens werden in Echtzeit überwacht und reagieren dynamisch auf Veränderungen, um die Resilienz von Produktions- oder Dienstleistungsprozessen zu fördern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt IT-gestützte Technologien für eine durchgängig nachhaltige und resiliente Planung und Steuerung (z. B. Absatzprognosen, Produktions-, Prozess-, Lager- und Logistikplanung).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt digitale Tools und Methoden ein, um Nachhaltigkeit, Resilienz und Menschzentrierung in den Abläufen zu verbessern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mit Hilfe digitaler Technologien gelingt es meinem Unternehmen, mit anderen Unternehmen der gleichen Branche oder Produktionsstufe zu kooperieren, um die Erreichung resilienter und menschzentrierter Ziele zu unterstützen (z. B. gemeinsames Commitment zu ethischen Richtlinien, Transparenz, Nachhaltigkeitsziele).]"]

# NOTE: Second difference, new question added (increase of efficiency)
MM_DIM5_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Technologien zur Automatisierung und Effizienzsteigerung von Abläufen (z. B. durch automatisierte Datenauswertungen, robotergestützte Fertigung).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt Roboter zur Automatisierung von Abläufen (wie Reinigung oder Verpackung) und / oder autonome Fahrzeuge für Logistikaufgaben ein. Diese Systeme interagieren mit Menschen und der Umgebung, um Abläufe resilient und menschzentriert zu gestalten.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Software, um Informationen zwischen den verschiedenen Unternehmensbereichen auszutauschen und Feedback zu erhalten, das für die Entscheidungsfindung in Abläufen relevant ist.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verwendet digitale bzw. digital lesbare Kennungen für Produktionsmittel (z. B. Produkte, Services, Teile, Werkzeuge oder Personal), um diese in den verschiedenen Bereichen des Unternehmens wie Produktionsstätten, Lager und Instandhaltung zu verfolgen. ]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen setzt Sensoren, Aktoren und SPS-Steuerungen an Maschinen und Anlagen ein, um Abläufe nachhaltiger und resilient zu gestalten.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen verfügt über interoperable Kommunikationssysteme zum Informationsaustausch zwischen Maschinen, Systemen und Mitarbeitenden auf verschiedenen Hierarchieebenen mit dem Ziel, die Resilienz und Menschzentrierung  von Abläufen zu verbessern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Plattformen, um in Echtzeit Informationen über die Leistung zwischen Produktions-, Servicestätten, Lieferant:innen und Lager auszutauschen und so die Abläufe im Sinne von Industrie 5.0 zu verbessern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt digitale Plattformen, um mit den Kund:innen Informationen über die Leistung in Produktion oder Dienstleistung zu teilen und Unterstützung bei spezifischen Anfragen zu leisten.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Augmented-Reality-Technologien, um Abläufe im Sinne von Industrie 5.0  zu verbessern (z. B. virtuelle Visualisierung von Problemen in Produktentwicklungsphasen, virtuelle Brillen zur Unterstützung der Mitarbeitenden bei Entscheidungen).]",]

MM_DIM6_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt 3D-Drucktechniken, um die Nachhaltigkeit von Abläufen zu verbessern (z. B. durch Reduzierung von Materialabfällen, Realisierung nachhaltiger Verpackungen und Senkung des Energieverbrauchs).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt mobile Geräte (z. B. Smartphones und Tablets) sowie tragbare Geräte (z. B. Smartwatches, Smartglasses und Smart Gloves), um Informationen über Abläufe abzurufen und in Echtzeit mit verschiedenen Systemen zu kommunizieren.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt fälschungssichere, digitale Datenspeicher, um die Lieferkette resilienter zu gestalten (z. B. durch Bereitstellung von Rückverfolgbarkeitsinformationen) und die Produktion zu optimieren (z. B. durch Zertifizierung von Nachhaltigkeitsindikatoren).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen erzeugt intelligente Produkte mit Sensoren und/oder Smart Services, die mit der Umgebung interagieren können, um Abläufe im Sinne von Industrie 5.0 zu verbessern.]",]

MM_DIM7_COLUMNS = ["Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Cloud-Computing-Systeme für die Fernverbindung und gemeinsame Nutzung von Hardware- (z. B. Geräte, Roboter) und Software-Ressourcen (z. B. Daten, Dokumente, Software), wodurch die Resilienz von Abläufen verbessert wird.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen speichert und ruft Informationen aus dem Cloud-Computing-Netzwerk ab, um die Resilienz von Abläufen zu verbessern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Technologien für die drahtlose Kommunikation zwischen Maschinen, Robotern, IT-Systemen und Mitarbeitenden (z. B. Wi-Fi, 0.17 ZigBee und Bluetooth), die in der Lage sind, die Abläufe im Sinne von Industrie 5.0 zu verbessern.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen bietet Kund:innen und Lieferant:innen Produkte und / oder Dienstleistungen auf Basis von Webtechnologien an, die einen individuellen Mehrwert bieten (z. B. durch interaktive Kundenportale oder Produktkonfiguratoren).]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen ist in der Lage, Daten (von physischen Objekten und externen Datenquellen) in Echtzeit zu erfassen, zu speichern und zu verwalten, mit dem Ziel, technische Anlagen im Sinne von Industrie 5.0 zu verbessern.	]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Produktions- und Dienstleistungsdaten, um mögliche Szenarien zu simulieren und dabei verschiedene Lösungen (oder Probleme) in Prozessabläufen zu bewerten.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt Technologien der künstlichen Intelligenz (z. B. Verarbeitung natürlicher Sprache, Spracherkennung, regelbasierte Systeme und Computer Vision), die zur Verbesserung von Produkten, Dienstleistungen und Abläufen nützlich sind.]",
                   "Wir bitten Sie, die folgenden Fragen zu Ihrem Unternehmen auf einer Skala von (1) \"stimme gar nicht zu\" bis (5) \"stimme voll zu\" möglichst spontan zu beantworten.  [Mein Unternehmen nutzt verschiedene IT-Sicherheitsmaßnahmen (z. B. Verschlüsselung, Authentifizierung und Autorisierung), die die Kommunikationssicherheit und den Datenschutz verbessern.]",]

MM_COLUMNS = [*MM_DIM1_COLUMNS,
              *MM_DIM2_COLUMNS,
              *MM_DIM3_COLUMNS,
              *MM_DIM4_COLUMNS,
              *MM_DIM5_COLUMNS,
              *MM_DIM6_COLUMNS,
              *MM_DIM7_COLUMNS]


MM_DIM1_ITEM_WEIGHTS = [0.46, 0.27, 0.18, 0.09]
MM_DIM2_ITEM_WEIGHTS = [0.39, 0.32, 0.16, 0.13]
# NOTE: I5.0 roadmap/strategy splitted into two questions 0.22 = 0.44 / 2
_MM_DIM3_ITEM_WEIGHTS = [0.44, 0.23, 0.14, 0.09, 0.08]
MM_DIM3_ITEM_WEIGHTS = [0.22, 0.22, 0.23, 0.14, 0.09, 0.08]
MM_DIM4_ITEM_WEIGHTS = [0.43, 0.25, 0.12, 0.13, 0.07]
# NOTE: Weight is missing for the added question, subtracted 0.01 from each question so that the new question gets 0.01 * 8 as its weight
_MM_DIM5_ITEM_WEIGHTS = [0.21, 0.25, 0.16, 0.08, 0.07, 0.07, 0.07, 0.06]
MM_DIM5_ITEM_WEIGHTS = [0.08, 0.2, 0.24, 0.15, 0.07, 0.06, 0.06, 0.06, 0.05]
MM_DIM6_ITEM_WEIGHTS = [0.39, 0.32, 0.12, 0.19]
MM_DIM7_ITEM_WEIGHTS = [0.27, 0.16, 0.13, 0.11, 0.13, 0.09, 0.06, 0.05]

MM_DIM_WEIGHTS = [0.39, 0.19, 0.16, 0.1, 0.07, 0.06, 0.05]

MM_COLS_AND_WEIGHTS = [(MM_DIM1_COLUMNS, MM_DIM1_ITEM_WEIGHTS),
                       (MM_DIM2_COLUMNS, MM_DIM2_ITEM_WEIGHTS),
                       (MM_DIM3_COLUMNS, MM_DIM3_ITEM_WEIGHTS),
                       (MM_DIM4_COLUMNS, MM_DIM4_ITEM_WEIGHTS),
                       (MM_DIM5_COLUMNS, MM_DIM5_ITEM_WEIGHTS),
                       (MM_DIM6_COLUMNS, MM_DIM6_ITEM_WEIGHTS),
                       (MM_DIM7_COLUMNS, MM_DIM7_ITEM_WEIGHTS)]


fix_weights(MM_DIM1_ITEM_WEIGHTS, label="1")
fix_weights(MM_DIM2_ITEM_WEIGHTS, label="2")
fix_weights(MM_DIM3_ITEM_WEIGHTS, label="3")
fix_weights(MM_DIM4_ITEM_WEIGHTS, label="4")
fix_weights(MM_DIM5_ITEM_WEIGHTS, label="5")
fix_weights(MM_DIM6_ITEM_WEIGHTS, label="6")
fix_weights(MM_DIM7_ITEM_WEIGHTS, label="7")
fix_weights(MM_DIM_WEIGHTS, label="top level")

assert math.isclose(sum(MM_DIM1_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 1 has to be 1.0 but is {sum(MM_DIM1_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM2_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 2 has to be 1.0 but is {sum(MM_DIM2_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM3_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 3 has to be 1.0 but is {sum(MM_DIM3_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM4_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 4 has to be 1.0 but is {sum(MM_DIM4_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM5_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 5 has to be 1.0 but is {sum(MM_DIM5_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM6_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 6 has to be 1.0 but is {sum(MM_DIM6_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM7_ITEM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of item weights in dimension 7 has to be 1.0 but is {sum(MM_DIM7_ITEM_WEIGHTS)}"
assert math.isclose(sum(MM_DIM_WEIGHTS), 1.0, rel_tol=EPS), f"Sum of dimension weights has to be 1.0 but is {sum(MM_DIM_WEIGHTS)}"


assert len(MM_DIM1_COLUMNS) == len(MM_DIM1_TOPICS) == len(MM_DIM1_ITEM_WEIGHTS)
assert len(MM_DIM2_COLUMNS) == len(MM_DIM2_TOPICS) == len(MM_DIM2_ITEM_WEIGHTS)
assert len(MM_DIM3_COLUMNS) == len(MM_DIM3_TOPICS) == len(MM_DIM3_ITEM_WEIGHTS)
assert len(MM_DIM4_COLUMNS) == len(MM_DIM4_TOPICS) == len(MM_DIM4_ITEM_WEIGHTS)
assert len(MM_DIM5_COLUMNS) == len(MM_DIM5_TOPICS) == len(MM_DIM5_ITEM_WEIGHTS)
assert len(MM_DIM6_COLUMNS) == len(MM_DIM6_TOPICS) == len(MM_DIM6_ITEM_WEIGHTS)
assert len(MM_DIM7_COLUMNS) == len(MM_DIM7_TOPICS) == len(MM_DIM7_ITEM_WEIGHTS)
assert len(MM_TOPICS) == len(MM_COLUMNS)


def validate_columns(df):
    assert len(df.columns) == len(SURVEY_COLUMNS)
    for col in SURVEY_COLUMNS:
        assert col in df.columns, f"{col} not in survey"


def sample_data(num_rows):
    rows = []
    for _ in range(num_rows):
        row = {}
        for name, field in SURVEY_COLUMNS_AND_TYPES:
            row[name] = field.sample()
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

def get_scores(df):
    dim_scores_list = []
    for i, (cols, weights) in enumerate(MM_COLS_AND_WEIGHTS):
        dim_scores = df[cols].multiply(weights, axis=1).sum(axis=1)
        df[f"Dimension_{i+1}_Score"] = dim_scores
        dim_scores_list.append(dim_scores)

    dim_scores_df = pd.concat(dim_scores_list, axis=1)
    df["Maturity_Score"] = dim_scores_df.dot(MM_DIM_WEIGHTS)
    return df
