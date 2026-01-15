import os
import json
import numpy as np
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from totalsegmentator.python_api import totalsegmentator

import SimpleITK as sitk

HU_thresholds = {
    "muscle": (-29, 150), # muscle: https://pmc.ncbi.nlm.nih.gov/articles/PMC4309522/
    "SAT": (-190, -30), # VAT/SAT: https://pmc.ncbi.nlm.nih.gov/articles/PMC5858805/
    "VAT": (-150, -50),
}

def get_sort_key(ds):
    ipp = getattr(ds, "ImagePositionPatient", None)

    if ipp and len(ipp) >= 3:
        try:
            return float(ipp[2])
        except Exception:
            pass

    # Fallback to instance number
    inst = getattr(ds, "InstanceNumber", None)

    if inst is not None:
        try:
            return float(inst)
        except Exception:
            pass

    return 0.0

def load_dicom_dataset(dicom_dir):
    dataset = []
    
    # Find and list all DICOM slices for one study
    for file in os.listdir(dicom_dir):
        path = os.path.join(dicom_dir, file)
        
        if not os.path.isfile(path):
            continue
        
        try: 
            dicom = dcmread(path)
        except (InvalidDicomError, OSError):
            continue
        
        dataset.append(dicom)
    
    # Sort all DICOM slices in the correct anatomical order
    # Priority: ImagePositionPatient[2] (Z-axis) -> InstanceNumber -> fallback to 0
    dataset = sorted(dataset, key=get_sort_key)
    
    return dataset

def to_hu(ds):
    slope = float(getattr(ds, "RescaleSlope", 1.0))
    intercept = float(getattr(ds, "RescaleIntercept", 0.0))

    arr = ds.pixel_array.astype(np.float32)

    return arr * slope + intercept

def load_hu_slab(dicom_dir, center_idx, half_window):
    dataset = load_dicom_dataset(dicom_dir)

    start = max(0, center_idx - half_window)
    end = min(len(dataset) - 1, center_idx + half_window)

    slab_ds = dataset[start : end + 1]  # inclusive
    slab_hu = np.stack([to_hu(ds) for ds in slab_ds], axis=0)  # (Z, H, W)

    return slab_hu, (start, end), dataset


def convert_to_nii(slab_hu, slab_path):
    with open("metadata/pixel_data.json", "r") as f:
        px = json.load(f)

    row_spacing = float(px["pixel_spacing"]["row_spacing_mm"])      # y
    col_spacing = float(px["pixel_spacing"]["column_spacing_mm"])   # x
    z_spacing = float(px.get("slice_thickness_mm", 1.0))            # z

    # SimpleITK expects numpy as (z, y, x) which matches your slab_hu (Z,H,W).
    img = sitk.GetImageFromArray(slab_hu.astype(np.float32))
    img.SetSpacing((col_spacing, row_spacing, z_spacing))

    sitk.WriteImage(img, slab_path)

    print(f"Saved NIfTI slab to: {slab_path}")


def segment_l3_slab(slab_path, output_path):

    segmentation_map = totalsegmentator(slab_path, output_path, task="total", ml=True)
    
    return segmentation_map


if __name__ == "__main__":
    dicom_ds_dir = "data/dataset/manifest-1765589194624/TCGA-COAD/TCGA-CK-6748/07-07-2000-NA-BWH CT ABDOMEN PELVIS OUTSIDE STUDY OICTAP-87264/5.000000-CEVol1.0Vol.-91258"

    with open("metadata/l3_slice_meta.json", "r") as f:
        meta = json.load(f)
    l3_idx = int(meta["slice_idx"]) 

    slab_hu, (start, end), dataset = load_hu_slab(dicom_ds_dir, center_idx=l3_idx, half_window=20)

    print(f"Slab indices: {start}..{end} (count={slab_hu.shape[0]})")
    print(f"Slab shape: {slab_hu.shape}  # (Z, H, W)")
    print(f"HU min/max: {slab_hu.min()} / {slab_hu.max()}")

    slab_path = "data/l3_slab.nii.gz"
    convert_to_nii(slab_hu, slab_path)

    mask_path = "figures/masks"
    mask = segment_l3_slab(slab_path, mask_path)




