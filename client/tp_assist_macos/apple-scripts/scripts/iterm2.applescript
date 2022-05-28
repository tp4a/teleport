on scriptRun(argsCmd, argsProfile, argsTitle, argsInteractiveMode)
	set theCmd to (argsCmd)
	set theProfile to (argsProfile)
	set theTitle to (argsTitle)
	CommandRun(theCmd, theProfile, theTitle, argsInteractiveMode)
end scriptRun

on CommandRun(theCmd, theProfile, theTitle, theInteractiveMode)
	try
		tell application "iTerm"
			if it is not running then
				tell application "iTerm"
					activate
					delay 0.5
					try
						close first window
					end try
				end tell
				
				tell application "iTerm"
					try
						create window with profile theProfile
					on error msg
						create window with profile "Default"
					end try
					tell the current window
						tell the current session
							delay 0.5
							set name to theTitle
							set profile to theProfile
							write text theCmd
                            if theInteractiveMode = "no" then
                                delay 0.5
                                write text ""
                            end if
						end tell
					end tell
				end tell
			else
				--assume that iTerm is open and open a new tab
				try
					tell application "iTerm"
						activate
						tell the current window
							try
								create tab with profile theProfile
							on error msg
								create tab with profile "Default"
							end try
							tell the current tab
								tell the current session
									delay 0.5
									set name to theTitle
									write text theCmd
                                    if theInteractiveMode = "no" then
                                        delay 0.5
                                        write text ""
                                    end if
								end tell
							end tell
						end tell
					end tell
				on error msg
					-- if all iTerm windows are closed the app stays open. In this scenario iTerm has
					-- no "current window" and will give an error when trying to create the new tab.  
					tell application "iTerm"
						try
							create window with profile theProfile
						on error msg
							create window with profile "Default"
						end try
						tell the current window
							tell the current session
								delay 0.5
								set name to theTitle
								write text theCmd
                                if theInteractiveMode = "no" then
                                    delay 0.5
                                    write text ""
                                end if
							end tell
						end tell
					end tell
				end try
			end if
		end tell
	on error msg
		display dialog "ERROR: " & msg
	end try
	
end CommandRun
