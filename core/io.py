"""
Input/Output operations for medical imaging data.

This module handles:
- Loading DICOM files
- Reading CT scan data
- Saving processed images
- Data format conversions
"""

import numpy as np
import os
import json
import SimpleITK as sitk

from pydicom import dcmread
from pydicom.errors import InvalidDicomError


def get_sort_key(dicom):
    """
    Get sort key for DICOM slice with fallback logic:
    1. Try ImagePositionPatient[2] (Z-axis) - most anatomically accurate
    2. Fall back to InstanceNumber if ImagePositionPatient unavailable
    3. Fall back to 0 if neither available (maintains original order)
    """

    # First try ImagePositionPatient[2] (Z-axis position)
    if hasattr(dicom, 'ImagePositionPatient') and dicom.ImagePositionPatient:
        try:
            return float(dicom.ImagePositionPatient[2])
        except (ValueError, IndexError, TypeError):
            pass
    
    # Fall back to InstanceNumber
    if hasattr(dicom, 'InstanceNumber') and dicom.InstanceNumber is not None:
        try:
            return float(dicom.InstanceNumber)
        except (ValueError, TypeError):
            pass
    
    # Final fallback: return 0 to maintain original order for slices without either attribute
    return 0


def load_dicom_dataset(dicom_dir):
    """
    Load and sort DICOM files from a directory.
    """
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


def extract_and_save_pixel_data(dataset, output_path="metadata/pixel_data.json"):
    """
    Extract PixelSpacing and SliceThickness from a DICOM dataset and save to JSON.
    """
    # Choose a rep. slice (PixelSpacing should be consistent across a series of CT slices)
    dicom_slice = dataset[0]

    metadata = {
        "pixel_spacing": None,
        "slice_thickness_mm": None,
        "spacing_between_slices_mm": None,
        "units": "mm",
        "notes": [],
    }

    # PixelSpacing: (0028,0030) => [row_spacing (y), col_spacing (x)]
    pixel_spacing = getattr(dicom_slice, "PixelSpacing", None)

    if pixel_spacing and len(pixel_spacing) >= 2:
        row_spacing = float(pixel_spacing[0])
        col_spacing = float(pixel_spacing[1])

        metadata["pixel_spacing"] = {
            "row_spacing_mm": row_spacing,      # y spacing
            "column_spacing_mm": col_spacing,   # x spacing
            "order": "[row(y), column(x)]",
        }

    # SliceThickness: (0018,0050)
    slice_thickness = getattr(dicom_slice, "SliceThickness", None)

    if slice_thickness and slice_thickness != "":
        metadata["slice_thickness_mm"] = float(slice_thickness)

    # SpacingBetweenSlices: (0018,0088)
    spacing_between = getattr(dicom_slice, "SpacingBetweenSlices", None)

    if spacing_between and spacing_between != "":
        metadata["spacing_between_slices_mm"] = float(spacing_between)
        
    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Save JSON
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata

if __name__ == "__main__":
    # Load dataset from specified directory
    dicom_ds_dir = "data/dataset/manifest-1765589194624/TCGA-COAD/TCGA-CK-6748/07-07-2000-NA-BWH CT ABDOMEN PELVIS OUTSIDE STUDY OICTAP-87264/5.000000-CEVol1.0Vol.-91258"
    dataset = load_dicom_dataset(dicom_ds_dir)

    # Find and locate L3 slice
    slice_idx = 315 # Specific L3 slice index
    dicom_slice = dataset[slice_idx]
    raw_slice = dataset[slice_idx].pixel_array

    # Convert L3 slice to HU
    slope = float(getattr(dicom_slice, "RescaleSlope", 1.0))
    intercept = float(getattr(dicom_slice, "RescaleIntercept", 0.0))

    # Convert to float32 gives numerical precision
    slice_HU = raw_slice.astype(np.float32) * slope + intercept

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, "l3_slice_hu.npy"), slice_HU)

    # After loading the dataset
    # Extract and save pixel spacing metadata
    pixel_metadata = extract_and_save_pixel_data(dataset, output_path='metadata/pixel_data.json')
    print(f"Pixel data: {pixel_metadata}")

    l3_meta = {
        "dicom_dir": dicom_ds_dir,
        "slice_idx": slice_idx,
        "z_mm": float(dicom_slice.ImagePositionPatient[2]) if hasattr(dicom_slice, "ImagePositionPatient") else None
    }

    with open("metadata/l3_slice_meta.json", "w") as f:
        json.dump(l3_meta, f, indent=2)


