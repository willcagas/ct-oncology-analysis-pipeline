import os
import json
import numpy as np
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

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

if __name__ == "__main__":
    dicom_ds_dir = "data/dataset/manifest-1765589194624/TCGA-COAD/TCGA-CK-6748/07-07-2000-NA-BWH CT ABDOMEN PELVIS OUTSIDE STUDY OICTAP-87264/5.000000-CEVol1.0Vol.-91258"


    with open("metadata/l3_slice_meta.json", "r") as f:
        meta = json.load(f)
    l3_idx = int(meta["slice_idx"]) 

    slab_hu, (start, end), dataset = load_hu_slab(dicom_ds_dir, center_idx=l3_idx, half_window=20)

    print(f"Slab indices: {start}..{end} (count={slab_hu.shape[0]})")
    print(f"Slab shape: {slab_hu.shape}  # (Z, H, W)")
    print(f"HU min/max: {slab_hu.min()} / {slab_hu.max()}")

