on scriptRun(argsCmd, argsProfile, argsTitle)
	set theCmd to (argsCmd)
	set theProfile to (argsProfile)
	set theTitle to (argsTitle)
	CommandRun(theCmd, theProfile, theTitle)
end scriptRun

on CommandRun(theCmd, theProfile, theTitle)
	tell application "Terminal"
		if it is not running then
			--if this is the first time Terminal is running you have specify window 1
			--if you dont do this you will get two windows and the title wont be set
			activate
			set newTerm to do script theCmd in window 1
			set newTerm's current settings to settings set theProfile
			set custom title of front window to theTitle
		else
			--Terminal is running get the window count
			set windowCount to (count every window)
			if windowCount = 0 then
				--Terminal is running but no windows are open
				--run our script in a new window
				reopen
				activate
				do script theCmd in window 1
			else
				--Terminal is running and we have a window run in a new tab
				reopen
				activate
				tell application "System Events"
					tell process "Terminal"
						delay 0.2
						keystroke "t" using {command down}
					end tell
				end tell
				activate
				do script theCmd in front window
			end if
			set current settings of selected tab of front window to settings set theProfile
			set title displays custom title of front window to true
			set custom title of selected tab of front window to theTitle
		end if
	end tell
end CommandRun
