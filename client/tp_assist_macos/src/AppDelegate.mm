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
#include "csrc/ts_ws_client.h"

@implementation AppDelegate

int AppDelegate_start_ssh_client (void *_self, const char* cmd_line, const char* term_type, const char* term_theme, const char* term_title) {
	NSString* cmdLine = [NSString stringWithUTF8String:cmd_line];
	NSString* termType = [NSString stringWithUTF8String:term_type];
	NSString* termTheme = [NSString stringWithUTF8String:term_theme];
	NSString* termTitle = [NSString stringWithUTF8String:term_title];

	return [(__bridge id)_self start_ssh_client:cmdLine termType:termType termTheme:termTheme termTitle:termTitle];
}

int AppDelegate_select_app (void *_self) {
    NSString* strIgnore = @"";
    return [(__bridge id)_self select_app:strIgnore];
}

- (void) awakeFromNib {
    NSFileManager *fileManager= [NSFileManager defaultManager];

    // create necessary directory to store config file and log file.
    // The path for the log file (by default: ~/tp-assist/log)
    NSString *logPath = [NSHomeDirectory() stringByAppendingPathComponent:@"tp-assist/log"];
    
    NSError *error = nil;
    if(![fileManager createDirectoryAtPath:logPath withIntermediateDirectories:YES attributes:nil error:&error]) {
        // An error has occurred, do something to handle it
        NSLog(@"Failed to create directory \"%@\". Error: %@", logPath, error);
        
//        NSAlert *alert = [[NSAlert alloc] init];
//        alert.icon = [NSImage imageNamed:@"tpassist"];
//        [alert addButtonWithTitle:@"确定"];
//        [alert setMessageText:@"无法启动Teleport助手"];
//        [alert setInformativeText:@"无法创建目录 ~/tp-assist 来存储配置文件及日志文件。"];
//        [alert runModal];
        
        [self my_alert:@"无法启动Teleport助手" msg:@"无法创建目录 ~/tp-assist 来存储配置文件及日志文件。"];
        
        [[NSStatusBar systemStatusBar] removeStatusItem:statusItem];
        [NSApp terminate:NSApp];
    }

	// The path for the configuration file (by default: ~/tp-assist/tp-assist.json)
	NSString *cfgFile = [NSHomeDirectory() stringByAppendingPathComponent:@"tp-assist/tp-assist.json"];

	// if the config file does not exist, create a default one
	if ( ![fileManager fileExistsAtPath:cfgFile] ) {
		NSString *cfgFileInResource = [[NSBundle mainBundle] pathForResource:@"tp-assist.macos" ofType:@"json"];
		[fileManager copyItemAtPath:cfgFileInResource toPath:cfgFile error:nil];
	}
	
    // Define Icons
    //only regular icon is needed for 10.10 and higher. OS X changes the icon for us.
    regularIcon = [NSImage imageNamed:@"StatusIcon"];
    [regularIcon setTemplate:YES];
    
    altIcon = [NSImage imageNamed:@"StatusIconAlt"];
	
    // Create the status bar item
    statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSSquareStatusItemLength];
    [statusItem setMenu:menu];
    [statusItem setImage: regularIcon];
	[statusItem setHighlightMode:YES];
    [statusItem setAlternateImage: altIcon];

    // Needed to trigger the menuWillOpen event
    [menu setDelegate:self];
	
    NSString *bundlePath = [[NSBundle mainBundle] bundlePath];
    std::string bundle_path = [bundlePath cStringUsingEncoding:NSUTF8StringEncoding];

    NSString *resPath = [[NSBundle mainBundle] resourcePath];
	std::string cpp_res_path = [resPath cStringUsingEncoding:NSUTF8StringEncoding];
	std::string cpp_cfg_file = [cfgFile cStringUsingEncoding:NSUTF8StringEncoding];
    std::string cpp_log_path = [logPath cStringUsingEncoding:NSUTF8StringEncoding];
	
    int ret = cpp_main((__bridge void*)self, bundle_path.c_str(), cpp_cfg_file.c_str(), cpp_res_path.c_str(), cpp_log_path.c_str());
	if(ret != 0) {
        // http_rpc_stop();
        g_ws_client.stop_all_client();

        NSString *msg = Nil;
		if(ret == -1)
			msg = @"初始化运行环境失败！";
		else if(ret == -2)
			msg = @"加载配置文件失败！\n\n请删除 ~/.tp-assist.json 后重试！";
		else
			msg = @"发生未知错误！";
		
//        NSAlert *alert = [[NSAlert alloc] init];
//        alert.icon = [NSImage imageNamed:@"tpassist"];
//        [alert addButtonWithTitle:@"确定"];
//        [alert setMessageText:@"无法启动Teleport助手"];
//        [alert setInformativeText:msg];
//        [alert runModal];
        [self my_alert:@"无法启动Teleport助手" msg:msg];
        
		[[NSStatusBar systemStatusBar] removeStatusItem:statusItem];
		[NSApp terminate:NSApp];
    }
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
        // If we have a handlerName (and potentially parameters), we build
        // an NSAppleEvent to execute the script.
        
        //Get a descriptor
        int pid = [[NSProcessInfo processInfo] processIdentifier];
        thisApplication = [NSAppleEventDescriptor descriptorWithDescriptorType:typeKernelProcessID
                                                                         bytes:&pid
                                                                        length:sizeof(pid)];
        
        //Create the container event
        
        // We need these constants from the Carbon OpenScripting framework,
        // but we don't actually need Carbon.framework...
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

