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


def load_dicom_dataset(dicom_dir, recursive=True):
    """
    Load and sort DICOM files from a directory.
    
    Args:
        dicom_dir (str): Path to directory containing DICOM files
        recursive (bool): If True, search subdirectories for DICOM files
        
    Returns:
        list: Sorted list of DICOM dataset objects, ordered by anatomical position
              (or InstanceNumber as fallback)
    """
    dataset = []
    
    # Find and list all DICOM slices for one study
    for file in os.listdir(dicom_dir):
        print(file)
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


# Load dataset from specified directory
dicom_ds_dir = "data/manifest-1765589194624/TCGA-COAD/TCGA-CK-6748/07-07-2000-NA-BWH CT ABDOMEN PELVIS OUTSIDE STUDY OICTAP-87264/5.000000-CEVol1.0Vol.-91258"
dataset = load_dicom_dataset(dicom_ds_dir)

# Stack pixel arrays into a 3D volume
if not dataset:
    raise ValueError("No DICOM files loaded. Cannot create volume.")
volume = np.stack([f.pixel_array for f in dataset])

# Find and locate L3 slice
slice_idx = 315 # Specific L3 slice index
if slice_idx >= len(volume):
    raise ValueError(f"Slice index {slice_idx} is out of range. Volume has {len(volume)} slices.")
raw_slice = volume[slice_idx]

print(raw_slice.dtype)

dicom_slice = dataset[slice_idx]

# Convert L3 slice to HU
slope = float(getattr(dicom_slice, "RescaleSlope", 1.0))
intercept = float(getattr(dicom_slice, "RescaleIntercept", 0.0))

slice_HU = raw_slice.astype(np.float32) * slope + intercept

output_dir = "data"
os.makedirs(output_dir, exist_ok=True)
np.save(os.path.join(output_dir, "baseline_slice.npy"), slice_HU)

def extract_and_save_pixel_spacing(dataset, output_path='metadata/pixel_spacing.json'):
    """
    Extract PixelSpacing from a DICOM dataset and save to JSON.
    
    Args:
        dataset: List of DICOM dataset objects (or single dataset)
        output_path: Path to save the metadata JSON file
    
    Returns:
        dict: Dictionary containing pixel spacing metadata
    """
    # Get PixelSpacing from first slice (should be same across all slices in series)
    if isinstance(dataset, list):
        dicom_slice = dataset[0]
    else:
        dicom_slice = dataset
    
    # Extract PixelSpacing (Tag (0018,0050) - 2D array: [row_spacing, column_spacing])
    if hasattr(dicom_slice, 'PixelSpacing') and dicom_slice.PixelSpacing:
        pixel_spacing = dicom_slice.PixelSpacing
        # Convert to list of floats (pydicom returns as list of strings)
        row_spacing = float(pixel_spacing[0])
        col_spacing = float(pixel_spacing[1])
        
        metadata = {
            'pixel_spacing': {
                'row_spacing_mm': row_spacing,
                'column_spacing_mm': col_spacing,
                'units': 'mm',
                'description': 'Physical spacing between pixels in row (y) and column (x) directions'
            },
            'has_two_values': True,
            'note': 'Required for mm-based measurements (RECIST diameter, area calculations)'
        }
    else:
        metadata = {
            'pixel_spacing': None,
            'has_two_values': False,
            'note': 'PixelSpacing not found in DICOM header'
        }
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

# After loading the dataset
# Extract and save pixel spacing metadata
pixel_spacing_metadata = extract_and_save_pixel_spacing(dataset, output_path='metadata/pixel_spacing.json')
print(f"Pixel spacing: {pixel_spacing_metadata}")





