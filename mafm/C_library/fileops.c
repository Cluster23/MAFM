#include "fileops.h"
#include "utils.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>

char* make_soft_links(char** paths, int num_paths, char *temp_dir) {
    for (int i = 0; i < num_paths; i++) {
        char link_path[512];
        snprintf(link_path, sizeof(link_path), "%s/%s", temp_dir, strrchr(paths[i], '/') + 1);
        symlink(paths[i], link_path);
    }
    
    return temp_dir;
}

char *get_filename(const char *path) {
    // Find the last occurrence of '/' in the path
    const char *lastSlash = strrchr(path, '/');
    
    // If there is no '/' in the path, use the whole path as the filename
    if (lastSlash == NULL) {
        return strdup(path);  // No '/' found, return the entire path as the filename
    }
    
    // Otherwise, return everything after the last '/'
    return strdup(lastSlash + 1);
}


char** get_file_data(const char* path) {
    FILE *file = fopen(path, "rb");
    if (!file) {
        return NULL;
    }

    char *fname = get_filename(path);
    int is_image_or_video_flag = is_image_or_video(path);
    
    if (is_image_or_video_flag) {
        char **data = malloc(sizeof(char *) * 3);
        data[0] = strdup(path);
        data[1] = fname;
        data[2] = NULL;
        fclose(file);
        return data;
    }

    int maxChunks = 4;
    char **data = (char **)malloc(sizeof(char *) * (maxChunks));

    data[0] = strdup(path); 
    data[1] = fname;
    
    int idx = 2;
    int chunkSize = 500;
    int bytesRead;

    while (1) {
        if (idx >= maxChunks) {
            maxChunks *= 2;
            data = (char **)realloc(data, maxChunks * sizeof(char *));
            if (data == NULL) {
                perror("Failed to reallocate memory for data array");
                fclose(file);
                return NULL;
            }
        }

        data[idx] = (char *)malloc(chunkSize * sizeof(char));
        if (data[idx] == NULL) {
            perror("Failed to allocate memory for chunk");
            fclose(file);
            return NULL;
        }

        bytesRead = fread(data[idx], 1, chunkSize, file);
        if (bytesRead > 0) {
            idx++;
        }
        if (bytesRead < chunkSize) {
            if (feof(file)) {
                break;
            } else if (ferror(file)) {
                perror("Error reading file");
                fclose(file);
                return NULL;
            }
        }
    }
    data[idx + 1] = NULL;
    fclose(file);
    return data;
}

void collect_file_data_recursive(const char* dir_path, int* num_files, char**** file_data_array, int depth) {
    if (depth > 3) {
        return;
    }

    DIR *d = opendir(dir_path);
    if (!d) {
        return;
    }

    struct dirent *dir;
    int alloc_size = 4;
    while ((dir = readdir(d)) != NULL) {
        if (strcmp(dir->d_name, ".") == 0 || strcmp(dir->d_name, "..") == 0) {
            continue;
        }
        char full_path[512];
        snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, dir->d_name);

        struct stat st;
        if (stat(full_path, &st) == 0) {
            if (S_ISREG(st.st_mode)) {
                char **data = get_file_data(full_path);
                if (data) {
                    (*num_files)++;
                    if (*num_files > alloc_size){
                        alloc_size *= 2;
                        *file_data_array = realloc(*file_data_array, sizeof(char***) * alloc_size);
                    }
                    (*file_data_array)[*num_files - 1] = data;
                }
            } else if (S_ISDIR(st.st_mode)) {
                collect_file_data_recursive(full_path, num_files, file_data_array, depth + 1);
            }
        }
    }
    closedir(d);
}

char*** get_all_file_data(const char* dir_path, int* num_files) {
    *num_files = 0;
    char*** file_data_array = malloc(sizeof(char **) * 4);
    collect_file_data_recursive(dir_path, num_files, &file_data_array, 1);
    return file_data_array;
}