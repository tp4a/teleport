//
//  AppDelegate.m
//  TPAssist
//

// Object-C与标准C/C++混合编程
// http://www.cppblog.com/zhangyuntaoshe/articles/123138.html
/*

 //stringWithUTF8String:
 //Returns a string created by copying the data from a given C array of UTF8-encoded bytes.
 cout<<"从string转成NSString:";
 NSLog( [NSString stringWithUTF8String:str.c_str()] );
 
 //cocoa Foundational NSString使用:
 NSString *istr=[NSString stringWithString:@"english and 中文"];
 str=[istr cStringUsingEncoding:	NSUTF8StringEncoding];
 cout<<"从NSString转成string: "<<str<<endl;
 
*/


#import "AppDelegate.h"
#import "AboutWindowController.h"

#include "AppDelegate-C-Interface.h"
#include "csrc/ts_http_rpc.h"

@implementation AppDelegate

int AppDelegate_start_ssh_client (void *_self, const char* cmd_line, const char* term_type, const char* term_theme, const char* term_title) {
	NSString* cmdLine = [NSString stringWithUTF8String:cmd_line];
	NSString* termType = [NSString stringWithUTF8String:term_type];
	NSString* termTheme = [NSString stringWithUTF8String:term_theme];
	NSString* termTitle = [NSString stringWithUTF8String:term_title];

	return [(__bridge id)_self start_ssh_client:cmdLine termType:termType termTheme:termTheme termTitle:termTitle];
}

- (void) awakeFromNib {
	
	// The path for the configuration file (by default: ~/.tp_assist.ini)
	NSString *cfgFile = [NSHomeDirectory() stringByAppendingPathComponent:@".tp-assist.json"];

	// if the config file does not exist, create a default one
	if ( ![[NSFileManager defaultManager] fileExistsAtPath:cfgFile] ) {
		NSString *cfgFileInResource = [[NSBundle mainBundle] pathForResource:@"tp-assist.default" ofType:@"json"];
		[[NSFileManager defaultManager] copyItemAtPath:cfgFileInResource toPath:cfgFile error:nil];
	}
	
    // Define Icons
    //only regular icon is needed for 10.10 and higher. OS X changes the icon for us.
    regularIcon = [NSImage imageNamed:@"StatusIcon"];
    altIcon = [NSImage imageNamed:@"StatusIconAlt"];
	
	// TODO: 现在statusIcon有两个问题：
	//   1. 不会响应系统设置“暗色菜单栏和Dock”的事件
	//   2. 即使是设置为暗色系，启动本程序也会使用黑色图标，导致在菜单栏中看不到图标。
	// 因此，应该响应系统的设置菜单栏颜色的事件，同时启动前先获取菜单栏的色系。
	
    // Create the status bar item
    statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSSquareStatusItemLength];
    [statusItem setMenu:menu];
    [statusItem setImage: regularIcon];
	[statusItem setHighlightMode:YES];
	[statusItem setAlternateImage: altIcon];

    // Needed to trigger the menuWillOpen event
    [menu setDelegate:self];


	//http_rpc_start((__bridge void*)self);
	
	NSString *resPath = [[NSBundle mainBundle] resourcePath];
	std::string cpp_res_path = [resPath cStringUsingEncoding:NSUTF8StringEncoding];
	std::string cpp_cfg_file = [cfgFile cStringUsingEncoding:NSUTF8StringEncoding];
	
	int ret = cpp_main((__bridge void*)self, cpp_cfg_file.c_str(), cpp_res_path.c_str());
	if(ret != 0) {
		// TODO: show error message and exit.
		NSString *msg = Nil;
		if(ret == -1)
			msg = @"初始化运行环境失败！";
		else if(ret == -2)
			msg = @"加载配置文件失败！";
		else if(ret == -3)
			msg = @"启动本地通讯端口失败！请检查本地50022端口是否被占用！";
		
		NSAlert *alert = [NSAlert alertWithMessageText:@"无法启动Teleport助手"
										 defaultButton:@"确定"
									   alternateButton:Nil
										   otherButton:Nil
							 informativeTextWithFormat:msg];
		[alert runModal];

		http_rpc_stop();
		
		[[NSStatusBar systemStatusBar] removeStatusItem:statusItem];
		[NSApp terminate:NSApp];	}
}

