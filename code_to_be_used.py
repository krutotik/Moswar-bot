# driver.get("https://www.moswar.ru/neftlenin/")
# # combine in one line later

# # Press "Атаковать"
# neft_attack_el_1 = driver.find_element(By.XPATH, '//div[contains(@class, "enemy-place fight") and not(contains(@style, "display: none"))]//div[text()="Атаковать"]')
# neft_attack_el_1.click()

# # Press "Напасть"
# neft_attack_el_2 = driver.find_element(By.XPATH, '//div[@id="content"]//div[starts-with(@class, "lenin-alert-attack") and not(contains(@style, "display: none"))]//button[1]')
# neft_attack_el_2.click()

# # Return to neft page
# skip_el = driver.find_element(By.XPATH, '//i[@onclick="fightForward();"]')
# skip_el.click()

# to_neft_el = driver.find_element(By.XPATH, '//div[text()="Нефтепровод им. Ленина"]')
# to_neft_el.click()

# for el in neft_attack_el_2:
#     print(el.text)

# item_el_addr = '//*[@id="inventory-stat_stimulator-btn"]'
# item_el = driver.find_element(By.XPATH, item_el_addr)
# parent_el = item_el.find_element(By.XPATH, "..") #ADD TO NOTES!
# # Locate the item element
# item_element = driver.find_element(By.XPATH, '//*[@id="inventory-stat_stimulator-btn"]')

# # Locate the count element relative to the item element's parent
# count_element = item_element.find_element(By.XPATH, "../*[@class='count']")
