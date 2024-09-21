#include "fileops.h"
#include "utils.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>

char* make_soft_links(char** paths, int num_paths) {
    char* temp_dir = strdup("/tmp/found_file_linksXXXXXX");
    mkdtemp(temp_dir);

    for (int i = 0; i < num_paths; i++) {
        char link_path[512];
        snprintf(link_path, sizeof(link_path), "%s/%s", temp_dir, strrchr(paths[i], '/') + 1);
        symlink(paths[i], link_path);
    }
    
    return temp_dir;
}

char* get_file_data(const char* path, int* is_image_or_video_flag) {
    FILE *file = fopen(path, "rb");
    if (!file) {
        return NULL;
    }

    *is_image_or_video_flag = is_image_or_video(path);
    if (*is_image_or_video_flag) {
        fclose(file);
        return strdup(strrchr(path, '/') + 1);
    }

    fseek(file, 0, SEEK_END);
    long fsize = ftell(file);
    fseek(file, 0, SEEK_SET);

    char *data = malloc(fsize + 1);
    fread(data, 1, fsize, file);
    fclose(file);

    data[fsize] = 0;
    return data;
}

void collect_file_data_recursive(const char* dir_path, int* num_files, char*** file_data_array, int depth) {
    // If depth is greater than 3, stop the recursion
    if (depth > 3) {
        return;
    }

    DIR *d = opendir(dir_path);
    if (!d) {
        return;
    }

    struct dirent *dir;
    while ((dir = readdir(d)) != NULL) {
        if (strcmp(dir->d_name, ".") == 0 || strcmp(dir->d_name, "..") == 0) {
            continue;
        }

        char full_path[512];
        snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, dir->d_name);

        struct stat st;
        if (stat(full_path, &st) == 0) {
            if (S_ISREG(st.st_mode)) {
                FILE *file = fopen(full_path, "rb");
                if (file) {
                    fseek(file, 0, SEEK_END);
                    long fsize = ftell(file);
                    fseek(file, 0, SEEK_SET);

                    char *data = malloc(fsize + 1);
                    fread(data, 1, fsize, file);
                    fclose(file);

                    data[fsize] = 0;

                    (*num_files)++;
                    *file_data_array = realloc(*file_data_array, sizeof(char*) * (*num_files));
                    (*file_data_array)[*num_files - 1] = data;
                }
            } else if (S_ISDIR(st.st_mode)) {
                collect_file_data_recursive(full_path, num_files, file_data_array, depth + 1);
            }
        }
    }
    closedir(d);
}

char** get_all_file_data(const char* dir_path, int* num_files) {
    *num_files = 0;
    char** file_data_array = malloc(0);
    collect_file_data_recursive(dir_path, num_files, &file_data_array, 1); // Start at depth 1
    return file_data_array;
}