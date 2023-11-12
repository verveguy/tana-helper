# calendar_auth is important to ensure authentication UI presented 
# to the user on the first time they run this service invocation

tell application id "com.apple.iCal"
	reload calendars
	calendars
end tell