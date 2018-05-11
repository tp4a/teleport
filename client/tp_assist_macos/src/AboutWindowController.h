//
//  AboutWindowController.h
//  TPAssist
//
//  Created by ApexLiu at 2017-09-13.
//

#import <Cocoa/Cocoa.h>

@interface AboutWindowController : NSWindowController

@property (strong) NSWindowController *aboutWindow;

@property (strong) IBOutlet NSTextField *appName;
@property (strong) IBOutlet NSTextField *appVersion;
@property (strong) IBOutlet NSTextField *appCopyright;

- (IBAction)btnHomepage:(id)sender;

@end
