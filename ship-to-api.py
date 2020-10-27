"""processing script for ship detection data"""
import csv
import json
import os
import subprocess
from glob import glob


def get_location(loc):
    """get location id of detections"""
    if loc == "New York":
        return "ny"
    elif loc == "San Francisco":
        return "sf"
    else:
        return "la"


def file_to_scene(f):
    """convert filename of tif to scene"""
    b = (
        os.path.basename(f)
        .replace("reprojected_", "")
        .replace("_resampled", "")
        .replace("_3B_Visual.tif", "")
        .replace("T", "_")
    )
    if b[-5] != "_":
        b = f"{b[:-4]}_{b[-4:]}"
    s = b.split("_")
    if len(s[1]) > 6:
        b = f"{s[0]}_{s[1][:6]}_{s[1][6:]}_{s[2]}"
    return b


with open("ships.geojson") as f:
    data = json.load(f)

with open("tifs.txt") as f:
    tifs = [line.strip() for line in f.readlines()]

scene_to_file_dict = dict(zip([file_to_scene(t) for t in tifs], tifs))


def scene_to_file(s):
    """convert scene to file name"""
    file = scene_to_file_dict.get(s)
    if not file:
        possible = [t for t in tifs if s in t]
        if possible:
            file = possible[0]
        else:
            print(f"no match for {s}")
    return file


for d in data:
    if "features" in d["ship_detections"]:
        date = d["date"].replace("-", "_")
        location = get_location(d["location"])
        detections = d["ship_detections"]
        # write geojson of detection
        with open(f"ship/{location}/{date}.geojson", "w") as w:
            w.write(json.dumps(detections))
        # append detection count to csv
        with open(f"ship_csvs/{location}.csv", "a+") as a:
            a.write(f'{date},{len(detections["features"])}\n')
        # create VRT for scene_ids
        with open("filelist.txt", "w") as fl:
            files = [
                f"/vsis3/image-labeling-tool-internal/{scene_to_file(s)}\n"
                for s in d["scene_ids"]
                if scene_to_file(s)
            ]
            fl.writelines(files)

        subprocess.run(
            [
                "gdalbuildvrt",
                "-input_file_list",
                "filelist.txt",
                f"{location}-{date}.vrt",
            ]
        )

# sort and add headers to the csvs
for file in glob("ship_csvs/*"):
    with open(file) as csvfile:
        reader = csv.reader(csvfile)
        sortedlist = sorted(reader, key=lambda row: row[0])

    with open(file, "w") as f:
        fieldnames = ["date", "count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sortedlist:
            writer.writerow(dict(date=row[0], count=row[1]))
