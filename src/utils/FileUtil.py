import os
def get_filepath_shortname_suffix(file_url):
    """
    获取文件路径， 文件名， 后缀名
    :param file_url:
    :return:
    """
    filepath, tmpfilename = os.path.split(file_url)
    shotname, extension = os.path.splitext(tmpfilename)
    return filepath, shotname, extension

def get_file_suffix(file_url):
    return os.path.splitext(file_url)[-1].lower()

def get_file_name_without_suffix(file_url):
    return os.path.splitext(file_url)[-2]
