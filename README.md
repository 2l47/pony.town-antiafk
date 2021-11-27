# pony.town-antiafk

## About

This is an anti-AFK script for the game [Pony Town](https://pony.town/) and its derivatives.

As of now, it has only been tested on Pony Town.

### Behavior

* The script attempts to turn the player's head back and forth every 10 to 15 (or so) minutes
	* The following things are checked:
		* Whether the user has moved their mouse in the past two minutes
			* If so, an earlier notice is given
		* Whether the user appears to be typing (has the chat textbox open)
			* If so, the action is not performed and the user is notified
	* Desktop notifications are sent informing the user of script action

### Functionality

* Turning the head is done randomly every 10 to 15 (or so) minutes
	* Each keypress has a random duration from 20 to 100 ms
	* The delay between each keypress is a random value between 100 and 200 ms
* Mouse movement events are recorded and cleared over 1 second periods to track actual user activity
	* If the user has been active in the past 2 minutes, earlier notice is given for actions
* A small portion of the screen is captured to determine whether the user has the chat textbox open
	* If so, actions are cancelled

### External programs

The Linux utility `xdotool` is used to simulate keyboard input.

The following external Python 3 libraries are used:
* [schedule](https://pypi.org/project/schedule/): function scheduling
* [pynput](https://pypi.org/project/pynput/): listening for mouse movement
* [Pillow](https://pypi.org/project/Pillow/): screen image capture and image loading
* [imagehash](https://pypi.org/project/ImageHash/): comparing screen captures to determine if the chat textbox is open

## Support

The script has been written to support Linux systems using the XFCE desktop environment. You may be able to tweak it to suit your needs.

It is intended for use in a virtual machine where the active window is always the game.

## Caveats

A specific window is not currently targeted by xdotool. This is because of the expectation that the script is being run in a virtual machine, as well as the developer's laziness to not bother using xdotool's command chaining functionality to search for windows first.

The script was developed with virtual machines in mind because xdotool can't send keypresses to windows on other workspaces without switching to them. Although a solution to this problem could be developed, using a virtual machine just seemed simpler.

For such a solution, of note might be commands like:
```
ACTIVEWINDOW=`xdotool getactivewindow`
xdotool search --desktop 0 --name 'Pony Town.*' windowactivate
# do stuff
xdotool windowactivate $ACTIVEWINDOW
```
...which could be used to perform actions across workspaces and then return the user's focus. Interrupting the user's activities, however, generally sounds undesirable.

## Installation

```
sudo apt update
sudo apt install git python3-pip xdotool
git clone https://github.com/2l47/pony.town-antiafk
cd ./pony.town-antiafk/
pip3 install -r requirements.txt
```

## Usage

```
./antiafk.py
```
