#include "utils.h"
#include <string.h>
int is_image_or_video(const char* filename) {
    const char *ext = strrchr(filename, '.');
    if (!ext) {
        return 0; // No extension
    }
    if (strcmp(ext, ".jpg") == 0 || strcmp(ext, ".png") == 0 || 
        strcmp(ext, ".mp4") == 0 || strcmp(ext, ".avi") == 0 || strcmp(ext, ".mp3") == 0) {
        return 1;
    }
    return 0;
}