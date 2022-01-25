import requests
import selenium
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
import time
import pandas as pd




def read_excel_file(path_to_file: str):
	teams_frame = pd.read_excel(path_to_file)
	print(teams_frame)


driver = Firefox()
driver.get("https://sports.bwin.de/en/sports/basketball-7")

time.sleep(5)

class_team_names = "participants-pair-game"


handicap = driver.find_elements(By.CLASS_NAME, class_team_names)

for elem in handicap:
	print(elem.text + "\n")
