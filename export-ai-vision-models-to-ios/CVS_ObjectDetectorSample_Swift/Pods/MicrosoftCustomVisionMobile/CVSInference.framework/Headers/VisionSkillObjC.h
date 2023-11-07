#import <UIKit/UIKit.h>

typedef NS_ENUM(NSInteger, VSVariableType)
{
    TypeBase         = 0, // base variable
    TypeString       = 1, // string variable
    TypeInt          = 2, // int variable
    TypeFloat        = 3, // float variable
    TypeRect         = 4, // rectangle variable
    TypeImage        = 6, // image variable
    TypeFloatVector  = 7, // float vector variable
    TypeStringVector = 8, // string vector variable
    TypeBool         = 9, // boolean variable
};

@interface VSVariable : NSObject
// bind variable from other skill instance to this variable
- (void) bind:(VSVariable *) variable;
- (void) unbind;
- (bool) isBound;

@property (nonatomic, readonly) const NSString *name;
@property (nonatomic, readonly) VSVariableType type;
@end

@interface VSString : VSVariable
@property (nonatomic) NSString *string;
@end

@interface VSBool : VSVariable
@property (nonatomic) Boolean value;
@end

@interface VSInt : VSVariable
@property (nonatomic) int value;
@end

@interface VSFloat : VSVariable
@property (nonatomic) float value;
@end

@interface VSRect : VSVariable
@property (nonatomic) CGRect rect;
@end

typedef enum {
    LOCAL,
    REMOTE,
} VSRunMode;


@interface VSImage : VSVariable
- (void) setImage:(UIImage *) image;
- (void) setCGImage:(CGImageRef) image;
- (void) setCGImage:(CGImageRef) image
    scale:(CGFloat) scale orientation:(UIImageOrientation) orientation;
- (void) setNV12:(NSData *) data width:(int) width height:(int) height;
- (void) setNV12:(NSData *) data width:(int) width height:(int) height
    scale:(CGFloat) scale orientation:(UIImageOrientation) orientation;
@property (nonatomic) UIImage *image;
@property (nonatomic) CGFloat scale;
@property (nonatomic) UIImageOrientation orientation;
- (UIImage *) getUIImage;
- (CGImageRef) getCGImage;
- (void) deallocate;
@end

@interface VSFloatVector : VSVariable
@property (nonatomic) NSArray *values;

// subset of std::vector manipulation methods
- (NSUInteger) countOfValue;
- (float) valueAtIndex:(NSUInteger) index;
@end

@interface VSStringVector : VSVariable
@property (nonatomic) NSArray<NSString *> *values;

// subset of std::vector manipulation methods
- (NSUInteger) countOfString;
- (const NSString *) stringAtIndex:(NSUInteger) index;
@end

@interface VSIntVector : VSVariable
@property (nonatomic) NSArray<NSNumber *> *values;

- (NSUInteger) countOfValue;
- (int) valueAtIndex:(NSUInteger) index;
@end

@interface VSRectVector : VSVariable
@property (nonatomic) NSArray<NSValue *> *values;

- (NSUInteger) countOfRect;
- (CGRect) rectAtIndex:(NSUInteger) index;
@end

@interface VisionSkillConfigObjC : NSObject
@end

@interface VisionSkillObjC : NSObject
@property (nonatomic) VSRunMode runMode;
- (void) run;
- (void) runAsync: (void (^)(void))completion;
@end

@interface VisionSkillsHelper : NSObject
+ (NSData *) convertToNV12:(CGImageRef) image;
@end
