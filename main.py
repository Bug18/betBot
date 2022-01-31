from selenium.webdriver import Firefox, FirefoxProfile, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
import time
import pandas as pd
from openpyxl import load_workbook
import json


def get_login():
	with open("login.json", "r") as file:
		try:
			lines = json.load(file)
		except:
			return "-1", "-1"
		return lines["username"], lines["password"]



def write_login(u, p):
	with open("login.json", "w") as file:
		data = {
			"username": u,
			"password": p
		}
		file.write(json.dumps(data))


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
	# profile = FirefoxProfile()
	# profile.set_preference("dom.popup_maximum", 0)
	options = FirefoxOptions()
	options.set_preference("dom.popup_maximum", 0)
	driver = Firefox(options=options)
	actions = ActionChains(driver)
	driver.maximize_window()

	driver.get("https://sports.bwin.de/en/sports/live/basketball-7")

	print("Please manually close popup if it appears on screen. You have 10 seconds to close it!")
	time.sleep(20)

	# close ad
	'''try:
		class_ad = "ng-star-inserted"
		el = driver.find_element(By.ID, class_ad)
		actions.move_to(el, -5, -5)
		actions.click()
		actions.perform()
		time.sleep(1)
	except:
		pass'''

	# accept all cookies
	driver.find_element(By.ID, "onetrust-accept-btn-handler").click()

	time.sleep(1)

	while True:
		print("Starting new cycle...\n")

		# check if login duration popup is up
		try:
			login_popup = driver.find_element(By.CLASS_NAME, "login-duration-content-inner")
			if login_popup:
				btns = driver.find_elements(By.CLASS_NAME, "btn")
				for btn in btns:
					if btn.text == "Continue":
						btn.click()
		except:
			pass

		# get number of currently live games
		class_live = "live-icon"
		live_games_number = len(driver.find_elements(By.CLASS_NAME, class_live))

		# go through all live games and bet if set

		bet_placed = False

		for i in range(live_games_number):
			time.sleep(5)

			# confirm bet if bet was selected
			if bet_placed:
				try:
					class_bet_button_confirm = "betslip-place-button"
					driver.find_element(By.CLASS_NAME, class_bet_button_confirm).click()
				except:
					pass

			# sort games by time
			try:
				sort_toggle_xpath = "/html/body/vn-app/vn-dynamic-layout-single-slot[4]/vn-main/main/div/ms-main/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-live/ms-live-event-list/div/ms-grid/ms-grid-header/div/ms-sort-selector/div[2]/div[2]/div[2]"
				driver.find_element(By.XPATH, sort_toggle_xpath).click()
			except:
				pass

			time.sleep(5)

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
				if games["Team1"][j] in all_games[i].text and games["Team2"][j] in all_games[i].text and int(games["Bet team"][j]) != -1:
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
				print("Next game...")
				continue

			# get spread values

			class_handicap = "name"
			class_score = "score-counter"
			class_bet_size = "stake-input-value"
			class_login_button = "betslip-place-button"
			email_field_name = "username"
			password_field_name = "password"
			login_button_xpath = "/html/body/div[6]/div[2]/div/mat-dialog-container/lh-login-dialog/lh-login/div/div/form/fieldset/section/div/button"

			score, handicaps = None, None

			try:
				score = int(driver.find_elements(By.CLASS_NAME, class_score)[team_to_bet_on_index - 1].text.replace("\n", " ").split(" ")[0])
				handicaps = driver.find_elements(By.CLASS_NAME, class_handicap)
				state = True
			except:
				print("Data not available")
				state = False

			if state:
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

							try:
								# enter login info
								driver.find_element(By.NAME, email_field_name).send_keys(username)
								driver.find_element(By.NAME, password_field_name).send_keys(password)

								# click to login
								driver.find_element(By.XPATH, login_button_xpath).click()

								time.sleep(3)

								ok_btns = driver.find_elements(By.CLASS_NAME, "btn")
								for btn in ok_btns:
									if btn.text == "OK":
										ok_btn.press()
							except:
								pass

							# make sure bot doesn't bet again on the same team
							games.at[current_index_in_book, "Bet team"] = -1
							bet_placed = True

							time.sleep(2)

				else:
					print("Betting locked for this game!")

			# go back to main site
			driver.get("https://sports.bwin.de/en/sports/live/basketball-7")

		# driver.quit()

		print("Waiting...\n")

		# waits before next cycle
		time.sleep(180)


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

	u, p = get_login()
	if u == "-1" and p == "-1":
		u = input("Enter app user id or email >> ")
		p = input("Enter app password >> ")
		write_login(u, p)

	games = read_excel_file(path)

	print("Bot starting... To stop it just kill entire program :P\n")

	bet(games, u, p)


if __name__ == '__main__':
	main()
