//
//  AboutWindowController.m
//  TPAssist
//
//  Created by ApexLiu at 2017-09-13.
//

#import "AboutWindowController.h"

@interface AboutWindowController ()

@end

@implementation AboutWindowController
@synthesize aboutWindow;
@synthesize appName;
@synthesize appVersion;
@synthesize appCopyright;

NSDictionary *plistDict;

- (id)initWithWindow:(NSWindow *)window
{
    aboutWindow = [super initWithWindow:window];
    if (self) {
        // Initialization code here.
    }
    return self;
}

- (void)windowDidLoad
{
    [super windowDidLoad];
    //Prevent the window from changing positions after multiple opens.
    [aboutWindow setShouldCascadeWindows:NO];
    
    //Load the plist so we can get current info for the about box.
    plistDict = [[NSBundle mainBundle] infoDictionary];
    
    //Get the application name.
//    id applicationName = [plistDict objectForKey:@"CFBundleName"];
    //Get the build version.
    id applicationVersion = [plistDict objectForKey:@"CFBundleVersion"];
    //Get the copyright.
//    id applicationCopyright = [plistDict objectForKey:@"NSHumanReadableCopyright"];
    
    //Build the string for the windows title.
    // NSString *aboutTitle = [NSString stringWithFormat:@"%@%@", NSLocalizedString(@"About ",nil), applicationName];
    NSString *strTitle = [NSString stringWithFormat:@"%@%@",
                          NSLocalizedString(@"about ",nil),
                          NSLocalizedString(@"app_name",nil)];
    [aboutWindow.window setTitle:strTitle];
    
    //Build the string for the application name. appName - tagline
    NSString *strProgName = [NSString stringWithFormat:@"%@", NSLocalizedString(@"app_full_name", nil)];
    [appName setStringValue:strProgName];
    
    //Build the string for the version. Version: $build
    NSString *strVersion = [NSString stringWithFormat:@"%@%@", NSLocalizedString(@"version", nil), applicationVersion];
    [appVersion setStringValue:strVersion];

    NSString *strCopyright = [NSString stringWithFormat:@"%@", NSLocalizedString(@"copyright", nil)];
    [appCopyright setStringValue:strCopyright];
}

- (IBAction)btnHomepage:(id)sender {
    
    //Get the homepage from the plist
    id applicationHomepage = [plistDict objectForKey:@"Product Homepage"];
    //Build the homepage's URL.
    NSURL *homeURL = [NSURL URLWithString:applicationHomepage];
    
    //Go to the website.
    [[NSWorkspace sharedWorkspace] openURL:homeURL];
    
    //Close the about box.
    [aboutWindow close];
}
@end
