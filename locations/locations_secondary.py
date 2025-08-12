from datetime import datetime, timedelta

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from entities.player import Player
from schemas.locations_secondary import FactoryPage
from utils.custom_logging import logger
from utils.decorators import require_location_page, require_page_prefix
from utils.general import parse_date
from utils.human_simulation import random_delay


class Shaurburgers:
    """
    Represents the 'Shaurburgers' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Shaurburgers page.
    """

    BASE_URL = "https://www.moswar.ru/shaurburgers/"
    LOCATORS: dict[str, tuple[str, str]] = {
        "work_start_button": (By.XPATH, '//span[@class="f"]'),
        "work_select_hours": (By.NAME, "time"),
        "work_leave_button": (By.XPATH, '//span[@class="button" and @onclick="macdonaldsLeave();"]'),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Shaurburgers class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def is_opened(self) -> bool:
        """
        Check if the driver is currently on the Shaurburgers page.
        """
        return self.driver.current_url == self.BASE_URL

    def open(self) -> None:
        """
        Ensure the driver is on the Shaurburgers page, navigating or refreshing as needed
        """
        if not self.is_opened():
            logger.info("Driver is not on the shaurburgers page. Going to the shaurburgers.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the shaurburgers page, refreshing.")
            self.driver.refresh()
            random_delay()

    @require_location_page
    def is_work_active(self) -> bool:
        """
        Return True if the player is currently working, else False.
        """
        try:
            self.driver.find_element(*self.LOCATORS["work_leave_button"])
            self.player.on_work = True
            return True
        except NoSuchElementException:
            self.player.on_work = False
            return False

    @require_location_page
    def get_work_time_left(self) -> int:
        """
        Get the remaining work time in hours.
        """
        if self.is_work_active():
            logger.error("Can't get work time left, player is currently working.")
            time_left = -9999
        else:
            try:
                select_work_hours_el_el = self.driver.find_element(*self.LOCATORS["work_select_hours"])
                time_left = int(select_work_hours_el_el.text.split("\n")[-1].split(" ")[0])
            except Exception:
                time_left = 0

        self.player.work_time_left = time_left
        return time_left

    @require_location_page
    def start_work_shift(self, work_hours: int) -> None:
        """
        Start a work shift for the specified duration.

        Parameters:
            work_hours (int): Duration of work shift in hours. Must be between 1 and 8.

        Behavior:
            - Checks for valid work shift duration and player status.
            - Ensures enough work time is left.
            - Selects work shift duration and starts work.
            - Updates player status and logs the result.
        """
        logger.info(f"Starting work shift for {work_hours} hours.")

        # Error checks
        if not (1 <= work_hours <= 8):
            logger.error("Work hours must be between 1 and 8.")
            return None

        if self.is_work_active():
            logger.error("Can't start the work shift, player is already working.")
            return None

        work_time_left = self.get_work_time_left()
        if work_time_left < work_hours:
            logger.error(
                f"Can't start the work shift for {work_hours} hours, player has only {work_time_left} hours left."
            )
            return None

        # Start work
        if work_hours == 1:
            work_hours_str = "1 час"
        elif work_hours in [2, 3, 4]:
            work_hours_str = f"{work_hours} часа"
        else:
            work_hours_str = f"{work_hours} часов"

        select_work_hours_el = Select(self.driver.find_element(*self.LOCATORS["work_select_hours"]))
        select_work_hours_el.select_by_visible_text(work_hours_str)
        random_delay()

        start_work_el = self.driver.find_element(*self.LOCATORS["work_start_button"])
        start_work_el.click()

        # Check
        random_delay(min_time=5, max_time=6)
        if self.is_work_active():
            self.player.work_time_left -= work_hours
            logger.info(
                f"Work shift started for {work_hours} hours. Remaining work time: {self.player.work_time_left} hours."
            )
        else:
            logger.error("Failed to start work shift")


class Casino:
    """
    Represents the 'Casino' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Casino page.
    """

    BASE_URL = "https://www.moswar.ru/casino/"
    LOCATORS: dict[str, tuple[str, str]] = {
        "buy_chips_input": (By.XPATH, '//input[@id="stash-change-ore"]'),
        "buy_chips_confirm": (By.XPATH, '//button[@id="button-change-ore"]'),
        "buy_chips_error": (By.XPATH, "//*[contains(text(), 'Антиазартный комитет запрещает')]"),
        "chips_balance": (By.XPATH, "//span[@id='fishki-balance-num']"),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Casino class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def is_opened(self) -> bool:
        """
        Check if the driver is currently on the Casino page.
        """
        return self.driver.current_url == self.BASE_URL

    def open(self) -> None:
        """
        Ensure the driver is on the casino page, navigating or refreshing as needed.
        """
        if not self.is_opened():
            logger.info("Driver is not on the casino page. Going to the casino.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the casino page, refreshing.")
            self.driver.refresh()
            random_delay()

    @require_location_page
    def get_player_chips_amount(self) -> int:
        """
        Get the current number of chips the player has in the casino.
        """
        try:
            amount = int(self.driver.find_element(*self.LOCATORS["chips_balance"]).text.replace(",", ""))
            self.player.casino_chips = amount
        except NoSuchElementException:
            amount = -9999
            logger.error("Can't get chips amount, element not found.")
        return amount

    @require_location_page
    def buy_chips(self, amount: int) -> None:
        """
        Buy chips in the casino.

        Parameters:
            amount (int): Number of chips to buy (1-20).
        """
        logger.info(f"Buying {amount} chips.")

        if not (1 <= amount <= 20):
            logger.error("The number of chips must be between 1 and 20.")
            return None

        # Buy
        buy_amt_el = self.driver.find_element(*self.LOCATORS["buy_chips_input"])
        buy_amt_el.click()
        random_delay()
        buy_amt_el.send_keys(Keys.BACKSPACE)
        random_delay()
        buy_amt_el.send_keys(str(amount))
        random_delay()

        self.driver.find_element(*self.LOCATORS["buy_chips_confirm"]).click()
        random_delay()

        # Check
        try:
            self.driver.find_element(*self.LOCATORS["buy_chips_error"])
            logger.error(f"Can't buy {amount} chips, player is not allowed to buy.")
        except NoSuchElementException:
            self.player.casino_chips += amount
            logger.info(f"Successfully bought {amount} chips.")


class Police:
    """
    Represents the 'Police' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Police page.
    """

    BASE_URL = "https://www.moswar.ru/police/"
    LOCATORS: dict[str, tuple[str, str]] = {
        "connections_establish": (By.XPATH, '//div[starts-with(text(), "Наладить связи —")]'),
        "connections_status": (By.XPATH, "//p[contains(text(), 'Связи налажены до')]"),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Police class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def is_opened(self) -> bool:
        """
        Check if the driver is currently on the Police page.
        """
        return self.driver.current_url == self.BASE_URL

    def open(self) -> None:
        """
        Ensure the driver is on the police page, navigating or refreshing as needed.
        """
        if not self.is_opened():
            logger.info("Driver is not on the police page. Going to the police.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the police page, refreshing.")
            self.driver.refresh()
            random_delay()

    @require_page_prefix("https://www.moswar.ru/police/")
    def are_connections_established(self) -> bool:
        """
        Return True if the player has established police connections, else False.
        """
        try:
            connections_status = self.driver.find_element(*self.LOCATORS["connections_status"]).text
            date_str = connections_status.split(sep=" ", maxsplit=3)[-1]
            self.player.police_expiration_date = parse_date(date_str)
            self.player.police_is_active = True
            return True
        except NoSuchElementException:
            self.player.police_expiration_date = None
            self.player.police_is_active = False
            return False

    @require_location_page
    def establish_connections(self) -> None:
        """
        Establish police connections.
        """
        logger.info("Establishing police connections.")

        if self.are_connections_established():
            logger.error(
                f"Can't establish connections, already established until {self.player.police_expiration_date}."
            )
            return None

        self.driver.find_element(*self.LOCATORS["connections_establish"]).click()
        random_delay()

        if self.are_connections_established():
            logger.info("Police connections established successfully.")
        else:
            logger.error("Failed to establish police connections.")


class NightClub:
    """
    Represents the 'NightClub' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the NightClub page.
    """

    BASE_URL = "https://www.moswar.ru/nightclub/"
    LOCATORS: dict[str, tuple[str, str]] = {
        "tattoo_timer": (By.XPATH, '//p[contains(text(), "До следующей печати")]/span[@class="timer"]'),
        "tattoo_get": (By.XPATH, '//div[text()="забрать"]'),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the NightClub class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def is_opened(self) -> bool:
        """
        Check if the driver is currently on the NightClub page.
        """
        return self.driver.current_url == self.BASE_URL

    def open(self) -> None:
        """
        Ensure the driver is on the nightclub page, navigating or refreshing as needed.
        """
        if not self.is_opened():
            logger.info("Driver is not on the nightclub page. Going to the nightclub.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the nightclub page, refreshing.")
            self.driver.refresh()
            random_delay()

    @require_location_page
    def is_tattoo_availiable(self) -> bool:
        """
        Return True if the player can take new tattoos, else False.
        """
        logger.info("Checking tattoo timer.")
        try:
            time_text = self.driver.find_element(*self.LOCATORS["tattoo_timer"]).text
            time_hours = int(time_text.split(":")[0])
            time_minutes = int(time_text.split(":")[1])
            time_seconds = int(time_text.split(":")[2])
        except NoSuchElementException:
            time_hours, time_minutes, time_seconds = 0, 0, 0

        time_seconds = timedelta(hours=time_hours, minutes=time_minutes, seconds=time_seconds).total_seconds()
        if time_seconds == 0:
            logger.info("Player can take new tattoos now.")
            self.player.tattoo_is_available = True
            self.player.tattoo_availability_date = datetime.now()
            return True
        else:
            logger.info(f"Player can take new tattoos in {time_hours} hours, {time_minutes} minutes")
            self.player.tattoo_is_available = False
            self.player.tattoo_availability_date = datetime.now() + timedelta(seconds=time_seconds)
            return False

    @require_location_page
    def get_tattoo(self) -> None:
        """
        Get a tattoo if available.
        """
        logger.info("Getting tattoo.")

        if not self.is_tattoo_availiable():
            logger.error("Can't get tattoo, player can't take new tattoos now.")
            return None

        self.driver.find_element(*self.LOCATORS["tattoo_get"]).click()
        random_delay()

        if not self.is_tattoo_availiable():
            logger.info("Tattoo successfully taken.")
        else:
            logger.error("Failed to take tattoo")


# TODO: finish
class Factory:
    """
    Represents the 'Factory' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Factory page.
    """

    PAGE_URLS = {
        FactoryPage.BASE: "https://www.moswar.ru/factory/",
        FactoryPage.BRONEVIK: "https://www.moswar.ru/factory/build/bronevik/",
    }

    LOCATORS: dict[str, tuple[str, str]] = {
        "petrics_amt": (By.XPATH, "//*[contains(text(), 'В наличии')]//span[@class='petric']"),
        "petrics_amt_to_be_produced": (By.XPATH, '//*[@id="factory_petrik_1"]//span[@class="petric"]'),
        "petrics_produce_timer": (By.XPATH, "TBA"),  # TODO: TBA
        "petrics_produce_no_timer": (By.XPATH, '//div[contains(text(), "Сделать моментально")]'),
        "petrics_in_production": (By.XPATH, "TBA"),  # TODO: TBA
        "bronevik_open": (By.XPATH, "//a[@href='/factory/build/bronevik/']"),
        "bronevik_details_img": (By.XPATH, "//div[@class='exchange']//div[@class='get']//img"),
        "bronevik_details_buy": (By.XPATH, "//button[@id='factory-build-exchange']"),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Factory class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def is_opened(self, page: FactoryPage = FactoryPage.BASE) -> bool:
        """
        Check if the driver is currently on the specified Factory page (BASE or BRONEVIK).
        """
        return self.driver.current_url == self.PAGE_URLS[page]

    def open(self, page: FactoryPage = FactoryPage.BASE) -> None:
        """
        Ensure the driver is on the requested Factory page (BASE or BRONEVIK).
        """
        if self.is_opened(page):
            logger.info(f"Driver is already on the {page} page, refreshing.")
            self.driver.refresh()
            random_delay()
            return

        if page == FactoryPage.BRONEVIK and self.is_opened(FactoryPage.BASE):
            logger.info("Driver is on BASE, navigating to BRONEVIK.")
            self.driver.find_element(*self.LOCATORS["bronevik_open"]).click()
            random_delay()
            return

        logger.info(f"Driver is not on the {page} page. Going to BASE first.")
        self.driver.get(self.PAGE_URLS[FactoryPage.BASE])
        random_delay()

        if page == FactoryPage.BRONEVIK:
            self.driver.find_element(*self.LOCATORS["bronevik_open"]).click()
            random_delay()

    # ------------------------
    # PETRICS
    # ------------------------
    @require_location_page
    def get_current_petrics_amount(self) -> int:
        """
        Get the current amount of 'Петрики' player has.
        """
        amount = int(self.driver.find_element(*self.LOCATORS["petrics_amt"]).text.replace(",", ""))
        self.player.petrics = amount
        return amount

    @require_location_page
    def get_petrics_amount_to_be_produced(self) -> int:
        """
        Get the amount of 'Петрики' that can be produced in the factory.
        """
        amount = int(
            self.driver.find_element(*self.LOCATORS["petrics_amt_to_be_produced"]).text.replace(",", "")
        )
        return amount

    # TODO: finish when status is available
    @require_location_page
    def if_producing_petrics(self) -> bool:
        """
        Return True if the factory is currently producing 'Петрики', else False.
        """
        return False

    # TODO: finish
    @require_location_page
    def start_producing_petrics(self) -> None:
        """
        Start producing 'Петрики' in the factory.
        """
        logger.info("Starting to produce 'Петрики'.")

        if self.if_producing_petrics():
            logger.error("Can't start producing 'Петрики', already producing.")
            return None

        amt_to_be_produced = self.get_petrics_amount_to_be_produced()

        try:
            current_amt = self.get_current_petrics_amount()
            self.driver.find_element(*self.LOCATORS["petrics_produce_no_timer"]).click()
            random_delay()

            if current_amt + amt_to_be_produced == self.get_current_petrics_amount():
                logger.info(f"{amt_to_be_produced} 'Петрики' successfully produced.")
                self.player.petrics += amt_to_be_produced
                self.player.ore -= amt_to_be_produced
                self.player.money -= amt_to_be_produced * 100
            else:
                logger.error("Failed to produce 'Петрики'")
        except NoSuchElementException:
            self.driver.find_element(*self.LOCATORS["petrics_produce_timer"]).click()
            random_delay()

            if self.if_producing_petrics():
                logger.info(f"Started producing {amt_to_be_produced} 'Петрики'.")
                self.player.ore -= amt_to_be_produced
                self.player.money -= amt_to_be_produced * 100
            else:
                logger.error("Failed to start producing 'Петрики'.")

    # ------------------------
    # BRONEVIK
    # ------------------------
    @require_page_prefix(PAGE_URLS[FactoryPage.BRONEVIK])
    def check_current_details_name(self) -> str:
        """
        Get the name of the current details available for purchase in the factory.
        """
        logger.info("Checking current details name.")

        details_name = self.driver.find_element(*self.LOCATORS["bronevik_details_img"]).get_attribute("alt")
        logger.info(f"Details name: '{details_name}'")
        return details_name if details_name else "ERROR"

    @require_page_prefix(PAGE_URLS[FactoryPage.BRONEVIK])
    def buy_current_details(self) -> None:
        """
        Buy the current details in the factory if available.
        """
        detail_name = self.check_current_details_name()
        logger.info(f"Buying current details: {detail_name}")
        self.driver.find_element(*self.LOCATORS["bronevik_details_buy"]).click()
        random_delay()

        self.player.mobiles -= 3
        self.player.stars -= 5


# add Bojara filtering and status check TODO: rework
class TrainerVip:
    """
    Represents the 'TrainerVip' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the TrainerVip page.
    """

    BASE_URL = "https://www.moswar.ru/trainer/vip/"

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the TrainerVip class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the vip trainer page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the vip trainer page. Going to the vip trainer.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the vip trainer page, refreshing.")
            self.driver.refresh()
            random_delay()

    def check_bojara_timer(self) -> float:
        """
        TBA
        """
        logger.info("Checking bojara timer.")
        self.open()

        # Open Bojara page
        self.driver.find_element(By.XPATH, '//div[@onclick="Hawthorn.show();"]').click()
        random_delay()

        # Check Bojara timer
        try:
            time_element = self.driver.find_element(
                By.XPATH,
                '//div[@class="hawthorn-popup__button"]/span',
            )
            time_text = time_element.text
            time_hours = int(time_text.split(":")[0])
            time_minutes = int(time_text.split(":")[1])
            logger.info(f"Player can drink Bojara in {time_hours} hours and {time_minutes} minutes.")
        except NoSuchElementException:
            time_hours = 0
            time_minutes = 0
            logger.info("Player can drink Bojara now.")
        time_seconds = timedelta(hours=time_hours, minutes=time_minutes).total_seconds()

        # Additionaly check if Bojara filtering is not used
        try:
            _ = self.driver.find_element(
                By.XPATH,
                '//div[@class="c" and contains(text(), "Отфильтровать боярышник")]',
            )
            logger.warning("Bojara filtering is not yet used!")
        except NoSuchElementException:
            pass

        return time_seconds

    def drink_Bojara(self) -> None:
        """
        TBA
        """
        logger.info("Drinking Bojara.")
        self.open()

        # Open Bojara page
        self.driver.find_element(By.XPATH, '//div[@onclick="Hawthorn.show();"]').click()
        random_delay()

        # Drink Bojara
        try:
            drink_el = self.driver.find_element(
                By.XPATH, '//div[@onclick[contains(., "trainer/activate-hawthorn/")]]'
            )
            drink_el.click()
            random_delay()
            logger.info("Bojara drink successfully.")
        except NoSuchElementException:
            logger.error("Can't drink Bojara, no Bojara element found.")
