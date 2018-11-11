//
//  AppDelegate.h
//  TPAssist
//

#import <Cocoa/Cocoa.h>

@interface AppDelegate : NSObject <NSApplicationDelegate, NSMenuDelegate>{
    IBOutlet NSMenu *menu;
    IBOutlet NSArrayController *arrayController;

    NSImage *regularIcon;
    NSImage *altIcon;
    
    NSStatusItem *statusItem;
}

- (int) start_ssh_client:(NSString*)cmd_line termType:(NSString*)term_type termTheme:(NSString*)term_theme termTitle:(NSString*)term_title;
- (int) select_app:(NSString*)ignore;

@end
