on scriptRun(argsCmd, argsProfile, argsTitle, argsInteractiveMode)
	set theCmd to (argsCmd)
	set theProfile to (argsProfile)
	set theTitle to (argsTitle)
	CommandRun(theCmd, theProfile, theTitle, argsInteractiveMode)
end scriptRun

on CommandRun(theCmd, theProfile, theTitle, theInteractiveMode)
	try
		tell application "Terminal"
			if it is not running then
				--if this is the first time Terminal is running you have specify window 1
				--if you dont do this you will get two windows and the title wont be set
                activate
				delay 3.0
				set newTerm to do script theCmd in window 1

                set newTerm's current settings to settings set theProfile
				set custom title of front window to theTitle
				
                if theInteractiveMode = "no"
                    delay 1.0
                    reopen
                    activate
                    tell application "System Events" to key code 36
                end if
			else
				--Terminal is running get the window count
				set windowCount to (count every window)
				if windowCount = 0 then
					--Terminal is running but no windows are open
					--run our script in a new window
					reopen
					activate
					
					do script theCmd in window 1

					set current settings of selected tab of front window to settings set theProfile
					set title displays custom title of front window to true
					set custom title of selected tab of front window to theTitle
					
                    if theInteractiveMode = "no"
                        delay 1.0
                        reopen
                        activate
                        tell application "System Events" to key code 36
					end if
				else
					--Terminal is running and we have a window run in a new tab
                    delay 1.0
					reopen
					activate
					
					tell application "System Events"
                        -- Command+T = new tab.
                        key code 17 using {command down}
					end tell
					
					reopen
					activate
					do script theCmd in front window
					
					set current settings of selected tab of front window to settings set theProfile
					set title displays custom title of front window to true
					set custom title of selected tab of front window to theTitle
					
                    if theInteractiveMode = "no"
                        delay 1.0
                        reopen
                        activate
                        tell application "System Events" to key code 36
					end if
				end if

			end if
			
		end tell
		
	on error msg
		display dialog "ERROR: " & msg
	end try
	
	
end CommandRun
