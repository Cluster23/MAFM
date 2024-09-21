import ctypes

lib = ctypes.CDLL("./C_library/libfileops.so")

lib.make_soft_links.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
lib.make_soft_links.restype = ctypes.c_char_p


def make_soft_links(paths):
    path_array = (ctypes.c_char_p * len(paths))(
        *[path.encode("utf-8") for path in paths]
    )
    result = lib.make_soft_links(path_array, len(paths))
    return result.decode("utf-8")


lib.get_file_data.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
lib.get_file_data.restype = ctypes.c_char_p


def get_file_data(path):
    is_image_or_video = ctypes.c_int(0)
    result = lib.get_file_data(path.encode("utf-8"), ctypes.byref(is_image_or_video))
    return result.decode("utf-8"), bool(is_image_or_video.value)


lib.get_all_file_data.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
lib.get_all_file_data.restype = ctypes.POINTER(ctypes.c_char_p)


def get_all_file_data(directory):
    num_files = ctypes.c_int(0)
    result = lib.get_all_file_data(directory.encode("utf-8"), ctypes.byref(num_files))
    files = []
    for i in range(num_files.value):
        files.append(result[i].decode("utf-8"))
    return files
