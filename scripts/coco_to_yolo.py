import json
import os

def convert_coco_to_yolo(coco_file, output_dir):
    with open(coco_file, "r") as f:
        coco_data = json.load(f)

    image_id_to_filename = {}
    for image in coco_data["images"]:
        image_id_to_filename[image["id"]] = image["file_name"]

    for annotation in coco_data["annotations"]:
        image_id = annotation["image_id"]
        filename = image_id_to_filename[image_id]
        label_file = os.path.join(output_dir, filename.replace(".jpg", ".txt"))

        with open(label_file, "a") as f:
            category_id = annotation["category_id"]
            bbox = annotation["bbox"]
            x_center = (bbox[0] + bbox[2] / 2) / image["width"]
            y_center = (bbox[1] + bbox[3] / 2) / image["height"]
            width = bbox[2] / image["width"]
            height = bbox[3] / image["height"]

            f.write(f"{category_id} {x_center} {y_center} {width} {height}\n")

# COCO 어노테이션 파일 경로
coco_file = "dataset/annotations/instances_train2017.json"

# YOLO 레이블 파일 저장 디렉토리
output_dir = "dataset/labels/train"

# COCO 어노테이션을 YOLO 형식으로 변환
convert_coco_to_yolo(coco_file, output_dir)