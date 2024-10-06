#ifndef FILEOPS_H
#define FILEOPS_H

#include <stdio.h>

char* make_soft_links(char** paths, int num_paths, char *temp_dir);
char** get_file_data(const char* path);
char*** get_all_file_data(const char* dir_path, int* num_files);
int split_file(const char* file_path, const char* output_dir, size_t chunk_size);
int is_image_or_video(const char* filename);

#endif