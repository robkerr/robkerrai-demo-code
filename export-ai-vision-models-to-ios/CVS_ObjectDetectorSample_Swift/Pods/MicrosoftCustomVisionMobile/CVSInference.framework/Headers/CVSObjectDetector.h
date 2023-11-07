#import <UIKit/UIKit.h>

//! Project version number for ObjectDetector.
FOUNDATION_EXPORT double CVSObjectDetectorVersionNumber;

//! Project version string for ObjectDetector.
FOUNDATION_EXPORT const unsigned char CVSObjectDetectorVersionString[];

#import "VisionSkillObjC.h"
@class CVSObjectDetectorConfig;

@interface CVSObjectDetector : VisionSkillObjC
- (instancetype) initWithConfig:(CVSObjectDetectorConfig*) config error:(NSError**) error;
- (instancetype) initWithConfig:(CVSObjectDetectorConfig*) config;
- (void) runWithError:(NSError **) error;
- (void) run;

// inputs
@property (nonatomic, readonly) VSImage* image;
@property (nonatomic, readonly) VSInt* maxReturns;
@property (nonatomic, readonly) VSFloat* threshold;

// outputs
@property (nonatomic, readonly) VSRectVector* boundingBoxes;
@property (nonatomic, readonly) VSFloatVector* confidences;
@property (nonatomic, readonly) VSIntVector* identifierIndexes;
@property (nonatomic, readonly) VSStringVector* identifiers;
@property (nonatomic, readonly) VSFloat* timeInMilliseconds;
@end

@interface CVSObjectDetectorConfig : VisionSkillConfigObjC
- (instancetype) buildWithError:(NSError**) error;
- (instancetype) build;

@property (nonatomic, readonly) VSString* modelFile;
@property (nonatomic, readonly) VSStringVector* supportedIdentifiers;
@end
