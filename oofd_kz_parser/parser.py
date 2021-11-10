import re
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Union

from bs4 import BeautifulSoup
from oofd_kz_parser.const import SETTINGS
from oofd_kz_parser.models import Ticket, TicketItem
from PIL import Image
from pyzbar.pyzbar import decode
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class TicketParser:
    @classmethod
    def from_qr(cls, img: Union[str, Path, Image.Image]) -> Ticket:
        """Спарсить чек используя QR код (Parse ticket from QR code)

        :param img: Путь к изображению или объект класса PIL.Image.Image (Path to image or instance of PIL.Image.Image)
        :return: Спарсенный чек (Parsed ticket)
        """
        if isinstance(img, (str, Path)):
            img = Image.open(img)

        decoded_list = decode(img)

        if len(decoded_list) == 0:
            raise ValueError

        decoded = decoded_list[0]

        return cls.parse_ticket(decoded.data.decode())

    @classmethod
    def from_parameters(cls, i: str, f: str, s: Union[float, int], t: datetime) -> Ticket:
        """Спарсить чек используя вручную введенные параметры (Parse ticket using manually provided parameters)

        :param i:
        :param f:
        :param s: Общая сумма чека (Ticket total)
        :param t: Время на чеке (Ticket's time)
        :return:
        """
        return cls.parse_ticket(
            f"https://consumer.oofd.kz?i={i}&f={f}&s={s:.1f}&t={t.strftime('%Y%m%dT%H%M%S')}"
        )

    @staticmethod
    def parse_ticket(url: str) -> Ticket:
        service = Service(SETTINGS.chromedriver_path)

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")

        driver = Chrome(service=service, options=options)
        driver.get(url)
        sleep(10)
        soup = BeautifulSoup(driver.page_source, "html5lib")
        driver.quit()

        app_ticket = soup.find("app-ticket")
        app_ticket_items = app_ticket.find("app-ticket-items")
        rows = app_ticket_items.find_all("div", {"class": "row row-position"})
        items_text = [[child.text for child in row] for row in rows]
        items = [
            TicketItem(
                index=int(item[0].replace(".", "")),
                name=item[1].replace("\xa0", "").strip().encode("utf-8"),
                price=float(item[3].replace("\xa0", "").replace("₸", "").strip()),
                quantity=float(item[4].strip()),
                total=float(item[5].replace("\xa0", "").replace("₸", "").strip().replace(",", ".")),
            )
            for item in items_text
        ]

        app_ticket_header = soup.find("app-ticket-header")
        dt = datetime.strptime(
            re.search(r"(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})", app_ticket_header.text).group(1),
            "%d.%m.%Y %H:%M",
        )
        seller = list(app_ticket_header.find_next("p").children)[0].strip()

        return Ticket(
            dt=dt,
            seller=seller,
            items=items,
            total=sum(item.total for item in items),
        )
