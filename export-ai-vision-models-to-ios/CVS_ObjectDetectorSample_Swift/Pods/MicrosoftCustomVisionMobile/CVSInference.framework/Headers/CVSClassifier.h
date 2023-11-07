#import <UIKit/UIKit.h>

//! Project version number for Classifier.
FOUNDATION_EXPORT double CVSClassifierVersionNumber;

//! Project version string for Classifier.
FOUNDATION_EXPORT const unsigned char CVSClassifierVersionString[];

#import "VisionSkillObjC.h"
@class CVSClassifierConfig;

@interface CVSClassifier : VisionSkillObjC
- (instancetype) initWithConfig:(CVSClassifierConfig*) config error:(NSError**) error;
- (instancetype) initWithConfig:(CVSClassifierConfig*) config;
- (void) runWithError:(NSError **) error;
- (void) run;

// inputs
@property (nonatomic, readonly) VSImage* image;
@property (nonatomic, readonly) VSInt* maxReturns;
@property (nonatomic, readonly) VSFloat* threshold;

// outputs
@property (nonatomic, readonly) VSFloatVector* confidences;
@property (nonatomic, readonly) VSStringVector* identifiers;
@property (nonatomic, readonly) VSFloat* timeInMilliseconds;
@end

@interface CVSClassifierConfig : VisionSkillConfigObjC
- (instancetype) buildWithError:(NSError**) error;
- (instancetype) build;

@property (nonatomic, readonly) VSString* modelFile;
@end
