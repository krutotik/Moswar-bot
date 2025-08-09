from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
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
    LOCATORS = {
        # Health and Energy
        "hp_current": (By.XPATH, '//*[@id="personal"]//*[@id="currenthp"]'),
        "hp_max": (By.XPATH, '//*[@id="personal"]//*[@id="maxhp"]'),
        "mp_current": (By.XPATH, '//*[@id="personal"]//*[@id="currenttonus"]'),
        "mp_max": (By.XPATH, '//*[@id="personal"]//*[@id="maxenergy"]'),
        "stats": (By.CSS_SELECTOR, "li.stat"),
        # Level related
        "level": (By.XPATH, "//h3[@class='curves clear']/span[@class='user ']/span[@class='level']"),
        "experience": (By.XPATH, "//div[@class='exp']"),
        # Major status
        "major_status": (By.XPATH, "//p[contains(text(), 'Ваш статус мажора закончится')]"),
        # Player basic resources
        "money": (By.XPATH, "//li[@class='tugriki-block']"),
        "ore": (By.XPATH, "//li[@class='ruda-block']"),
        "oil": (By.XPATH, "//li[@class='neft-block']"),
        "honey": (By.XPATH, "//li[@class='med-block']"),
        # Player advanced resources
        "base": (By.XPATH, "//div[contains(text(), 'У вас в наличии:')]"),
        "mobiles": (By.XPATH, "//span[@class='mobila']"),
        "stars": (By.XPATH, "//span[@class='star']"),
        "hunter_tokens": (By.XPATH, "//span[@class='badge']"),
        "tooth_white": (By.XPATH, "//span[@class='tooth-white']"),
        "pet_medals": (By.XPATH, "//span[@class='pet-golden counter']"),
        "powers": (By.XPATH, "//span[@class='power counter']"),
        "patriotisms": (By.XPATH, "//span[@class='patriotism_points']"),
        "debts": (By.XPATH, "//span[@class='debt_points']"),
        # Player inventory resources
        "pielmienies": (
            By.XPATH,
            '//*[@id="inventory-stat_stimulator-btn"]/parent::div//div[@class="count"]',
        ),
        "tonuses": (By.XPATH, '//*[@id="inventory-restoretonus-btn"]/parent::div//div[@class="count"]'),
        "snickers": (By.XPATH, '//*[@id="inventory-snikers-btn"]/parent::div//div[@class="count"]'),
    }

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
        self.hp_max = 0.0
        self.hp_current = 0.0
        self.hp_current_prc = 1.0
        self.mp_max = 0.0
        self.mp_current = 0.0
        self.mp_current_prc = 1.0

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

        # Player additional recourses
        self.mobiles = 0
        self.stars = 0
        self.hunter_tokens = 0
        self.tooth_white = 0
        self.pet_medals = 0
        self.powers = 0
        self.patriotisms = 0
        self.debts = 0
        self.travel_shuffles = 0
        self.travel_passes = 0
        self.moskowpoly_dices = 0
        self.casino_chips = 0

        # Player acitve items
        self.pielmienies = 0
        self.tonuses = 0
        self.snickers = 0

        # Player statuses
        self.is_major = False
        self.on_rest = False
        self.on_patrol = False
        self.on_work = False
        self.on_TV = False
        self.in_battle = False
        self.in_underground = False
        self.current_blocking_activity = None  # TODO: add enum for this

        # Player time left to do activities (TODO: add refresh of those values)
        self.patrol_time_left = 0
        self.work_time_left = 0
        self.TV_time_left = 0

        # Update player status
        self.open()
        self.is_in_battle(is_refresh=False)
        self.is_in_underground(is_refresh=False)

        if not update_info_on_init:
            logger.warning("Player successfully initialized, however player info was not updated.")
        elif self.in_battle:
            logger.warning(
                "Player successfully initialized, however information about player status was not updated. Player is in battle."
            )
        elif self.in_underground:
            logger.warning(
                "Player successfully initialized, however information about player status was not updated. Player is in underground."
            )
        else:
            self.update_health_and_energy(is_refresh=False)
            self.update_recourses_basic()
            self.update_stats()
            self.update_recourses_inventory()
            self.update_recourses_advanced()
            self.update_major_status()
            self.update_all_actvities_status()
            logger.info("Player successfully initialized.")

    def __setattr__(self, name: str, value: float):
        # HP prc auto update
        object.__setattr__(self, name, value)
        if name == "hp_current":
            hp_max = getattr(self, "hp_max", None)
            if hp_max and hp_max != 0:
                object.__setattr__(self, "hp_current_prc", value / hp_max)
            else:
                object.__setattr__(self, "hp_current_prc", 1.0)

        # MP prc auto update
        if name == "mp_current":
            mp_max = getattr(self, "mp_max", None)
            if mp_max and mp_max != 0:
                object.__setattr__(self, "mp_current_prc", value / mp_max)
            else:
                object.__setattr__(self, "mp_current_prc", 1.0)

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

    # ------------------------
    # PLAYER INFO UPDATES
    # ------------------------
    def update_health_and_energy(self, is_refresh: bool = True) -> None:
        """
        Updates the information about player's current health and energy levels.
        """
        if is_refresh:
            self.driver.refresh()
            random_delay()

        # Health
        hp_max_el = self.driver.find_element(*self.LOCATORS["hp_max"])
        hp_current_el = self.driver.find_element(*self.LOCATORS["hp_current"])
        self.hp_max = float(hp_max_el.get_attribute("title") or 0)
        self.hp_current = float(hp_current_el.get_attribute("title") or 0)
        self.hp_current_prc = self.hp_current / self.hp_max

        # Energy
        mp_max_el = self.driver.find_element(*self.LOCATORS["mp_max"])
        mp_current_el = self.driver.find_element(*self.LOCATORS["mp_current"])
        self.mp_max = float(mp_max_el.text)
        self.mp_current = float(mp_current_el.text)
        self.mp_current_prc = self.mp_current / self.mp_max

    def update_stats(self) -> None:
        """
        Updates player's stats, including health, strength, dexterity, resistance,
        intuition, attention, charism, level, and experience.
        """
        logger.info("Updating player stats info.")

        # Stats
        stats_list = ["health", "strength", "dexterity", "resistance", "intuition", "attention", "charism"]
        for stat in stats_list:
            element_adress = f"//li[@data-type='{stat}']//span[@class='num']"
            element = self.driver.find_element(By.XPATH, element_adress)
            setattr(self, stat, int(element.text))

        # Level
        self.level = int(self.driver.find_element(*self.LOCATORS["level"]).text.strip("[]"))

        # Experience
        experience_el = self.driver.find_element(*self.LOCATORS["experience"])
        current, needed = map(int, experience_el.text.split(" ")[1].split("/"))
        self.experience = current
        self.experience_needed_to_level = needed

        if needed - current <= 200:
            logger.warning("There are less than 200 experience points to level up.")

    def update_major_status(self) -> None:
        """
        Updates the information about player's "major" status based on data from the stash page.

        TODO: potententially move to separate location class
        """
        logger.info("Updating major status.")
        self.driver.get("https://www.moswar.ru/stash/")
        random_delay()

        try:
            self.driver.find_element(*self.LOCATORS["major_status"])
            self.is_major = True
        except NoSuchElementException:
            self.is_major = False

    def update_recourses_basic(self) -> None:
        """
        Updates the information about player's basic resources, including money, ore, oil, and honey.
        """
        basic_recourses = ["money", "ore", "oil", "honey"]
        for recourse in basic_recourses:
            try:
                recourse_attr = self.driver.find_element(*self.LOCATORS[recourse]).get_attribute("title")
                value = int(recourse_attr.split(" ")[1]) if recourse_attr else 0
            except NoSuchElementException:
                value = 0
            setattr(self, recourse, value)

    # TODO: add casino_chips
    def update_recourses_advanced(self) -> None:
        """
        Updates the information about player's advanced resources, including mobiles, stars, hunter tokens, and others.
        TODO: potentially move to separate location classes
        """
        logger.info("Updating player advanced recourses info.")
        self.driver.get("https://www.moswar.ru/berezka/")
        random_delay()

        base_xpath = self.LOCATORS["base"][1]
        advanced_recourses = [
            "mobiles",
            "stars",
            "hunter_tokens",
            "tooth_white",
            "pet_medals",
            "powers",
            "patriotisms",
            "debts",
        ]

        for recourse in advanced_recourses:
            try:
                xpath = base_xpath + self.LOCATORS[recourse][1]
                value = int(self.driver.find_element(By.XPATH, xpath).text.replace(",", ""))
            except Exception:
                value = 0
            setattr(self, recourse, value)

    # TODO: travel_passes, moskowpoly_dices,
    def update_recourses_inventory(self) -> None:
        """
        Updates player's resources which can be found only in the inventory.
        """
        logger.info("Updating player inventory recourses info.")
        inventory_recourses = ["pielmienies", "tonuses", "snickers"]

        for recourse in inventory_recourses:
            try:
                value = int(self.driver.find_element(*self.LOCATORS[recourse]).text.replace("#", ""))
            except NoSuchElementException:
                value = 0
            setattr(self, recourse, value)

    def is_in_battle(self, is_refresh: bool = False) -> bool:
        """
        Return True if the player is currently in battle, else False.
        """
        if is_refresh:
            self.driver.refresh()
            random_delay()

        if self.driver.current_url.startswith("https://www.moswar.ru/fight/"):
            self.in_battle = True
            return True
        else:
            self.in_battle = False
            return False

        # TODO: Finish later, better to use separate function
        # if not self.in_battle and self.current_blocking_activity == "battle":
        #     self.current_blocking_activity = None

    def is_in_underground(self, is_refresh: bool = False) -> bool:
        """
        Return True if the player is currently in underground, else False.
        """
        if is_refresh:
            self.driver.refresh()
            random_delay()

        if self.driver.current_url.startswith("https://www.moswar.ru/dungeon/inside/"):
            self.in_underground = True
            return True
        else:
            self.in_underground = False
            return False

        # TODO: Finish later, better to use separate function
        # if not self.in_underground and self.current_blocking_activity == "underground":
        #     self.current_blocking_activity = None

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
        self.is_in_battle(is_refresh=True)
        self.is_in_underground(is_refresh=False)

        # Non-restrictive statuses if possible
        if self.in_battle or self.in_underground:
            logger.error("Cannot update other status while in battle or underground.")
        else:
            pass
            # self.update_patrol_status()
            # self.update_watch_patriot_TV_status()
            # self.update_work_status()

    # TODO: add info when was the last time this info was updated?
    def show_info(self, show_all: bool = False) -> None:
        """
        Displays information about the player's current state, including health, energy,
        resources, and activities. Optionally shows additional resources and attributes.

        Parameters:
            show_all (bool): If True, displays additional player details. Default is False.
        """
        print("Текущие состояния игрока:")
        print(f"Здоровье: {self.hp_current:,}/{self.hp_max:,} ({self.hp_current_prc * 100:.2f}%)")
        print(f"Энергия: {self.mp_current:,}/{self.mp_max:,} ({self.mp_current_prc * 100:.2f}%)")
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
            print(f"Фишки в казино: {self.casino_chips:,}")
            print("\n")
            print("Текущие ресурсы игрока  из инвенторя:")
            print(f"Пельмени: {self.pielmienies:,}")
            print(f"Тонусы: {self.tonuses:,}")
            print(f"Сникерсы: {self.snickers:,}")
            print(f"(Кругосветка) Смена босса: {self.travel_shuffles:,}")
            print(f"(Кругосветка) Праймари пассы: {self.travel_passes:,}")
            print(f"Кубики Москвополии: {self.moskowpoly_dices:,}")
            print("\n")
            print("Текущие характеристики игрока:")
            print(f"Здоровье: {self.health:,}")
            print(f"Сила: {self.strength:,}")
            print(f"Ловкость: {self.dexterity:,}")
            print(f"Выносливость: {self.resistance:,}")
            print(f"Хитрость: {self.intuition:,}")
            print(f"Внимательность: {self.attention:,}")
            print(f"Харизма: {self.charism:,}")

    # ------------------------
    # PLAYER ACTIONS
    # ------------------------
    def restore_health(self) -> None:
        """
        Restores the player's health if it's not already at full.

        Checks the current health status, and if not full, tries to find and click
        the appropriate healing buttons to restore health.
        """
        logger.info("Restoring player health.")

        # Check current hp status
        self.update_health_and_energy()
        if self.hp_current_prc == 1.0:
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
        self.update_health_and_energy(is_refresh=False)
        if self.hp_current_prc != 1.0:
            logger.error("Something went wrong, player health was not restored.")

    def restore_energy(self) -> None:
        """
        Restores the player's energy if it's not already full.

        Checks the current energy status and attempts to restore energy using
        different methods (tonus bottle, ore).
        """
        logger.info("Restoring player energy.")

        # Check current energy status
        self.update_health_and_energy()
        if self.mp_current_prc == 1.0:
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
        for _ in tqdm(range(times), desc=f"Using '{item}'"):
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