- (int) select_app:(NSString*)strIgnore {
    // NOT WORK NOW
    // this function called by ts_http_rpc.c but it run in worker thread.
    // once we call select_app from worker thread, the NSOpenPanel alloc crash.
    // so we have had to show UI like "post a event and call callback" stuff.

    NSOpenPanel *mySelectPanel = [[NSOpenPanel alloc] init];
    [mySelectPanel setCanChooseDirectories:YES];
    [mySelectPanel setCanChooseFiles:YES];
    [mySelectPanel setCanCreateDirectories:YES];
    [mySelectPanel setAllowsMultipleSelection:NO];
    [mySelectPanel setResolvesAliases:YES];

    if([mySelectPanel runModal] == NSModalResponseOK) {
        NSURL *ret = [mySelectPanel URL];
        NSLog(@"%@", ret.absoluteString);
    }

    return 0;
}

- (IBAction)visitWebsite:(id)sender {
	
	NSURL *url = [NSURL URLWithString:@"https://www.tp4a.com/"];
	[[NSWorkspace sharedWorkspace] openURL:url];
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
    g_ws_client.stop_all_client();
	
	[[NSStatusBar systemStatusBar] removeStatusItem:statusItem];
    [NSApp terminate:NSApp];
}

//- (void)applicationDidFinishLaunching:(NSNotification *)notification
//{
//    // once the program start, register URL scheme handler.
//    [[NSAppleEventManager sharedAppleEventManager] setEventHandler:self andSelector:@selector(handleURLEvent:withReplyEvent:) forEventClass:kInternetEventClass andEventID:kAEGetURL];
//}

- (void)applicationWillFinishLaunching:(NSNotification *)notification
{
    // once the program start, register URL scheme handler.
    [[NSAppleEventManager sharedAppleEventManager] setEventHandler:self andSelector:@selector(handleURLEvent:withReplyEvent:) forEventClass:kInternetEventClass andEventID:kAEGetURL];
}

- (void)handleURLEvent:(NSAppleEventDescriptor*)theEvent withReplyEvent:(NSAppleEventDescriptor*)replyEvent {
    // Process URL Request
    NSString* url = [[theEvent paramDescriptorForKeyword:keyDirectObject] stringValue];
//    unsigned long long pid = cpp_getpid();
//
//    NSAlert *alert = [[NSAlert alloc] init];
//    alert.icon = [NSImage imageNamed:@"tpassist"];
//    [alert addButtonWithTitle:@"确定"];
//    [alert setMessageText:@"URL Request"];
//    [alert setInformativeText:[NSString stringWithFormat:@"%@, pid=%llu", url, pid]];
//    [alert runModal];
//
//    [self my_alert:@"URL Request" msg:url];
    std::string _url = [url cStringUsingEncoding:NSUTF8StringEncoding];
    g_ws_client.url_scheme_handler(_url);
}

- (void)my_alert:(NSString*) title msg:(NSString*)message {
        NSAlert *alert = [[NSAlert alloc] init];
        alert.icon = [NSImage imageNamed:@"tpassist"];
        [alert addButtonWithTitle:@"确定"];
        [alert setMessageText:title];
        [alert setInformativeText:[NSString stringWithFormat:@"%@", message]];
        [alert runModal];
}

@end
