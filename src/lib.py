import os, json
from datetime import datetime

import filedate
import progressbar
from exif import Image as ImageExif

from src import file_utils

FIX_FILE_EXTENSIONS = None
CONVERT_HEIC_TO_JPG = None
REMOVE_MP4_FOR_LIVE_PHOTO = None


def __apply_exif(img_fname: str, dt: datetime):
    fmt = "%Y:%m:%d %H:%M:%S"
    dt_str = dt.strftime(fmt)

    try:
        with open(img_fname, "rb") as f:
            image = ImageExif(f)
        try:
            image.datetime = dt_str
            image.datetime_original = dt_str
            image.datetime_digitized = dt_str
        except:
            pass
        with open(img_fname, "wb") as f:
            f.write(image.get_file())
    except:
        pass


def __apply_os_metadata(img_fname: str, dt: datetime):
    fmt = "%Y.%m.%d %H:%M:%S"
    dt_str = dt.strftime(fmt)

    fdate = filedate.File(img_fname)
    fdate.set(
        created = dt_str,
	    modified = dt_str,
	    accessed = dt_str
    )


def apply_metadata(img_path: str, json_path: str):
    if os.path.basename(json_path).startswith('._'):
        return
    with open(json_path) as json_f:
        md = json.load(json_f)

    times = md.get("photoTakenTime", md.get("creationTime", {}))
    time_num = int(times.get("timestamp"))
    if not time_num:
        return
    dt = datetime.fromtimestamp(time_num)

    __apply_exif(img_path, dt)
    __apply_os_metadata(img_path, dt)


def apply_image_fixes(file_pairs):
    bar = progressbar.ProgressBar()
    for dirname in bar(file_pairs):
        print("Applying file fixes for directory:", dirname)
        for key in file_pairs[dirname]:
            pair = file_pairs[dirname][key]
            can_fix_extensions = FIX_FILE_EXTENSIONS and len(pair.get("images", set()))
            if CONVERT_HEIC_TO_JPG or can_fix_extensions:
                new_set = set()
                for img_fname in pair.get("images", set()):
                    img_path = f"{dirname}{'/' if dirname else ''}{img_fname}"
                    new_img_path = None
                    can_convert = CONVERT_HEIC_TO_JPG and file_utils.is_heic(img_path)
                    if can_convert:
                        new_img_path = file_utils.convert_heic_to_jpg(img_path)
                    elif can_fix_extensions:
                        new_img_path = file_utils.fix_incorrect_extension(img_path)
                    if new_img_path:
                        _, new_prefix, new_ext = file_utils.get_file_details(new_img_path)
                        new_img_fname = new_prefix + new_ext
                    else:
                        new_img_fname = None
                    new_set.add(new_img_fname or img_fname)
                pair["images"] = new_set


# Entry point for this script
def process_files_in_dir(path: str) -> int:
    files = file_utils.get_file_paths(path)
    file_pairs = file_utils.group_files_by_name(files)

    # if FIX_FILE_EXTENSIONS or CONVERT_HEIC_TO_JPG:
    #     apply_image_fixes(file_pairs)

    imgs_modified = 0
    print("Applying metadata...")
    bar = progressbar.ProgressBar()
    for dirname in bar(file_pairs):
        for key in file_pairs[dirname]:
            pair = file_pairs[dirname][key]
            if len(pair) < 2 or next(iter(pair['images'])).startswith('._'):
                continue
            for img in pair["images"]:
                apply_metadata(f"{dirname}{'/' if dirname else ''}{img}",
                               f"{dirname}{'/' if dirname else ''}{pair['json']}")
                imgs_modified += 1
            os.remove(f"{dirname}/{pair['json']}")
            if REMOVE_MP4_FOR_LIVE_PHOTO:
                mp4_file = next((file for file in pair['images'] if file.endswith('.MP4')), None)
                if mp4_file is not None and len(pair['images']) > 1:
                    os.remove(f"{dirname}/{mp4_file}")
                else:
                    mp4_file = next((file for file in pair['images'] if file.endswith('.mp4')), None)
                    if mp4_file is not None and len(pair['images']) > 1:
                        os.remove(f"{dirname}/{mp4_file}")
    return imgs_modified


if __name__ == "__main__":
    raise Exception("Do not run the program from this file. Instead, run the run.py file.")
