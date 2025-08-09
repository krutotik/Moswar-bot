from typing import Literal, Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from entities.player import Player
from schemas.alley import EnemySearchType, ResetTimerType
from utils.custom_logging import logger
from utils.human_simulation import random_delay

# TODO:
# update description and docstrings
# address TODOs in the code
# add противостояние


class Alley:
    """
    Represents the 'Alley' location in the game, providing methods for interacting with its features such as timers, enemy search, patrol, caravan, and Patriot TV.

    Attributes:
        player: Player object representing the user.
        driver: Selenium WebDriver for browser automation.
        BASE_URL: Base URL for the Alley page.
    """

    # TODO: optimize locators if possible
    BASE_URL = "https://www.moswar.ru/alley/"
    LOCATORS: dict[str, tuple[str, str]] = {
        # Rest timers
        "rest_timer": (By.XPATH, "//span[@class='timer' and contains(@trigger, 'end_alley_cooldown')]"),
        "rest_reset_enegry": (By.XPATH, "//div[@onclick=\"cooldownReset('tonus');\"]"),
        "rest_reset_enegry_cost": (By.XPATH, "//span[@class='tonus']"),
        "rest_reset_snikers": (By.XPATH, "//div[@onclick=\"cooldownReset('snikers');\"]"),
        # Enemy search start
        "enemy_weak": (By.CSS_SELECTOR, ".button-big.btn.f1"),
        "enemy_equal": (By.CSS_SELECTOR, ".button-big.btn.f2"),
        "enemy_strong": (By.CSS_SELECTOR, ".button-big.btn.f3"),
        "enemy_major_bar": (By.ID, "search-enemy-bar"),
        "enemy_major_bar_toggle": (
            By.XPATH,
            "//span[@class='dashedlink' and @onclick='toggleSearchEnemyBar();']",
        ),
        "enemy_level_min": (By.NAME, "minlevel"),
        "enemy_level_max": (By.NAME, "maxlevel"),
        "enemy_level_find": (By.XPATH, '//div[contains(text(), "Искать противника")]'),
        # "enemy_name_input": "TBA",
        # "enemy_name_find": "TBA",
        # Enemy search end
        "enemy_stats_table": (
            By.XPATH,
            '//td[@class="fighter2-cell"]//ul[@class="stats"]//span[@class="num"]',
        ),
        "enemy_find_another": (By.XPATH, '//a[contains(@href, "/alley/search/again/")]'),
        "enemy_attack": (By.XPATH, "//div[@class='button button-fight']"),
        # Patrol
        "patrol_start_button": (By.XPATH, '//button[@id="alley-patrol-button" and @class="button"]'),
        # "patrol_leave_button": "TBA",
        "patrol_select_minutes": (By.XPATH, '//*[@id="patrolForm"]/div[2]/select'),
        "patrol_active": (By.XPATH, "//td[@class='label' and text()='Патрулирование:']"),
        "patrol_time_left": (By.XPATH, '//form[@class="patrol" and @id="patrolForm"]//p[@class="timeleft"]'),
        # Caravan
        "caravan_available": (By.XPATH, "//a[@href='/desert/']"),
        "caravan_rob": (By.XPATH, "//a[contains(@href, '/desert/rob/')]"),
        "caravan_result": (By.CLASS_NAME, "text"),
        # Patriot TV
        "TV_select_hours": (By.XPATH, '//*[@id="patriottvForm"]/div/select'),
        "TV_start_button": (By.XPATH, '//*[@id="alley-patriot-button"]'),
        "TV_active": (By.XPATH, "//td[@class='label' and text()='Просмотр:']"),
        "TV_time_left": (By.XPATH, '//form[@class="patrol" and @id="patriottvForm"]//p[@class="timeleft"]'),
    }

    def __init__(self, player: Player, driver: WebDriver):
        """
        Initializes the Alley class with the player and WebDriver.

        Parameters:
            player: The player object representing the user in the game.
            driver: The Selenium WebDriver instance used for navigating and interacting with web elements.
        """
        self.player = player
        self.driver = driver

    def open(self) -> None:
        """
        Ensure the driver is on the alley page, navigating or refreshing as needed.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the alley page. Going to the alley.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the alley page, refreshing.")
            self.driver.refresh()
            random_delay()

    # FIGHTING SINGLE ENEMY
    def is_rest_active(self) -> bool:
        """
        Return True if the player is currently resting, else False.
        """
        timer_value = self.driver.find_element(*self.LOCATORS["rest_timer"]).get_attribute("timer")
        if timer_value and timer_value.count("-") > 0:
            self.player.on_rest = False
            return False
        else:
            self.player.on_rest = True
            return True

    def reset_rest_timer(self, reset_timer_type: ResetTimerType) -> None:
        """
        Reset the rest timer using energy or snickers, if possible.
        """
        if not self.is_rest_active():
            logger.error("Player is not resting, can't reset the timer.")
            return None

        # Reset
        if reset_timer_type == reset_timer_type.ENERGY:
            logger.info("Resetting energy timer by using enegry.")

            energy_cost = float(self.driver.find_element(*self.LOCATORS["rest_reset_enegry_cost"]).text)
            if self.player.currentmp < energy_cost:
                logger.error(
                    f"Not enough energy to reset the timer. Current energy: {self.player.currentmp}, required: {energy_cost}"
                )
                return None
            else:
                self.driver.find_element(*self.LOCATORS["rest_reset_enegry"]).click()
                self.player.currentmp -= energy_cost
                logger.info(f"Energy timer reset, current energy: {self.player.currentmp}")
            random_delay()

        elif reset_timer_type == reset_timer_type.SNICKERS:
            logger.info("Resetting rest timer by using sneakers.")

            if self.player.snickers == 0:
                logger.error("Player has no sneakers to reset the timer.")
                return None

            self.driver.find_element(*self.LOCATORS["rest_reset_snikers"]).click()
            self.player.snickers -= 1
            random_delay()

        # Check
        random_delay(min_time=5, max_time=6)
        self.driver.refresh()
        if not self.is_rest_active():
            logger.info("Rest timer successfully reset.")
        else:
            logger.error("Failed to reset rest timer, player is still resting.")

    def _search_enemy_by_level(
        self,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        Search for an enemy by specifying minimum and maximum level.

        Parameters:
            enemy_level_min (Optional[int]): Minimum level of the enemy to search for. If None, defaults to player level + 1.
            enemy_level_max (Optional[int]): Maximum level of the enemy to search for. If None, defaults to player level + 1.

        Behavior:
            - Ensures the search bar is visible.
            - Sets the min and max level fields.
            - Initiates the search for an enemy within the specified level range.
        """
        if not self.player.is_major:
            logger.error("Player is not a major, can't fight enemies by level.")
            return None

        # Show search bar if not displayed
        is_displ = self.driver.find_element(*self.LOCATORS["enemy_major_bar"]).get_attribute("style")
        if is_displ == "display: none;":
            logger.info("Search enemy bar is hidden. Clicking to display it.")
            self.driver.find_element(*self.LOCATORS["enemy_major_bar_toggle"]).click()
            random_delay()

        # Set enemy min level
        enemy_level_min = enemy_level_min or self.player.level + 1
        enemy_level_min_str = str(enemy_level_min)

        set_enemy_level_min_el = self.driver.find_element(*self.LOCATORS["enemy_level_min"])
        curr_value_min = set_enemy_level_min_el.get_attribute("value")
        if curr_value_min != enemy_level_min_str:
            logger.info(f"Enemy minimum level is not {enemy_level_min_str}. Updating it.")
            set_enemy_level_min_el.clear()
            set_enemy_level_min_el.send_keys(enemy_level_min_str)
            random_delay()

        # Set enemy max level
        enemy_level_max = enemy_level_max or self.player.level + 1
        enemy_level_max_str = str(enemy_level_max)

        set_enemy_level_max_el = self.driver.find_element(*self.LOCATORS["enemy_level_max"])
        value_max = set_enemy_level_max_el.get_attribute("value")
        if value_max != enemy_level_max_str:
            logger.info(f"Enemy maximum level is not {enemy_level_max_str}. Updating it.")
            set_enemy_level_max_el.clear()
            set_enemy_level_max_el.send_keys(enemy_level_max_str)
            random_delay()

        self.driver.find_element(*self.LOCATORS["enemy_level_find"]).click()
        random_delay()

    def start_enemy_search(
        self,
        enemy_search_type: EnemySearchType,
        enemy_level_min: Optional[int] = None,
        enemy_level_max: Optional[int] = None,
    ) -> None:
        """
        Start an enemy search of the specified type.

        Parameters:
            enemy_search_type (EnemySearchType): Type of enemy search (weak, equal, strong, by name, by level).
            enemy_level_min (Optional[int]): Minimum level for BY_LEVEL search. Defaults to player level + 1 if not provided.
            enemy_level_max (Optional[int]): Maximum level for BY_LEVEL search. Defaults to player level + 1 if not provided.

        Behavior:
            - Checks if the player is resting.
            - Initiates the appropriate search based on the type.
            - Validates navigation to the search page.
        """
        logger.info(f"Starting enemy search of type: {enemy_search_type}")

        if self.is_rest_active():
            logger.error("Player is resting, can't start enemy search.")
            return None

        # Search
        if enemy_search_type == enemy_search_type.WEAK:
            self.driver.find_element(*self.LOCATORS["enemy_weak"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.EQUAL:
            self.driver.find_element(*self.LOCATORS["enemy_equal"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.STRONG:
            self.driver.find_element(*self.LOCATORS["enemy_strong"]).click()
            random_delay()
        elif enemy_search_type == enemy_search_type.BY_NAME:
            pass
        elif enemy_search_type == enemy_search_type.BY_LEVEL:
            self._search_enemy_by_level(enemy_level_min, enemy_level_max)

        if not self.driver.current_url.startswith(self.BASE_URL + "search/"):
            logger.error("Failed to start enemy search, driver is not on the search page.")

        # Check
        # TODO: check if on search page

    # TODO: add check if on search page
    def finish_enemy_search(self) -> None:
        """
        Complete the enemy search and attack a suitable enemy.
        """
        player_stats_sum = (
            self.player.health
            + self.player.strength
            + self.player.dexterity
            + self.player.resistance
            + self.player.intuition
            + self.player.attention
            + self.player.charism
        )

        # Search
        finished_enemy_search = False
        while not finished_enemy_search:
            enemy_stat_elements = self.driver.find_elements(*self.LOCATORS["enemy_stats_table"])
            enemy_stats_sum = sum([int(element.text) for element in enemy_stat_elements])

            if enemy_stats_sum > player_stats_sum:
                logger.warning("Enemy stats are too high, trying to find another enemy.")
                self.driver.find_element(*self.LOCATORS["enemy_find_another"]).click()
                random_delay()
            else:
                logger.info("Enemy found, attacking.")
                finished_enemy_search = True

        # Attack
        attack_enemy_el = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.LOCATORS["enemy_attack"])
        )
        attack_enemy_el.click()
        self.player.on_rest = True
        random_delay()

        # Return to the alley
        self.open()
        random_delay()
        logger.info("Finished fight with random enemy.")

    # PATROL
    def is_patrol_active(self) -> bool:
        """
        Return True if the player is currently on patrol, else False.
        """
        try:
            self.driver.find_element(*self.LOCATORS["patrol_active"])
            self.player.on_patrol = True
            return True
        except NoSuchElementException:
            self.player.on_patrol = False
            return False

    # TODO: check if correct when no time left
    def get_patrol_time_left(self) -> int:
        """
        Get the remaining patrol time in minutes.
        """
        try:
            time_left_el = self.driver.find_element(*self.LOCATORS["patrol_time_left"])
            time_left = int(time_left_el.text.split(" ")[-2])
        except Exception:
            time_left = 0

        self.player.patrol_time_left = time_left
        return time_left

    def start_patrol(self, patrol_minutes: Literal[20, 40] = 20) -> None:
        """
        Start a patrol for the specified duration.

        Parameters:
            patrol_minutes (Literal[20, 40]): Duration of patrol in minutes. Must be 20 or 40.

        Behavior:
            - Checks for valid patrol duration and player status.
            - Ensures enough patrol time is left.
            - Selects patrol duration and starts patrol.
            - Updates player status and logs the result.
        """
        logger.info(f"Starting patrol for {patrol_minutes} minutes.")

        # Error checks
        if patrol_minutes not in [20, 40]:
            logger.error("Invalid patrol minutes. Valid options are 20 or 40 minutes.")
            return None

        if self.is_patrol_active():
            logger.error("Can't start patrol, player is already on patrol.")
            return None

        patrol_time_left = self.get_patrol_time_left()
        if patrol_time_left < patrol_minutes:
            logger.error(
                f"Can't start patrol for {patrol_minutes} minutes, only {self.player.patrol_time_left} minutes left."
            )
            return None

        # Start patrol
        patrol_minutes_str = str(patrol_minutes) + " минут"
        select_patrol_minutes_el = Select(self.driver.find_element(*self.LOCATORS["patrol_select_minutes"]))
        select_patrol_minutes_el.select_by_visible_text(patrol_minutes_str)
        random_delay()

        start_patrol_el = self.driver.find_element(*self.LOCATORS["patrol_start_button"])
        start_patrol_el.click()

        # Check
        random_delay(min_time=5, max_time=6)
        if self.is_patrol_active():
            self.player.patrol_time_left -= patrol_minutes
            logger.info(
                f"Patrol successfully started, patrol time left: {self.player.patrol_time_left} minutes."
            )
        else:
            logger.error("Failed to start patrol")

    # CARAVAN
    # TODO: test caravan functions
    def is_caravan_available(self) -> bool:
        """
        Return True if a caravan is available to rob, else False.
        """
        try:
            self.driver.find_element(*self.LOCATORS["caravan_available"])
            return True
        except NoSuchElementException:
            return False

    def rob_caravan(self) -> None:
        """
        Attempt to rob the caravan if available.

        Behavior:
            - Checks if a caravan is available.
            - Navigates through caravan robbing steps.
            - Logs the result and updates player money if successful.
            - Returns to the alley page after the attempt.
        """
        if not self.is_caravan_available():
            logger.error("No caravan available to rob.")
            return None

        try:
            caravan_el_1 = self.driver.find_element(*self.LOCATORS["caravan_available"])
            caravan_el_1.click()
            random_delay()

            caravan_el_2 = self.driver.find_element(*self.LOCATORS["caravan_rob"])
            caravan_el_2.click()
            random_delay()

            result_text = self.driver.find_element(*self.LOCATORS["caravan_result"]).text
            if result_text.startswith("К сожалению"):
                logger.info("Caravan farm failed :(")
            else:
                logger.info(f"Caravan farm successfully completed. Result: {result_text}")
                self.player.money += 0  # TODO: Update with actual money farmed
        except NoSuchElementException:
            logger.error("Error while trying to rob the caravan")

        self.open()

    # PATRIOT TV
    def is_TV_active(self) -> bool:
        """
        Return True if the player is currently watching Patriot TV, else False.
        """
        try:
            self.driver.find_element(*self.LOCATORS["TV_active"])
            self.player.on_TV = True
            return True
        except NoSuchElementException:
            self.player.on_TV = False
            return False

    # TODO: check if correct
    def get_TV_time_left(self) -> int:
        """
        Get the remaining Patriot TV watching time in minutes.
        """
        try:
            time_left_el = self.driver.find_element(*self.LOCATORS["TV_time_left"])
            time_left = int(time_left_el.text.split(" ")[-2])
        except Exception:
            time_left = 0

        self.player.TV_time_left = time_left
        return time_left

    # TODO: check if correct
    def start_watching_TV(self, watch_hours: Literal[1] = 1) -> None:
        """
        Start a Patriot TV session for 1 hour if possible.

        Parameters:
            watch_hours (Literal[1]): Number of hours to watch. Only 1 is allowed.

        Behavior:
            - Checks for valid watch duration and player status.
            - Ensures enough TV time is left.
            - Selects watch duration and starts session.
            - Updates player status and logs the result.
        """
        logger.info(f"Starting Patriot TV session for {watch_hours} hour(s).")

        # Error checks
        if watch_hours != 1:
            logger.error("Invalid watch hours. Only 1 hour is allowed.")
            return None

        if self.is_TV_active():
            logger.error("Can't start watching Patriot TV, player is already watching.")
            return None

        watch_time_left = self.get_TV_time_left()
        if watch_time_left < watch_hours:
            logger.error(
                f"Can't start watching Patriot TV for {watch_hours} hour(s), only {self.player.TV_time_left} hours left."
            )
            return None

        # Start watching TV
        select_watch_hours_el = Select(self.driver.find_element(*self.LOCATORS["TV_select_hours"]))
        select_watch_hours_el.select_by_visible_text(f"{watch_hours} час")
        random_delay()

        start_watch_el = self.driver.find_element(*self.LOCATORS["TV_start_button"])
        start_watch_el.click()

        # Check
        random_delay(min_time=5, max_time=6)
        if self.is_TV_active():
            self.player.TV_time_left -= watch_hours
            logger.info(
                f"Patriot TV session successfully started, time left: {self.player.TV_time_left} hours."
            )
        else:
            logger.error("Failed to start Patriot TV session")
