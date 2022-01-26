from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
from openpyxl import load_workbook


def read_excel_file(path_to_file: str):
	return pd.read_excel(path_to_file, sheet_name="bet games", index_col=0)


def write_to_file(path_to_file: str, dataframe: pd.DataFrame):
	book = load_workbook(path_to_file)
	writer = pd.ExcelWriter(path_to_file, engine='openpyxl')
	writer.book = book
	writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
	dataframe.to_excel(writer, "all games")
	writer.save()


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


def return_handicap_element_index(i):
	if i == 1:
		return 0
	elif i == 2:
		return 3


def bet(games: pd.DataFrame, username: str, password: str):

	# web driver init start
	driver = Firefox()
	actions = ActionChains(driver)
	driver.maximize_window()

	driver.get("https://sports.bwin.de/en/sports/live/basketball-7")

	time.sleep(7)

	driver.find_element(By.ID, "onetrust-accept-btn-handler").click()

	# get number of currently live games
	class_live = "live-icon"
	live_games_number = len(driver.find_elements(By.CLASS_NAME, class_live))

	# go through all live games and bet if set
	for i in range(live_games_number):
		time.sleep(5)

		# sort games by time

		sort_toggle_xpath = "/html/body/vn-app/vn-dynamic-layout-single-slot[4]/vn-main/main/div/ms-main/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-live/ms-live-event-list/div/ms-grid/ms-grid-header/div/ms-sort-selector/div[2]/div[2]/div[2]"
		driver.find_element(By.XPATH, sort_toggle_xpath).click()

		time.sleep(1)

		# get all currently available games
		class_game = "participants-pair-game"
		all_games = driver.find_elements(By.CLASS_NAME, class_game)

		# scroll into view
		desired_y = (all_games[i].size['height'] / 2) + all_games[i].location['y']
		current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
			'return window.pageYOffset')
		scroll_y_by = desired_y - current_y
		driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)

		# end scroll
		time.sleep(1)

		# check if game is on list to bet on
		team_to_bet_on_index = 0
		current_index_in_book = -1

		# print("Game:", all_games[i].text)

		for j in range(len(games.index)):
			if games["Team1"][j] in all_games[i].text and games["Team2"][j] in all_games[i].text:
				# print("True")
				team_to_bet_on_index = int(games["Bet team"][j])
				current_index_in_book = j
				all_games[i].click()
				break
			else:
				# print("False")
				continue

		# wait to load game page
		time.sleep(5)

		# go to next game if this one is not on the list to bet on
		if team_to_bet_on_index == 0:
			continue

		# get spread values

		class_handicap = "name"
		class_score = "score-counter"
		class_bet_size = "stake-input-value"
		class_login_button = "betslip-place-button"
		email_field_name = "username"
		password_field_name = "password"
		class_login_button_2 = "login"

		score = int(driver.find_elements(By.CLASS_NAME, class_score)[team_to_bet_on_index - 1].text.replace("\n", " ").split(" ")[0])
		handicaps = driver.find_elements(By.CLASS_NAME, class_handicap)

		if len(handicaps) > 0:
			handicap = float(handicaps[return_handicap_element_index(team_to_bet_on_index)].text.replace(",", "."))
			target_handicap = float(str(games["Spread"][current_index_in_book]).replace(",", "."))
			if handicap >= target_handicap:
				if score <= int(games["Max score"][current_index_in_book]):
					# select bet
					handicaps[return_handicap_element_index(team_to_bet_on_index)].click()

					# enter bet amount
					driver.find_element(By.CLASS_NAME, class_bet_size).send_keys(float(games["Bet size"][current_index_in_book]))

					# find login button
					login_button = driver.find_element(By.CLASS_NAME, class_login_button)

					# scroll it into view
					desired_y = (login_button.size['height'] / 2) + login_button.location['y']
					current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
						'return window.pageYOffset')
					scroll_y_by = desired_y - current_y
					driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
					time.sleep(1)

					# click login button
					login_button.click()

					# enter login info
					driver.find_element(By.NAME, email_field_name).send_keys(username)
					driver.find_element(By.NAME, password_field_name).send_keys(password)

					# click to login
					driver.find_element(By.CLASS_NAME, class_login_button_2).click()

					time.sleep(5)

		else:
			print("Betting locked for this game!")

		# go back to main site
		driver.get("https://sports.bwin.de/en/sports/live/basketball-7")

	driver.quit()


def main():
	title = r"""
	__________        __    __  .__                 __________        __   
	\______   \ _____/  |__/  |_|__| ____    ____   \______   \ _____/  |_ 
	|    |  _// __ \   __\   __\  |/    \  / ___\   |    |  _//  _ \   __\
	|    |   \  ___/|  |  |  | |  |   |  \/ /_/  >  |    |   (  <_> )  |  
	|______  /\___  >__|  |__| |__|___|  /\___  /   |______  /\____/|__|  
	   	   \/     \/                   \//_____/           \/             
	""" + "\n" + "source: 'github.com/Bug18/betBot'"

	print(title)

	status = False
	path = ".\\games.xlsx"

	refresh_list = input("Refresh list of all available games? (y/n) >> ")
	if refresh_list == "y":
		print("Fetching and saving all available games... Please wait...\n")
		get_games(path)
		print("Games fetched and saved into games.xlsx in 'all games' sheet\n")

	command = input("Enter 'start' after modifying, saving and closing 'bet games' sheet >> ")

	while not status:
		if command != "start":
			command = input("Enter 'start' after modifying, saving and closing 'bet games' sheet >> ")
		else:
			status = True

	usernm = input("Enter app user id or email >> ")
	passwd = input("Enter app password >> ")

	games = read_excel_file(path)

	print("Bot starting... To stop it just kill entire program :P\n")

	while status:
		print("Starting new cycle...\n")
		bet(games, usernm, passwd)
		print("Waiting...\n")

		# waits before next cycle
		time.sleep(180)


if __name__ == '__main__':
	main()
