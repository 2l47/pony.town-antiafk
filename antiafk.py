#!/usr/bin/env python3

import imagehash
import os
import PIL.Image
import PIL.ImageGrab
import pynput
import random
import schedule
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

# Load the image we use to check if the user is typing
chat_indicator = PIL.Image.open("chat_indicator.png")
# Calculate its hash
chat_indicator_hash = imagehash.average_hash(chat_indicator)


# Sends a desktop notification
def notify(text):
	print(text)
	os.system(f"notify-send --expire-time={notification_duration} antiafk.py \"{text}\"")


# Function to check whether the user has the textbox open
def user_typing():
	# 19x16 pixels
	image = PIL.ImageGrab.grab(bbox=(473, 1048, 492, 1064))
	#image.save("capture.png")
	capture_hash = imagehash.average_hash(image)
	difference = chat_indicator_hash - capture_hash
	#print(f"capture_hash: {capture_hash}")
	#print(f"chat_indicator_hash: {chat_indicator_hash}")
	#print(f"difference: {difference}")
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
		print(f"Script moved mouse to {x}, {y} (ignoring mouse movement)")
	else:
		mouse_points.append((x, y))
		# If the user has 100ms of activity, update the last active epoch
		if len(mouse_points) >= 100:
			now = time.time()
			# If the user is currently considered active, don't log the fact that we're updating the epoch
			if not user_considered_active():
				print(f"[{now}] User activity epoch updated")
			user_last_active = now


# Sends an initial warning and subsequent warnings before returning
def warning_timer(caller, execution_grace):
	notify(f"{caller} called, waiting {execution_grace} seconds before executing...")
	for i in range(execution_grace):
		remaining = execution_grace - i
		if remaining <= 5:
			notify(f"Returning to {caller} in {remaining} seconds...")
		time.sleep(1)


# Turns the head back and forth to simulate player activity
def headturn():
	if user_typing():
		return notify("Not running headturn() because user is typing...")
	execution_grace = active_execution_grace if user_considered_active() else inactive_execution_grace
	warning_timer("headturn()", execution_grace)
	keypress_duration = random.randint(20, 100)
	print(f"headturn() using keypress duration of {keypress_duration} ms")
	interkey_delay = random.randint(100, 200)
	print(f"headturn() using inter-key delay of {interkey_delay} ms")
	os.system(f"xdotool key --clearmodifiers --delay {keypress_duration} --repeat 2 --repeat-delay {interkey_delay} h")
	print("headturn() done.\n")


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
		except KeyboardInterrupt:
			print("\n\nShutting down...")

			# Cancel all jobs
			print("Clearing the schedule...")
			schedule.clear()
			print("Schedule cleared.")

			# Shutdown the mouse listener
			print("Shutting down the mouse listener (you may need to move your mouse)...")
			pynput.mouse.Listener.stop(listener)
			print("Mouse listener shut down.")

			# Exit
			return


if __name__ == "__main__":
	main()
