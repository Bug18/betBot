from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd


def read_excel_file(path_to_file: str):
	return pd.read_excel(path_to_file, index_col=0)


def write_to_file(path_to_file: str, dataframe: pd.DataFrame):
	dataframe.to_excel(path_to_file)


def get_games(path):

	driver = Firefox()
	driver.minimize_window()
	driver.get("https://sports.bwin.de/en/sports/basketball-7")

	time.sleep(5)

	class_team_names = "participants-pair-game"

	games = driver.find_elements(By.CLASS_NAME, class_team_names)
	games = [team.text.split("\n") for team in games]
	for game in games:
		if "@" in game:
			game.remove("@")

	games_frame = pd.DataFrame(data=games, columns=["Team1", "Team2"])
	write_to_file(path, games_frame)

	driver.quit()


def bet(games: pd.DataFrame):
	class_option = "option-indicator"

	driver = Firefox()
	driver.maximize_window()

	driver.get("https://sports.bwin.de/en/sports/basketball-7")

	time.sleep(7)

	driver.find_element(By.ID, "onetrust-accept-btn-handler").click()

	actions = ActionChains(driver)

	class_game = "participants-pair-game"
	all_games = driver.find_elements(By.CLASS_NAME, class_game)

	for i in range(len(all_games)):
		time.sleep(5)
		desired_y = (all_games[i].size['height'] / 2) + all_games[i].location['y']
		current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
			'return window.pageYOffset')
		scroll_y_by = desired_y - current_y
		driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
		time.sleep(5)
		print("Game:", all_games[i].text)
		if games["Team1"][i] in all_games[i].text and games["Team2"][i] in all_games[i].text:
			print("True")
			all_games[i].click()
		else:
			print("False")
			continue
		time.sleep(5)
		# decide weather to trade or no
		handicaps = driver.find_elements(By.CLASS_NAME, "name")
		print(handicaps[0].text, handicaps[3].text)
		# end of block
		driver.get("https://sports.bwin.de/en/sports/basketball-7")
		time.sleep(5)
		all_games = driver.find_elements(By.CLASS_NAME, class_game)

	driver.quit()


def main():
	title = r"""
	__________        __    __  .__                 __________        __   
	\______   \ _____/  |__/  |_|__| ____    ____   \______   \ _____/  |_ 
	|    |  _// __ \   __\   __\  |/    \  / ___\   |    |  _//  _ \   __\
	|    |   \  ___/|  |  |  | |  |   |  \/ /_/  >  |    |   (  <_> )  |  
	|______  /\___  >__|  |__| |__|___|  /\___  /   |______  /\____/|__|  
	   	   \/     \/                   \//_____/           \/             
	""" + "\n" + "source: 'github.com/Bug18/betBot' all rights reserved."

	# print(title)

	status = False
	path = "C:\\Users\\Naglic\\PycharmProjects\\betBot\\games.xlsx"

	get_games(path)

	# command = input("Enter 'start' after modifying, saving and closing excel file > ")

	'''while not status:
		if command != "start":
			command = input("Enter 'start' after modifying excel file > ")
		else:
			status = True'''

	games = read_excel_file(path)

	status = True

	while status:
		bet(games)
		time.sleep(300)


if __name__ == '__main__':
	main()
