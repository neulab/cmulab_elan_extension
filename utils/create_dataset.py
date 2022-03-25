import os
import argparse
import pympi
# import pydub
from pathlib import Path
import hashlib
import shutil
import json
from collections import defaultdict


def create_dataset_from_eaf_files(eaf_files, output_dir, tier_names=None, annotators=None):
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    for eaf_file in eaf_files:
        input_eaf = pympi.Elan.Eaf(file_path=eaf_file)
        audio_file_path = input_eaf.media_descriptors[0]["MEDIA_URL"][len("file://"):]
        file_extension = os.path.splitext(audio_file_path)[1]

        with open(audio_file_path, "rb") as f:
            filedata = f.read() # read file as bytes
            audio_file_hash = hashlib.md5(filedata).hexdigest();

        dst_audio_file = (output_dir_path / (audio_file_hash + file_extension))
        dst_json_file = (output_dir_path / (audio_file_hash + ".json"))
        if not os.path.exists(dst_audio_file):
            shutil.copy2(audio_file_path, dst_audio_file.resolve())

        transcriptions = defaultdict(list)
        if os.path.exists(dst_json_file):
            transcriptions = json.loads(dst_json_file.read_text())

        for tier_name in input_eaf.get_tier_names():
            if tier_names and tier_name not in tier_names:
                continue
            annotator = input_eaf.get_parameters_for_tier(tier_name).get("ANNOTATOR")
            if annotators and annotator not in annotators:
                continue
            for start, end, transcription in input_eaf.get_annotation_data_for_tier(tier_name):
                if transcription.strip():
                    transcriptions[f"{start}-{end}"].append(transcription.strip())

        dst_json_file.write_text(json.dumps(transcriptions, indent=4, sort_keys=True, ensure_ascii=False))


# def create_dataset_from_eaf(eaf_file, output_dir, tier_name="Allosaurus"):
    # print(eaf_file)
    # print(output_dir)
    # print(tier_name)
    # output_dir_path = Path(output_dir)
    # output_dir_path.mkdir(parents=True, exist_ok=True)
    # input_eaf = pympi.Elan.Eaf(file_path=eaf_file)
    # audio_file_path = input_eaf.media_descriptors[0]["MEDIA_URL"][len("file://"):]
    # full_audio = pydub.AudioSegment.from_file(audio_file_path, format = 'wav')
    # for segment_id in input_eaf.tiers[tier_name][0]:
        # # eaf.get_parameters_for_tier(tier_name).get('ANNOTATOR')
        # start_id, end_id, transcription, _ = input_eaf.tiers[tier_name][0][segment_id]
        # start = input_eaf.timeslots[start_id]
        # end = input_eaf.timeslots[end_id]
        # clip = full_audio[start:end]
        # clip.export(output_dir_path / (segment_id + ".wav"), format = 'wav')
        # (output_dir_path / (segment_id + ".txt")).write_text(transcription)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="convert EAF file to dataset required for fine-tuning allosaurus")
    parser.add_argument('eaf_file', type=str, help="EAF file with phone transcriptions")
    parser.add_argument('output_dir', type=str, help="output dir")
    parser.add_argument('--tier', type=str, default="Allosaurus", help="Tier containing phone transcriptions")
    args = parser.parse_args()
    # create_dataset_from_eaf(args.eaf_file, args.output_dir, args.tier)
