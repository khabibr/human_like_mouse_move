# human_like_mouse_move

Usage:
./mouse_move.py [COORDINATES] [PARAMS] [KEYS]

COORDINATES: x1:y1 x2:y2 ... xM:yM
	Move cursor sequentially along the COORDINATES
	endless random movements if no COORDINATES
PARAMS: param1:val1 param2:val2 ... paramN:valN
	Set of params:
	count - count of random movement
	min_pause, max_pause - pause between movements (seconds)
	min_speed, max_speed - speed of movements (1..100)
	top_left, bottom_right - movements range (top_left:x:y or bottom_right:x:y)
KEYS:
	--debug_show_curve : Show mouse path curve (matplotlib figure)
	--autopilot : Use autopilot mouse move method (default)
	  (https://developer.ubuntu.com/api/autopilot/python/1.5.0/autopilot.input)
	--xdotool : Use xdotool mouse move method
Example:
	./mouse_move.py 100:100 500:100 300:250 100:100 max_speed:50
	./mouse_move.py count:10 count:10 max_pause:1 top_left:0:0 bottom_right:639:199