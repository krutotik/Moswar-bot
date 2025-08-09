import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from tqdm import tqdm

from utils.custom_logging import logger
from utils.human_simulation import random_delay

# TODO: add find elements to make the code shorter like when I try to find sum of stats of the enemy
# TODO: add status of the player, searching< fighting, etc.


class Player:
    """
    Represents a Player in the Moswar game.

    This class interacts with the game's web interface using Selenium WebDriver to fetch and update various
    player attributes, such as health, energy, stats, resources, and activities.
    """

    BASE_URL = "https://www.moswar.ru/player/"

    def __init__(self, driver: WebDriver, update_info_on_init: bool = True):
        """
        Initializes the Player instance with default attributes and fetches player data.

        Parameters:
            driver (WebDriver): Selenium WebDriver instance for interacting with the game's web interface.
            update_info_on_init (bool): Whether to fetch and update player data upon initialization. Defaults to True.
        """
        self.driver = driver

        # Player level
        self.level = 0
        self.experience = 0
        self.experience_needed_to_level = 0

        # Player health and energy
        self.currenthp = 0.0
        self.currenthp_max = 0.0
        self.currenthp_prc = 0.0
        self.currentmp = 0.0
        self.currentmp_max = 0.0
        self.currentmp_prc = 0.0

        # Player stats
        self.health = 0
        self.strength = 0
        self.dexterity = 0
        self.resistance = 0
        self.intuition = 0
        self.attention = 0
        self.charism = 0

        # Player basic recourses
        self.money = 0
        self.ore = 0
        self.oil = 0
        self.honey = 0

        # Player additional recourses (TBA primary_passes and dices update, also chips)
        self.mobiles = 0
        self.stars = 0
        self.hunter_tokens = 0
        self.tooth_white = 0
        self.pet_medals = 0
        self.powers = 0
        self.patriotisms = 0
        self.debts = 0
        self.primary_passes = 0
        self.dices = 0
        self.chips = 0

        # Player acitve items
        self.pielmienies = 0
        self.tonuses = 0
        self.snickers = 0

        # Player statuses
        self.on_rest = False
        self.on_patrol = False
        self.on_work = False
        self.on_TV = False
        self.in_battle = False
        self.in_underground = False
        self.is_major = False

        # Player time left to do activities (TBA add refresh of those values)
        self.patrol_time_left = 0
        self.work_time_left = 0
        self.TV_time_left = 0

        # Update player status
        self.open()
        self.update_battle_status(is_refresh=False, verbose=False)
        self.update_underground_status(is_refresh=False, verbose=False)

        if not update_info_on_init:
            logger.warning("Player successfully initialized, however player info was not updated.")
        elif self.in_battle or self.in_underground:
            logger.warning(
                "Player successfully initialized, however information about player status was not updated. Player is in battle or underground."
            )
        else:
            self.update_health_and_energy()
            self.update_stats()
            self.update_recourses_active()
            self.update_recourses_basic()
            self.update_recourses_advanced()
            self.update_major_status()
            self.update_all_actvities_status()
            logger.info("Player successfully initialized.")

    def open(self) -> None:
        """
        This method ensures the driver is on the player page by navigating to its URL.
        """
        if self.driver.current_url != self.BASE_URL:
            logger.info("Driver is not on the player page. Going to the player.")
            self.driver.get(self.BASE_URL)
            random_delay()
        else:
            logger.info("Driver is already on the player page, refreshing.")
            self.driver.refresh()
            random_delay()

    # create dict and use setattr
    def update_health_and_energy(self, is_refresh: bool = True, verbose: bool = True) -> None:
        """
        Updates the information about player's current health and energy levels.

        Parameters:
            is_refresh (bool): Whether to refresh the page before fetching the data. Defaults to True.
            verbose (bool): Whether to log the update process. Defaults to True.
        """
        if verbose:
            logger.info("Updating player health and energy info.")
        if is_refresh:
            self.driver.refresh()
            random_delay()

        # Health
        currenthp_el = self.driver.find_element(By.XPATH, '//*[@id="personal"]//*[@id="currenthp"]')
        self.currenthp = float(currenthp_el.get_attribute("title") or 0)
        currenthp_max_el = self.driver.find_element(By.XPATH, '//*[@id="personal"]//*[@id="maxhp"]')
        self.currenthp_max = float(currenthp_max_el.get_attribute("title") or 0)
        self.currenthp_prc = self.currenthp / self.currenthp_max

        # Energy
        currentmp_el = self.driver.find_element(By.XPATH, '//*[@id="personal"]//*[@id="currenttonus"]')
        self.currentmp = float(currentmp_el.text)
        currentmp_max_el = self.driver.find_element(By.XPATH, '//*[@id="personal"]//*[@id="maxenergy"]')
        self.currentmp_max = float(currentmp_max_el.text)
        self.currentmp_prc = self.currentmp / self.currentmp_max

    def update_stats(self) -> None:
        """
        Updates player's stats, including health, strength, dexterity, resistance,
        intuition, attention, charism, level, and experience.
        """
        logger.info("Updating player stats info.")
        self.open()

        # Map stat types to attributes and selectors
        stats_map = {
            "health": "li.stat.odd[data-type='health'] .label span.num",
            "strength": "li.stat[data-type='strength'] .label span.num",
            "dexterity": "li.stat.odd[data-type='dexterity'] .label span.num",
            "resistance": "li.stat[data-type='resistance'] .label span.num",
            "intuition": "li.stat.odd[data-type='intuition'] .label span.num",
            "attention": "li.stat[data-type='attention'] .label span.num",
            "charism": "li.stat.odd[data-type='charism'] .label span.num",
        }

        # Extract stats using the map
        for stat, selector in stats_map.items():
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            setattr(self, stat, int(element.text))

        # Level
        level_el = self.driver.find_element(
            By.XPATH,
            "//h3[@class='curves clear']/span[@class='user ']/span[@class='level']",
        )
        self.level = int(level_el.text.strip("[]"))

        # Experience
        experience_el = self.driver.find_element(By.XPATH, "//div[@class='exp']")
        current, needed = map(int, experience_el.text.split(" ")[1].split("/"))
        self.experience = current
        self.experience_needed_to_level = needed

        # Warn if nearing level-up
        if needed - current <= 200:
            logger.warning("There are less than 200 experience points to level up.")

    def update_major_status(self) -> None:
        """
        Updates the information about player's "major" status based on data from the stash page.
        """
        logger.info("Updating major status.")
        self.driver.get("https://www.moswar.ru/stash/")
        random_delay()

        try:
            self.driver.find_element(By.XPATH, "//p[contains(text(), 'Ваш статус мажора закончится')]")
            self.is_major = True
        except NoSuchElementException:
            self.is_major = False

    def update_recourses_basic(self) -> None:
        """
        Updates the information about player's basic resources, including money, ore, oil, and honey.
        """
        basic_recourses_addr_dict = {
            "money": "//li[@class='tugriki-block']",
            "ore": "//li[@class='ruda-block']",
            "oil": "//li[@class='neft-block']",
            "honey": "//li[@class='med-block']",
        }

        for recourse, addr in basic_recourses_addr_dict.items():
            recourse_attr = self.driver.find_element(By.XPATH, addr).get_attribute("title")
            if recourse_attr:
                recourse_value = int(recourse_attr.split(" ")[1])
                setattr(self, recourse, recourse_value)

    # TODO: add primary_passes, dices, chips
    def update_recourses_advanced(self) -> None:
        """
        Updates the information about player's advanced resources, including mobiles, stars, hunter tokens, and others.
        """
        logger.info("Updating player advanced recourses info.")
        self.driver.get("https://www.moswar.ru/berezka/")
        random_delay()

        general_address = "//div[contains(text(), 'У вас в наличии:')]//span[@class="
        advanced_recourses_addr_dict = {
            "mobiles": general_address + "'mobila']",
            "stars": general_address + "'star']",
            "hunter_tokens": general_address + "'badge']",
            "tooth_white": general_address + "'tooth-white']",
            "pet_medals": general_address + "'pet-golden counter']",
            "powers": general_address + "'power counter']",
            "patriotisms": general_address + "'patriotism_points']",
            "debts": general_address + "'debt_points']",
        }

        for recourse, addr in advanced_recourses_addr_dict.items():
            recourse_el = self.driver.find_element(By.XPATH, addr)
            recourse_value = int(recourse_el.text.replace(",", ""))
            setattr(self, recourse, recourse_value)

    def update_recourses_active(self) -> None:
        """
        Updates the player's active resources (Pielmienies, Tonuses, Snickers) by retrieving
        their counts from the webpage. If an element is not found, the count is set to 0.

        """
        logger.info("Updating player active recourses info.")
        self.open()

        # TODO: move to class attributes to be able to use this items using use_item function
        active_recourses_addr_dict = {
            "pielmienies": "//*[@id='inventory-stat_stimulator-btn']/parent::div//div[@class='count']",
            "tonuses": "//*[@id='inventory-restoretonus-btn']/parent::div//div[@class='count']",
            "snickers": "//*[@id='inventory-snikers-btn']/parent::div//div[@class='count']",
        }

        for recourse, addr in active_recourses_addr_dict.items():
            try:
                recourse_el = self.driver.find_element(By.XPATH, addr)
                recourse_value = int(recourse_el.text.replace("#", ""))
            except NoSuchElementException:
                recourse_value = 0
            setattr(self, recourse, recourse_value)

    def update_battle_status(self, is_refresh: bool = True, verbose: bool = True) -> None:
        """
        Updates the player's in-battle status.

        If the player is currently in a battle, updates the `in_battle` attribute to True
        and logs the status. If not, sets `in_battle` to False.

        Parameters:
            is_refresh (bool): Whether to refresh the page before checking the battle status. Defaults to True.
            verbose (bool): Whether to log the update process. Defaults to True.
        """
        if verbose:
            logger.info("Updating in battle status.")

        if is_refresh:
            self.driver.refresh()
            random_delay()

        if self.driver.current_url.startswith("https://www.moswar.ru/fight/"):
            self.in_battle = True
        else:
            self.in_battle = False

        if verbose:
            logger.info(f"In battle status: {self.in_battle}")

    def update_underground_status(self, is_refresh: bool = True, verbose: bool = True) -> None:
        """
        Updates the player's in-underground status.

        Checks if the player is currently in the underground and updates the `in_underground` attribute accordingly.
        Logs the status and stops further updates if the player is underground.

        Parameters:
            is_refresh (bool): Whether to refresh the page before checking the underground status. Defaults to True.
            verbose (bool): Whether to log the update process. Defaults to True.
        """
        if is_refresh:
            self.driver.refresh()
            random_delay()

        if verbose:
            logger.info("Updating in undeground status.")

        try:
            self.driver.find_element(By.XPATH, "//span[@class='text' and text()='В туннелях метро']")
            self.in_underground = True
        except NoSuchElementException:
            self.in_underground = False

        if verbose:
            logger.info(f"In undeground status: {self.in_underground}")

    def update_work_status(self) -> None:
        """
        Updates the player's work status and remaining work time.

        Checks if the player is currently working and updates the `on_work` attribute.
        If the player is not working, retrieves the remaining work time (in hours) and updates the `work_time_left` attribute.
        Logs the work status and remaining time.
        """
        # Work status
        logger.info("Updating work status.")
        self.driver.get("https://www.moswar.ru/shaurburgers/")
        random_delay()

        try:
            self.driver.find_element(By.XPATH, "//td[@class='label' and text()='Вкалываем:']")
            self.on_work = True
        except NoSuchElementException:
            self.on_work = False

        # Work time left
        if self.on_work:
            logger.warning("Cannot update how many hours left to work, player is working.")
        else:
            try:
                select_work_minutes_el = Select(self.driver.find_element(By.NAME, "time"))
                remaining_time_el_text = [option.text for option in select_work_minutes_el.options][-1]
                match = re.search(r"(\d+)", remaining_time_el_text)
                if match:
                    self.work_time_left = int(match.group(1))
            except NoSuchElementException:
                self.work_time_left = 0  # change

        logger.info(f"Work status: {self.on_work}")
        logger.info(f"Work time left: {self.work_time_left} hours.")

    # TODO: fix this, it is not working
    def update_all_actvities_status(self) -> None:
        """
        Updates all player activity statuses, both restrictive and non-restrictive.

        First updates restrictive statuses (in-battle and underground). If the player is in
        a restrictive status, logs an error and stops further updates. Otherwise, updates
        non-restrictive statuses including patrol, work, and watching Patriot TV.

        Logs the progress and results of the updates.
        """
        logger.info("Updating all player activities status.")

        # Restrictive statuses
        self.update_battle_status(is_refresh=True)
        self.update_underground_status(is_refresh=False)

        # Non-restrictive statuses if possible
        if self.in_battle or self.in_underground:
            logger.error("Cannot update other status while in battle or underground.")
        else:
            # self.update_patrol_status()
            # self.update_watch_patriot_TV_status()
            self.update_work_status()

    # TODO: add info when was the last time this info was updated?
    def show_info(self, show_all: bool = False) -> None:
        """
        Displays information about the player's current state, including health, energy,
        resources, and activities. Optionally shows additional resources and attributes.

        Parameters:
            show_all (bool): If True, displays additional player details. Default is False.
        """
        print("Текущие состояния игрока:")
        print(f"Текущее здоровье: {self.currenthp:,}")
        print(f"Максимальное здоровье: {self.currenthp_max:,}")
        print(f"Процент здоровья: {self.currenthp_prc * 100:.2f}%")
        print(f"Текущая энергия: {self.currentmp:,}")
        print(f"Максимальная энергия: {self.currentmp_max:,}")
        print(f"Процент энергии: {self.currentmp_prc * 100:.2f}%")
        print("\n")
        print("Текущие базовые ресурсы игрока:")
        print(f"Тугрики: {self.money:,}")
        print(f"Руда: {self.ore:,}")
        print(f"Нефть: {self.oil:,}")
        print(f"Мёд: {self.honey:,}")
        print("\n")
        print(f"Текущий уровень игрока: {self.level:,}")
        print(f"Опыта до следующего уровня: {self.experience_needed_to_level - self.experience:,}")
        print("\n")
        print("Текущие активности игрока:")
        print(f"В бою: {'Да' if self.in_battle else 'Нет'}")
        print(f"В подземке: {'Да' if self.in_underground else 'Нет'}")
        print(f"Патрулирует: {'Да' if self.on_patrol else 'Нет'}")
        print(f"Работает: {'Да' if self.on_work else 'Нет'}")
        print(f"Смотрит Патриот-ТВ: {'Да' if self.on_TV else 'Нет'}")
        print(f"Статус мажора: {'Да' if self.is_major else 'Нет'}")

        print("\n")
        print("Количество оставшегося времени на актиновсти:")
        print(f"Патрулирование: {self.patrol_time_left} минут")
        print(f"Патриот-ТВ: {self.TV_time_left} часов")
        print(f"Работа: {self.work_time_left} часов")

        if show_all:
            print("\n")
            print("Текущие дополнительные ресурсы игрока:")
            print(f"Мобилы: {self.mobiles:,}")
            print(f"Звёзды: {self.stars:,}")
            print(f"Токены охотника: {self.hunter_tokens:,}")
            print(f"Белые зубы: {self.tooth_white:,}")
            print(f"Медали питомцев: {self.pet_medals:,}")
            print(f"Державы: {self.powers:,}")
            print(f"Патриотизм: {self.patriotisms:,}")
            print(f"Долги: {self.debts:,}")
            print(f"Праймари пассы: {self.primary_passes:,}")
            print(f"Кубики Москвополии: {self.dices:,}")
            print(f"Фишки в казино: {self.chips:,}")
            print("\n")
            print("Текущие активные ресурсы игрока:")
            print(f"Пельмени: {self.pielmienies:,}")
            print(f"Тонусы: {self.tonuses:,}")
            print(f"Сникерсы: {self.snickers:,}")
            print("\n")
            print("Текущие характеристики игрока:")
            print(f"Здоровье: {self.health:,}")
            print(f"Сила: {self.strength:,}")
            print(f"Ловкость: {self.dexterity:,}")
            print(f"Выносливость: {self.resistance:,}")
            print(f"Хитрость: {self.intuition:,}")
            print(f"Внимательность: {self.attention:,}")
            print(f"Харизма: {self.charism:,}")

    def restore_health(self) -> None:
        """
        Restores the player's health if it's not already at full.

        Checks the current health status, and if not full, tries to find and click
        the appropriate healing buttons to restore health.
        """
        logger.info("Restoring player health.")

        # Check current hp status
        self.update_health_and_energy(verbose=False)
        if self.currenthp_prc == 1.0:
            logger.error("Player health is full, there is no need to restore health.")
            return None

        # Try to find healing button and heal
        try:
            healing_el_1 = self.driver.find_element(
                By.XPATH,
                '//i[contains(@onclick, "showHPAlert();") and not(contains(@style, "display:none;"))]',
            )
            healing_el_1.click()
            random_delay()

            healing_el_2 = self.driver.find_element(
                By.XPATH, '//div[@class="c" and contains(text(), "Вылечиться - ")]'
            )
            healing_el_2.click()
            random_delay()
            logger.info("Player health restored.")
        except NoSuchElementException:
            logger.error("Can't restore player health, restoring button not found.")
            return None

        # Check if player health is restored
        self.update_health_and_energy(is_refresh=False, verbose=False)
        if self.currenthp_prc != 1.0:
            logger.error("Something went wrong, player health was not restored.")

    def restore_energy(self) -> None:
        """
        Restores the player's energy if it's not already full.

        Checks the current energy status and attempts to restore energy using
        different methods (tonus bottle, ore).
        """
        logger.info("Restoring player energy.")

        # Check current energy status
        self.update_health_and_energy(verbose=False)
        if self.currentmp_prc == 1.0:
            logger.error("Player energy is full, there is no need to restore energy.")
            return None

        # Try to find energy button 1
        try:
            energy_el_1 = self.driver.find_element(
                By.XPATH,
                '//i[contains(@onclick, "jobShowTonusAlert();") and not(contains(@style, "display:none;"))]',
            )
            energy_el_1.click()
            random_delay()
        except NoSuchElementException:
            logger.error("Can't restore player energy, restoring button not found.")
            return None

        # Try to use tonus bottle from inventory
        try:
            use_tonus_bottle_el = self.driver.find_element(
                By.XPATH, '//div[@class="c" and contains(., " — «Тонус+»")]'
            )
            use_tonus_bottle_el.click()
            logger.info("Player energy restored using tonus bottle.")
            random_delay()
            return None
        except NoSuchElementException:
            logger.warning("Tried to use tonus bottle from inventory, but it's not available.")

        # Try to find restore energy using ore
        try:
            restore_energy_el = self.driver.find_element(By.XPATH, '//span[@class="ruda"]')
            restore_energy_el.click()
            logger.info("Player energy restored using ore.")
            random_delay()
            return None
        except NoSuchElementException:
            logger.error("Tried to restore energy using ore, button was not found.")

    # TODO: add minus in recources when using this
    def use_item(self, item: str, times: int) -> None:
        """
        Uses a specified item from the inventory a given number of times.

        Parameters:
            item (str): The name of the item to be used.
            times (int): The number of times the item should be used.
        """
        logger.info(f"Using '{item}' for {times} times.")
        self.open()

        # Find item address TODO: create dict with item adresses in class dict?
        # add that se can use itmes only from dict with available items
        if item == "Полезный пельмень":
            logger.info("Eating pielmienies, nyam nyam.")
            item_el_addr = '//*[@id="inventory-stat_stimulator-btn"]'
        else:
            logger.error(f"Item '{item}' is not supported.")
            return None

        # Try to find item on page
        try:
            item_el = self.driver.find_element(By.XPATH, item_el_addr)
        except NoSuchElementException:
            logger.error(f"Item '{item}' is not available.")
            return None

        # Stop function if there are less items available than we want to use
        count_el = item_el.find_element(By.XPATH, "../*[@class='count']")
        count = int(count_el.text.replace("#", ""))
        if count < times:
            logger.error(f"Not enough '{item}' to use {times} times. There are only {count} available.")
            return None

        # Use items
        used_times = 0
        for i in tqdm(range(times), desc=f"Using '{item}'"):
            try:
                item_el.click()
                used_times += 1
                random_delay(2, 3)
            except Exception as e:
                logger.error("Something went wrong while using the item, stopping.")
                logger.error(e)
                return None

        logger.info(f"Used '{item}' for {used_times} times.")
        return None
