

## Day 1

- Surfed though TCIA (The Cancer Imaging Archive) for a proper CT scan dataset
- Decided to use TCGA-COAD, specifically downloading one study from one patient
- Wrote to code to load and correctly order the DICOM files based on anatomical structure and how each DICOM slice has an "Image Position Patient" property
- Correctly looked for L3 slice based on 
An axial CT slice at approximately the L3 vertebral level was selected based on bilateral psoas muscle visualization and confirmed absence of iliac crest structures
- Studied full in-depth explanation into DICOM files: https://www.youtube.com/watch?v=eLS9nDVJx5Y
- found notes on CT scans and dicom on Nucleo founder's X: https://oil-exhaust-7d6.notion.site/CT-scans-and-dicom-files-1d4ec46124188093a0f8dbc8c1185fc8 
All quantitative analysis was performed in native Hounsfield Unit space, with windowing applied only for visualization.
- pydicom: read series, sort, compute HU volume, extract pixel spacing
- implemented conversion from raw pixel arrays to the Housenfield Unit (HU) which is used to measure the radiodensity of physical tissue
- NumPy: slice extraction, synthetic follow-up generation math, saving .npy
- learned about the types RECIST responses including PD, PR, CR, SD
- find and extract pixel spacing