- (int) start_ssh_client:(NSString*)cmd_line termType:(NSString*)term_type termTheme:(NSString*)term_theme termTitle:(NSString*)term_title {
	NSString *term = [[NSBundle mainBundle] pathForResource:term_type ofType:@"scpt"];
	
	if(!term)
		return 1;
	
	NSString *handlerName = @"scriptRun";
	NSArray *passParameters = @[cmd_line, term_theme, term_title];
	[self runScript:term handler:handlerName parameters:passParameters];
	
	return 0;
}

- (void) runScript:(NSString *)scriptPath handler:(NSString*)handlerName parameters:(NSArray*)parametersInArray {
    NSAppleScript           * appleScript;
    NSAppleEventDescriptor  * thisApplication, *containerEvent;
    NSURL                   * pathURL = [NSURL fileURLWithPath:scriptPath];
    
    NSDictionary * appleScriptCreationError = nil;
    appleScript = [[NSAppleScript alloc] initWithContentsOfURL:pathURL error:&appleScriptCreationError];
    
    if (handlerName && [handlerName length])
    {
        /* If we have a handlerName (and potentially parameters), we build
         * an NSAppleEvent to execute the script. */
        
        //Get a descriptor
        int pid = [[NSProcessInfo processInfo] processIdentifier];
        thisApplication = [NSAppleEventDescriptor descriptorWithDescriptorType:typeKernelProcessID
                                                                         bytes:&pid
                                                                        length:sizeof(pid)];
        
        //Create the container event
        
        //We need these constants from the Carbon OpenScripting framework, but we don't actually need Carbon.framework...
#define kASAppleScriptSuite 'ascr'
#define kASSubroutineEvent  'psbr'
#define keyASSubroutineName 'snam'
        containerEvent = [NSAppleEventDescriptor appleEventWithEventClass:kASAppleScriptSuite
                                                                  eventID:kASSubroutineEvent
                                                         targetDescriptor:thisApplication
                                                                 returnID:kAutoGenerateReturnID
                                                            transactionID:kAnyTransactionID];
        //Set the target handler
        [containerEvent setParamDescriptor:[NSAppleEventDescriptor descriptorWithString:handlerName]
                                forKeyword:keyASSubroutineName];
        
        //Pass parameters - parameters is expecting an NSArray with only NSString objects
        if ([parametersInArray count])
        {
            
            NSAppleEventDescriptor  *arguments = [[NSAppleEventDescriptor alloc] initListDescriptor];
            NSString                *object;
            
            for (object in parametersInArray) {
                [arguments insertDescriptor:[NSAppleEventDescriptor descriptorWithString:object]
                                    atIndex:([arguments numberOfItems] +1)];
            }
            
            [containerEvent setParamDescriptor:arguments forKeyword:keyDirectObject];
        }
        //Execute the event
        [appleScript executeAppleEvent:containerEvent error:nil];
    }
}

- (IBAction)visitWebsite:(id)sender {
	
	NSURL *url = [NSURL URLWithString:@"https://www.tp4a.com/"];
	[[NSWorkspace sharedWorkspace] openURL:url];
}

- (IBAction)configure:(id)sender {
	NSURL *configURL = [NSURL URLWithString:@"http://127.0.0.1:50022/config"];
	[[NSWorkspace sharedWorkspace] openURL:configURL];
}

- (IBAction)showAbout:(id)sender {
    
    //Call the windows controller
    AboutWindowController *aboutWindow = [[AboutWindowController alloc] initWithWindowNibName:@"AboutWindowController"];
    
    //Set the window to stay on top
    [aboutWindow.window makeKeyAndOrderFront:nil];
    [aboutWindow.window setLevel:NSFloatingWindowLevel];
    
    //Show the window
    [aboutWindow showWindow:self];
}

- (IBAction)quit:(id)sender {
	http_rpc_stop();
	
	[[NSStatusBar systemStatusBar] removeStatusItem:statusItem];
    [NSApp terminate:NSApp];
}

@end
