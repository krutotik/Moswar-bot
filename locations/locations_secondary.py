from datetime import timedelta
from typing import Literal, Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from entities.player import Player
from utils.custom_logging import logger
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

    def get_work_time_left(self) -> int:
        """
        Get the remaining work time in hours.
        """
        try:
            select_work_hours_el_el = self.driver.find_element(*self.LOCATORS["work_select_hours"])
            time_left = int(select_work_hours_el_el.text.split("\n")[-1].split(" ")[0])
        except NoSuchElementException:
            logger.error("Can't get work time left, work select hours element not found.")
            time_left = -9999
        except Exception:
            time_left = 0

        self.player.work_time_left = time_left
        return time_left

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


# TODO: add as player attribute the number of chips the user has
class Casino:
    """
    Represents the 'Casino' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Casino page.
    """

    BASE_URL = "https://www.moswar.ru/casino/"

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Casino class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the casino page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the casino page. Going to the casino.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the casino page, refreshing.")
            self.driver.refresh()
            random_delay()

    # TODO: change the number of chips in player attribute
    def buy_chips(self, amount: int) -> None:
        """
        TBA
        """
        logger.info(f"Buying {amount} chips.")
        self.open()

        if not (1 <= amount <= 20):
            raise ValueError("Chips must be between 1 and 20.")

        # Buy chips
        buy_amt_el = self.driver.find_element(By.XPATH, '//input[@id="stash-change-ore"]')
        buy_amt_el.click()
        random_delay()
        buy_amt_el.send_keys(Keys.BACKSPACE)
        random_delay()
        buy_amt_el.send_keys(str(amount))
        random_delay()

        buy_confirm_el = self.driver.find_element(By.XPATH, '//button[@id="button-change-ore"]')
        buy_confirm_el.click()
        random_delay()

        # Confirm bought chips
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'Антиазартный комитет запрещает')]")
            logger.error(f"Can't buy {amount} chips, player is not allowed to buy.")
        except NoSuchElementException:
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

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Police class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the police page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the police page. Going to the police.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the police page, refreshing.")
            self.driver.refresh()
            random_delay()

    # TODO: implement function for establishing police connections
    def establish_connections(self) -> None:
        """
        TBA
        """
        logger.info("Establishing police connections.")
        self.open()

        pass


class NightClub:
    """
    Represents the 'NightClub' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the NightClub page.
    """

    BASE_URL = "https://www.moswar.ru/nightclub/"

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the NightClub class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        This method ensures the driver is on the nightclub page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the nightclub page. Going to the nightclub.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the nightclub page, refreshing.")
            self.driver.refresh()
            random_delay()

    def check_tatoo_timer(self) -> float:
        """
        TBA
        """
        logger.info("Checking tattoo timer.")
        self.open()

        # Check tattoo timer
        try:
            time_element = self.driver.find_element(
                By.XPATH,
                '//p[contains(text(), "До следующей печати")]/span[@class="timer"]',
            )
            time_text = time_element.text
            time_hours = int(time_text.split(":")[0])
            time_minutes = int(time_text.split(":")[1])
            logger.info(f"Player can take new tattoos in {time_hours} hours and {time_minutes} minutes.")
        except NoSuchElementException:
            time_hours = 0
            time_minutes = 0
            logger.info("Player can take new tattoos now.")

        time_seconds = timedelta(hours=time_hours, minutes=time_minutes).total_seconds()
        return time_seconds

    # TODO: implement function for getting tattoos when available
    def get_tattoo(self) -> None:
        """
        TBA
        """
        logger.info("Getting tattoo.")
        self.open()

        pass


# TODO: add docstrings, add check which details and how many are required
# TODO: open page and open bronevik page should be in the same function (see home for reference)
class Factory:
    """
    Represents the 'Factory' in the game and provides methods for interacting with it.

    Attributes:
        player: The player object representing the user in the game.
        driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL: The base URL for the Metro page.
    """

    BASE_URL = "https://www.moswar.ru/factory/"
    SUBPAGES = {"bronevik"}  # add main and change to pages?
    subpages_buttons_xpath_dict = {
        "bronevik": "//a[@href='/factory/build/bronevik/']",
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
        self.on_page: Optional[Literal["main", "bronevik"]] = None

    def open(self, page: Literal["main", "bronevik"] = "main") -> None:
        """
        Navigates to the factory page or its subpage.

        Parameters:
            page (Literal["main", "bronevik"]): The name of the page to open. Defaults to "main".

        Raises:
            ValueError: If the requested subpage is not supported.
        """

        # Check if driver is out of factory
        if not self.driver.current_url.startswith(self.BASE_URL):
            self.on_page = None

        # Check if page is supported
        if page != "main" and page not in self.SUBPAGES:
            raise ValueError(f"Page '{page}' is not supported. Allowed: {', '.join(self.SUBPAGES)}.")

        # Check if page is already open
        if self.on_page == page:
            logger.info(f"Driver is already on the '{page}' page, refreshing.")
            self.driver.refresh()
            random_delay()
            return

        # Navigate to the requested page
        logger.info(f"Opening '{page}' page.")
        self.driver.get(self.BASE_URL)
        random_delay()
        self.on_page = "main"

        if page != "main":
            logger.info(f"Navigating to the '{page}' subpage.")
            xpath = self.subpages_buttons_xpath_dict.get(page)
            try:
                subpage_el = self.driver.find_element(By.XPATH, xpath)
                subpage_el.click()
                random_delay()
                self.on_page = page
            except NoSuchElementException:
                logger.error(f"Subpage '{page}' button not found. XPath: {xpath}")
            except Exception as e:
                logger.error(f"Failed to open subpage '{page}': {e}")

    def check_current_details_name(self) -> Optional[str]:
        """
        TBA
        """
        logger.info("Checking current details name.")
        self.open("bronevik")

        if not self.on_page == "bronevik":
            logger.error("Can't check details name, driver is not on bronevik page.")
            return None

        # Get details name
        img_el = self.driver.find_element(By.XPATH, "//div[@class='exchange']//div[@class='get']//img")
        details_name = img_el.get_attribute("alt")
        logger.info(f"Details name: '{details_name}'")
        return details_name

    def buy_current_details(self) -> None:
        """
        TBA
        """
        logger.info("Buying current details.")
        self.open("bronevik")

        if not self.on_page == "bronevik":
            logger.error("Can't buy details, driver is not on bronevik page.")
            return None

        # Buy details
        buy_details_el = self.driver.find_element(By.XPATH, '//button[@id="factory-build-exchange"]')
        buy_details_el.click()
        random_delay()


# add Bojara filtering and status check
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
            element = self.driver.find_element(
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
