import os, zipfile
from typing import Optional, Tuple, List, Dict

import whatimage
from PIL import Image as ImagePIL
from pillow_heif import register_heif_opener


def __get_key(fname: str) -> str:
    # -- Assumes this structure --
    # Image:
    #   filename1.HEIC
    # Json:
    #   filename1.HEIC.json
    # So 'key' should be:
    #   filename1
    _, prefix, ext = get_file_details(fname)
    if ext == ".json":
        key = os.path.splitext(os.path.splitext(prefix)[0])[0]
    elif "-edited" in prefix:
        key = prefix.split("-edited")[0]
    else:
        key = prefix
    return key


def __search_dir_for_files(dirname: str) -> List[str]:
    if not os.path.isdir(dirname):
        raise Exception(f'"{dirname}" is not a directory')
    list_of_file_paths = []
    stack = [dirname]
    while stack:
        cur = stack.pop()
        if os.path.isdir(cur):
            for item in os.listdir(cur):
                stack.append(f"{cur}/{item}")
        else:
            list_of_file_paths.append(cur)
    return list_of_file_paths


def is_heic(img_path: str) -> bool:
    with open(img_path, "rb") as f:
        img_fmt = whatimage.identify_image(f.read())
    return img_fmt == "heic"


def convert_heic_to_jpg(img_path: str) -> str:
    dirname, prefix, ext = get_file_details(img_path)
    jpg_path = f"{dirname}{'/' if dirname else ''}{prefix}.jpg"

    register_heif_opener()
    with ImagePIL.open(img_path) as f:
        f.save(jpg_path)
    os.remove(img_path)

    _, jpg_prefix, jpg_ext = get_file_details(jpg_path)
    print(f"Converted: {prefix + ext} -> {jpg_prefix + jpg_ext}")
    return jpg_path


def fix_incorrect_extension(img_path) -> Optional[str]:
    with open(img_path, "rb") as f:
        img_fmt = whatimage.identify_image(f.read())
    dirname, prefix, ext = get_file_details(img_path)

    if img_fmt and img_fmt.lower() == "jpeg":
        img_fmt = "jpg"
    if ext == ".jpeg":
        ext = ".jpg"

    if img_fmt and ext[1:].lower() != img_fmt.lower():
        new_img_path = f"{dirname}{'/' if dirname else ''}{prefix}.{img_fmt.lower()}"
        os.rename(img_path, new_img_path)
        _, new_prefix, new_ext = get_file_details(new_img_path)
        _, old_prefix, old_ext = get_file_details(img_path)
        print(f"Renamed: {old_prefix + old_ext} -> {new_prefix + new_ext}")
        return new_img_path
    return None


def group_files_by_name(files: List[str]) -> Dict:
    file_pairs = {}

    files = sorted(files)
    for fname in files:
        dirname, prefix, ext = get_file_details(fname)
        key = __get_key(fname)
        pair = file_pairs.setdefault(dirname, {}).setdefault(key, {})

        if fname[-5:].lower() == ".json":
            pair["json"] = prefix + ext
        else:
            images = pair.setdefault("images", set())
            images.add(prefix + ext)

    return file_pairs


def get_file_paths(path: str) -> List[str]:
    if os.path.isdir(path):
        return __search_dir_for_files(path)
    elif zipfile.is_zipfile(path):
        dirname, prefix, _ = get_file_details(path)
        extracted_path = f"{dirname}{'/' if dirname else ''}{prefix}"
        print("Extracting...")
        with zipfile.ZipFile(path, "r") as zip_obj:
            zip_obj.extractall(extracted_path)
        return __search_dir_for_files(extracted_path)
    else:
        raise Exception("Only directories and zip files are allowed to be entered as an arg to this script")


def get_file_details(full_name: str) -> Tuple[str, str, str]:
    dirname = os.path.dirname(full_name)
    basename = os.path.basename(full_name)
    prefix, ext = os.path.splitext(basename)
    return (dirname, prefix, ext)


if __name__ == "__main__":
    raise Exception("Do not run the program from this file. Instead, run the run.py file.")
