from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

from schemas.player import RestoreEnergyType
from utils.custom_logging import logger
from utils.human_simulation import random_delay

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
        # Waiting for battle
        "waiting_for_battle": (
            By.XPATH,
            "//*[span[@class='text' and text()='Ожидание боя'] and span[@class='timeleft']]",
        ),
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
        # Player inventory resources TODO: update to allow using those items too, not only for counting
        "pielmienies": (
            By.XPATH,
            '//*[@id="inventory-stat_stimulator-btn"]/parent::div//div[@class="count"]',
        ),
        "tonuses": (By.XPATH, '//*[@id="inventory-restoretonus-btn"]/parent::div//div[@class="count"]'),
        "snickers": (By.XPATH, '//*[@id="inventory-snikers-btn"]/parent::div//div[@class="count"]'),
        # Health restoration
        "restore_health_button": (
            By.XPATH,
            '//i[contains(@onclick, "showHPAlert();") and not(contains(@style, "display:none;"))]',
        ),
        "restore_health_confirm": (By.XPATH, '//div[@class="c" and contains(text(), "Вылечиться - ")]'),
        # Energy restoration
        "restore_energy_button": (
            By.XPATH,
            '//i[contains(@onclick, "jobShowTonusAlert();") and not(contains(@style, "display:none;"))]',
        ),
        "restore_energy_tonus": (By.XPATH, '//div[@class="c" and contains(., " — «Тонус+»")]'),
        "restore_energy_ore": (By.XPATH, '//div[@class="c" and .//span[@class="ruda" and text()="10"]]'),
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
        self.awaits_battle = False

        # Player time left to do activities
        self.patrol_time_left = 0
        self.work_time_left = 0
        self.TV_time_left = 0

        # Update player status
        self.update_player_info() if update_info_on_init else None
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

    def is_opened(self) -> bool:
        """
        Checks if the current driver URL is the player page.
        """
        return self.driver.current_url == self.BASE_URL

    def open(self) -> None:
        """
        This method ensures the driver is on the player page by navigating to its URL.
        """
        if not self.is_opened():
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

        try:
            # Stats
            stats_list = [
                "health",
                "strength",
                "dexterity",
                "resistance",
                "intuition",
                "attention",
                "charism",
            ]
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

        except NoSuchElementException as e:
            logger.error(f"Error updating player stats: {e}")

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
                setattr(self, recourse, value)
            except NoSuchElementException:
                logger.error(f"Basic recourse '{recourse}' not found on the page, it will not be updated.")

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
                setattr(self, recourse, value)
            except Exception:
                logger.error(f"Advanced recourse '{recourse}' not found on the page, it will not be updated.")

    # TODO: travel_passes, moskowpoly_dices, irons
    def update_recourses_inventory(self) -> None:
        """
        Updates player's resources which can be found only in the inventory.
        """
        logger.info("Updating player inventory recourses info.")

        inventory_recourses = ["pielmienies", "tonuses", "snickers"]
        for recourse in inventory_recourses:
            try:
                value = int(self.driver.find_element(*self.LOCATORS[recourse]).text.replace("#", ""))
                setattr(self, recourse, value)
            except NoSuchElementException:
                logger.error(
                    f"Inventory recourse '{recourse}' not found on the page, it will not be updated."
                )

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

    def is_waiting_for_battle(self, is_refresh: bool = False) -> bool:
        """
        Return True if the player is currently waiting for a battle, else False.
        """
        if is_refresh:
            self.driver.refresh()
            random_delay()

        try:
            self.driver.find_element(*self.LOCATORS["waiting_for_battle"])
            self.awaits_battle = True
            return True
        except NoSuchElementException:
            self.awaits_battle = False
            return False

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

    def update_actvities_status_blocking(self, is_refresh: bool = True) -> None:
        """
        Updates player blocking activities statuses.
        """
        self.is_in_battle(is_refresh)
        self.is_waiting_for_battle(is_refresh=False)
        self.is_in_underground(is_refresh=False)

    def update_actvities_status_non_blocking(self) -> None:
        """
        Updates player non-blocking activities statuses
        """
        from locations.alley import Alley
        from locations.locations_secondary import Shaurburgers

        logger.info("Updating player non-blocking activities statuses.")

        self.update_actvities_status_blocking(is_refresh=False)
        if self.in_battle or self.in_underground:
            logger.error("Cannot update other statuses while in battle or underground.")
            return

        alley = Alley(self, self.driver)
        alley.open()
        self.on_patrol = alley.is_patrol_active()
        self.patrol_time_left = alley.get_patrol_time_left()
        self.on_TV = alley.is_TV_active()
        self.TV_time_left = alley.get_TV_time_left()

        work = Shaurburgers(self, self.driver)
        work.open()
        self.on_work = work.is_work_active()
        self.work_time_left = work.get_work_time_left()

    def update_player_info(self) -> None:
        """
        Updates all player information, including health, energy, stats, resources, and activities.
        """
        logger.info("Updating all player information.")
        self.update_actvities_status_blocking(is_refresh=True)

        if self.in_battle or self.in_underground:
            logger.error("Cannot update player info while in battle or underground.")
            return None

        self.open()
        self.update_health_and_energy(is_refresh=False)
        self.update_stats()
        self.update_recourses_inventory()
        self.update_recourses_basic()
        self.update_recourses_advanced()
        self.update_major_status()
        self.update_actvities_status_non_blocking()

    def show_info(self, show_all: bool = False) -> None:
        """
        Displays information about the player's current state, including health, energy,
        resources, and activities. Optionally shows additional resources and attributes.

        Parameters:
            show_all (bool): If True, displays additional player details. Default is False.
        """
        info = [
            "Текущие состояния игрока:",
            f"Здоровье: {self.hp_current:,}/{self.hp_max:,} ({self.hp_current_prc * 100:.2f}%)",
            f"Энергия: {self.mp_current:,}/{self.mp_max:,} ({self.mp_current_prc * 100:.2f}%)",
            "",
            "Текущие базовые ресурсы игрока:",
            f"Тугрики: {self.money:,}",
            f"Руда: {self.ore:,}",
            f"Нефть: {self.oil:,}",
            f"Мёд: {self.honey:,}",
            "",
            f"Текущий уровень игрока: {self.level:,}",
            f"Опыта до следующего уровня: {self.experience_needed_to_level - self.experience:,}",
            "",
            "Текущие активности игрока:",
            f"В бою: {'Да' if self.in_battle else 'Нет'}",
            f"В подземке: {'Да' if self.in_underground else 'Нет'}",
            f"Ожидает боя: {'Да' if self.awaits_battle else 'Нет'}",
            f"Патрулирует: {'Да' if self.on_patrol else 'Нет'}",
            f"Работает: {'Да' if self.on_work else 'Нет'}",
            f"Смотрит Патриот-ТВ: {'Да' if self.on_TV else 'Нет'}",
            f"Статус мажора: {'Да' if self.is_major else 'Нет'}",
            "",
            "Количество оставшегося времени на актиновсти:",
            f"Патрулирование: {self.patrol_time_left} минут",
            f"Патриот-ТВ: {self.TV_time_left} часов",
            f"Работа: {self.work_time_left} часов",
        ]

        if show_all:
            info += [
                "",
                "Текущие дополнительные ресурсы игрока:",
                f"Мобилы: {self.mobiles:,}",
                f"Звёзды: {self.stars:,}",
                f"Токены охотника: {self.hunter_tokens:,}",
                f"Белые зубы: {self.tooth_white:,}",
                f"Медали питомцев: {self.pet_medals:,}",
                f"Державы: {self.powers:,}",
                f"Патриотизм: {self.patriotisms:,}",
                f"Долги: {self.debts:,}",
                f"Фишки в казино: {self.casino_chips:,}",
                "",
                "Текущие ресурсы игрока  из инвенторя:",
                f"Пельмени: {self.pielmienies:,}",
                f"Тонусы: {self.tonuses:,}",
                f"Сникерсы: {self.snickers:,}",
                f"(Кругосветка) Смена босса: {self.travel_shuffles:,}",
                f"(Кругосветка) Праймари пассы: {self.travel_passes:,}",
                f"Кубики Москвополии: {self.moskowpoly_dices:,}",
                "",
                "Текущие характеристики игрока:",
                f"Здоровье: {self.health:,}",
                f"Сила: {self.strength:,}",
                f"Ловкость: {self.dexterity:,}",
                f"Выносливость: {self.resistance:,}",
                f"Хитрость: {self.intuition:,}",
                f"Внимательность: {self.attention:,}",
                f"Харизма: {self.charism:,}",
            ]

        print("\n".join(info))

    # ------------------------
    # PLAYER ACTIONS
    # ------------------------
    def restore_health(self) -> None:
        """
        Restores the player's health if it's not already at full.
        """
        logger.info("Restoring player health.")

        self.update_health_and_energy()
        if self.hp_current_prc == 1.0:
            logger.error("Player health is full, there is no need to restore health.")
            return None

        self.driver.find_element(*self.LOCATORS["restore_health_button"]).click()
        random_delay()

        self.driver.find_element(*self.LOCATORS["restore_health_confirm"]).click()
        random_delay()

        self.update_health_and_energy(is_refresh=False)
        if self.hp_current_prc != 1.0:
            logger.error("Something went wrong, player health was not restored.")
        else:
            self.money -= 100

    # TODO: fix ore, now it works even for honey
    def restore_energy(self, restore_by: RestoreEnergyType) -> None:
        """
        Restores the player's energy if it's not already full.

        Parameters:
            restore_by (RestoreEnergyType): The type of energy restoration to use (TONUS or ORE).
        """
        logger.info("Restoring player energy.")

        self.update_health_and_energy()
        if self.mp_current_prc == 1.0:
            logger.error("Player energy is full, there is no need to restore energy.")
            return None

        self.driver.find_element(*self.LOCATORS["restore_energy_button"]).click()
        random_delay()

        try:
            self.driver.find_element(
                *self.LOCATORS[f"restore_energy_{RestoreEnergyType.TONUS.value}"]
            ).click()
            random_delay()
        except NoSuchElementException:
            logger.error(f"Energy restore type '{restore_by}' is not available.")
            return None

        self.update_health_and_energy(is_refresh=False)
        if self.mp_current_prc != 1.0:
            logger.error(f"Something went wrong, player energy could not be restored using {restore_by}.")
        else:
            logger.info(f"Player energy successfully restored using {restore_by}.")
            if restore_by == RestoreEnergyType.TONUS:
                self.tonuses -= 1
            elif restore_by == RestoreEnergyType.ORE:
                self.ore -= 1

    # TODO: refactor function + add minus in recources when using this
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
