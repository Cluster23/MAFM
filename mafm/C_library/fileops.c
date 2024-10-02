#include "fileops.h"
#include "utils.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include <io.h>
#include <Windows.h>

// make_soft_links: 여러 파일 경로에 대해 임시 디렉토리에 소프트 링크를 만든다.
// 입력: paths (파일 경로 배열), num_paths (경로 개수), temp_dir (임시 디렉토리 경로)
// 출력: 임시 디렉토리 경로 (char*)
char* make_soft_links(char** paths, int num_paths, char *temp_dir) {
    for (int i = 0; i < num_paths; i++) {
        char link_path[512];
        snprintf(link_path, sizeof(link_path), "%s/%s", temp_dir, strrchr(paths[i], '/') + 1);
        symlink(paths[i], link_path);
    }
    
    return temp_dir;
}

// get_filename: 파일 경로에서 파일 이름만 추출
// 입력: path (파일 경로)
// 출력: 파일 이름 (char*)
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


// get_file_data: 주어진 파일 경로에 대한 정보를 읽고 필요한 데이터를 반환
// 입력: path (파일 경로)
// 출력: 파일 정보 배열 (파일 경로, 파일 이름, 파일 내용 조각)
/* 파일 정보 배열의 구조:
 * data[0]: 파일의 전체 경로 (char*)
 * data[1]: 파일의 이름 (char*)
 * data[2], data[3], ...: 파일 내용을 일정 크기(chunkSize)로 나눈 조각들 (char*)
 * 마지막 data[idx + 1]: NULL 포인터 (배열의 끝을 알리기 위해)
*/
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


// collect_file_data_recursive: 지정된 디렉터리를 재귀적으로 탐색하며 파일 데이터를 수집
// 입력: dir_path (탐색할 디렉터리 경로), num_files (수집된 파일 개수 포인터), file_data_array (파일 데이터 배열 포인터), depth (재귀 깊이)
// 출력: 없음 (num_files와 file_data_array가 수정됨)
/* file_data_array는 파일 데이터를 가진 3차원 배열이다.
 * file_data_array[0]는 첫 번째 파일의 데이터를 가리키고, file_data_array[1]는 두 번째 파일의 데이터를 가리킨다.
 * file_data_array[i][j]는 i번째 파일 중 j번째 data(get_file_data의 리턴 배열)를 의미한다.
 * 즉, file_data_array[0][0]는 첫 번째 파일의 전체 경로를 의미한다.
 * file_data_array[i][j][k]는 단순 문자이므로 큰 의미가 없다.
*/
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


