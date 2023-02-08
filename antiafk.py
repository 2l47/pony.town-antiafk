#!/usr/bin/env python3

import imagehash
import os
import PIL.Image
import PIL.ImageGrab
import pynput
import random
import re
import schedule
import subprocess
import time



# === Configuration options ===
# Time in milliseconds to display notifications for
notification_duration = 15 * 1000
# Time in seconds before considering the user inactive
inactivity_timeout = 2 * 60
# Time in seconds to wait before executing actions depending on whether the user is active
inactive_execution_grace = 10
active_execution_grace = 15
# How many seconds early we anticipate getting disconnected by the server, to prevent waiting too long
afk_timeout_grace = 45

# === Variable instantiation ===
# Is the script currently moving the mouse?
global automating_mouse
automating_mouse = False
# Array of mouse movement coordinates from the past second
global mouse_points
mouse_points = []
# Epoch the user was last active at
global user_last_active
user_last_active = 0


# Sends a desktop notification
def notify(text, duration=notification_duration, log=True):
	if log:
		print(text)
	os.system(f"notify-send --expire-time={duration} antiafk.py \"{text}\"")


# Returns the bounding box and chat indicator hash to be used for the game
# This is lazy and inefficient code
def getGameData():
	# Detect what game we're on
	window_title = subprocess.check_output("xdotool getactivewindow getwindowname", shell=True).decode().strip()
	games = [
			{
				"name": "pony.town",
				"regex": re.compile("^. Pony Town.*"),
				# 19x16 pixels
				"bbox": (473, 1048, 492, 1064),
				"chat_indicator_image": PIL.Image.open("pony.town_chat_indicator.png")
			},
			{
				"name": "ashes.town",
				"regex": re.compile("^Ashes Town.*"),
				# 19x16 pixels: x+5, y-1 from pony.town
				"bbox": (478, 1047, 497, 1063),
				"chat_indicator_image": PIL.Image.open("ashes.town_chat_indicator.png")
			}
	]
	for game in games:
		if game["regex"].match(window_title):
			chat_indicator_hash = imagehash.average_hash(game["chat_indicator_image"])
			return game["bbox"], chat_indicator_hash
	raise RuntimeError(f"Unknown game window title: {window_title}")


# Function to check whether the user has the textbox open
def user_typing():
	bounding_box, chat_indicator_hash = getGameData()
	image = PIL.ImageGrab.grab(bbox=bounding_box)
	#image.save("capture.png")
	capture_hash = imagehash.average_hash(image)
	difference = chat_indicator_hash - capture_hash
	#print(f"[user_typing] capture_hash: {capture_hash}")
	#print(f"[user_typing] chat_indicator_hash: {chat_indicator_hash}")
	print(f"[user_typing] difference: {difference}")
	return difference == 0


# Clears past mouse coordinates every second
def clear_points():
	global mouse_points
	mouse_points = []


# Helper function to check if the user is currently active
def user_considered_active():
	return (time.time() - user_last_active) < inactivity_timeout


# Mouse event handler
def on_mouse_move(x, y):
	global automating_mouse
	global user_last_active
	if automating_mouse:
		print(f"[on_mouse_move] Script moved mouse to {x}, {y} (ignoring mouse movement)")
	else:
		mouse_points.append((x, y))
		# If the user has 100ms of activity, update the last active epoch
		if len(mouse_points) >= 100:
			now = time.time()
			# If the user is currently considered active, don't log the fact that we're updating the epoch
			if not user_considered_active():
				print(f"[on_mouse_move] User activity epoch updated: {now}")
			user_last_active = now


# Sends an initial warning and subsequent warnings before returning
def warning_timer(caller, execution_grace):
	notify(f"{caller} called, waiting {execution_grace} seconds before executing...")
	for i in range(execution_grace):
		remaining = execution_grace - i
		if remaining <= 5:
			notify(f"Returning to {caller} in {remaining} seconds...", duration=1, log=False)
		time.sleep(1)


# Turns the head back and forth to simulate player activity
def headturn():
	if user_typing():
		return notify("Not running headturn() because user is typing...")
	execution_grace = active_execution_grace if user_considered_active() else inactive_execution_grace
	warning_timer("headturn()", execution_grace)
	keypress_duration = random.randint(20, 100)
	interkey_delay = random.randint(100, 200)
	print(f"[headturn] keypress duration: {keypress_duration} ms, inter-key delay {interkey_delay} ms\n")
	os.system(f"xdotool key --clearmodifiers --delay {keypress_duration} --repeat 2 --repeat-delay {interkey_delay} h")


def main():
	# === Start monitoring user activity ===
	listener = pynput.mouse.Listener(on_move=on_mouse_move)
	listener.start()

	# === Schedule tasks ===
	# Clear the mouse points array every second
	schedule.every().second.do(clear_points)

	# headturn should run every 10-15 minutes.
	min_s = 10 * 60
	max_s = (15 * 60) - (afk_timeout_grace + active_execution_grace)
	schedule.every(min_s).to(max_s).seconds.do(headturn)

	# === Run forever-ish ===
	while True:
		try:
			schedule.run_pending()
			time.sleep(1)
		except (KeyboardInterrupt, RuntimeError) as ex:
			print(f"\n\n[main] Shutting down due to {type(ex).__name__}: {ex}")

			# Cancel all jobs
			print("[main] Clearing the schedule...")
			schedule.clear()
			print("[main] Schedule cleared.")

			# Shutdown the mouse listener
			print("[main] Shutting down the mouse listener (you may need to move your mouse)...")
			pynput.mouse.Listener.stop(listener)
			print("[main] Mouse listener shut down.")

			# Exit
			return


if __name__ == "__main__":
	main()
