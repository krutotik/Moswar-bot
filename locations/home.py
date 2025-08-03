from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import Select
from utils.human_simulation import random_delay
from utils.custom_logging import logger
from entities.player import Player
from typing import Optional
from datetime import timedelta
from typing import Literal

# TODO:
# update description and docstrings


class Home:
    """
    Represents the 'Home' section of the game and provides methods for interacting with its pages.

    Attributes:
        player (Player): The player object representing the user in the game.
        driver (WebDriver): The Selenium WebDriver instance used for navigating and interacting with web elements.
        BASE_URL (str): The base URL for the 'Home' page.
        PAGES (set): A set of valid pages within the 'Home' section.
        subpages_buttons_xpath_dict (dict): A dictionary mapping subpage names to their respective XPath for navigation.
    """

    BASE_URL = "https://www.moswar.ru/home/"
    PAGES = {"home", "mars", "zodiac"}
    subpages_buttons_xpath_dict = {
        "mars": "//div[@class='button' and @onclick=\"AngryAjax.goToUrl('/mars2024/');\"]",
        "zodiac": "//div[@class='button' and @onclick=\"AngryAjax.goToUrl('/zodiac/');\"]",
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Home class.

        Parameters:
            player (Player): The player object representing the user in the game.
            driver (WebDriver): The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver
        self.on_page: Optional[Literal["home", "mars", "zodiac"]] = None

    # limit options which can be used here, create dict of subpage buttons to click on
    def open(self, page: Literal["home", "mars", "zodiac"] = "home") -> None:
        """
        Navigates to the specified page within the 'Home' section.

        Parameters:
            page (Literal["home", "mars", "zodiac"], optional): The name of the page to navigate to. Defaults to "home".

        Raises:
            ValueError: If the specified page is not supported.

        Notes:
            This method ensures the driver navigates to the correct page within the 'Home' section, refreshing the
            main page if necessary and clicking the appropriate button for subpages.
        """

        # Check if driver is out of home locations
        if not any(word in self.driver.current_url for word in self.PAGES):
            self.on_page = None

        # Check if page is supported
        if page not in self.PAGES:
            raise ValueError(
                f"Page '{page}' is not supported. Allowed: {', '.join(self.PAGES)}."
            )

        # Check if page is already open
        if self.on_page == page:
            logger.info(f"Driver is already on the '{page}' page, refreshing.")
            self.driver.refresh()
            random_delay()
            return

        # Navigate to the requested page
        logger.info(f"Navigating to the 'home' page.")
        self.driver.get(self.BASE_URL)
        random_delay()
        self.on_page = "home"

        if page != "home":
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

    def check_mars_trip_timer(self) -> Optional[float]:
        """
        TBA
        """
        logger.info("Checking mars trip timer.")
        self.open("mars")

        if not self.on_page == "mars":
            logger.error("Can't check mars trip timer, driver is not on mars page.")
            return None

        # Check mars trip timer
        try:
            time_element = self.driver.find_element(
                By.XPATH,
                '//div[contains(text(), "Доступно через")]/span',
            )
            time_text = time_element.text
            time_hours = int(time_text.split(":")[0])
            time_minutes = int(time_text.split(":")[1])
            logger.info(
                f"Player can take a trip to Mars in {time_hours} hours and {time_minutes} minutes."
            )
        except NoSuchElementException:
            # TBA - add when timer is there, check if it dissapears, if so, then we can add here message that tattoo is available
            time_hours = 0
            time_minutes = 0
            pass

        time_seconds = timedelta(hours=time_hours, minutes=time_minutes).total_seconds()
        return time_seconds
