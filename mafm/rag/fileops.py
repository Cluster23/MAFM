import ctypes

lib = ctypes.CDLL("./rag/C_library/libfileops.so")

lib.make_soft_links.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.c_int,
    ctypes.c_char_p,
]
lib.make_soft_links.restype = ctypes.c_char_p


def make_soft_links(paths, temp_dir):
    path_array = (ctypes.c_char_p * len(paths))(
        *[path.encode("utf-8") for path in paths]
    )
    result = lib.make_soft_links(path_array, len(paths), temp_dir.name.encode("utf-8"))
    return result.decode("utf-8")


lib.get_file_data.argtypes = [ctypes.c_char_p]
lib.get_file_data.restype = ctypes.POINTER(ctypes.c_char_p)


def get_file_data(path):
    result = lib.get_file_data(path.encode("utf-8"))
    data_list = []
    idx = 0

    while result[idx] is not None:
        string = ctypes.string_at(result[idx]).decode("utf-8")
        data_list.append(string)
        idx += 1
    return data_list


lib.get_all_file_data.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
lib.get_all_file_data.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))

# ctypes를 통해 free_all_file_data 함수를 정의
lib.free_file_data_array.restype = None
lib.free_file_data_array.argtypes = [ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)), ctypes.c_int]

def get_all_file_data(directory):
    num_files = ctypes.c_int(0)
    result = lib.get_all_file_data(directory.encode("utf-8"), ctypes.byref(num_files))
    files = []
    try:
        for i in range(num_files.value):
            idx = 0
            data_list = []
            while result[i][idx] is not None:
                try:
                    string = ctypes.string_at(result[i][idx]).decode("utf-8")
                except:
                    string = ctypes.string_at(result[i][idx])
                data_list.append(string)
                idx += 1
            files.append(data_list)
        return files
    finally:
        # C에서 할당된 메모리 해제
        result_casted = ctypes.cast(result, ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)))
        lib.free_file_data_array(result_casted, num_files.value)


# get_file_data("/Users/Ruffles/Downloads/MAFM_test/text9.txt")
