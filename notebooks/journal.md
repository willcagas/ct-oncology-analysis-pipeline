

## Day 1

- Surfed though TCIA (The Cancer Imaging Archive) for a proper CT scan dataset
- Decided to use TCGA-COAD, specifically downloading one study from one patient
- Wrote to code to load and correctly order the DICOM files based on anatomical structure and how each DICOM slice has an "Image Position Patient" property
- found the L3 slice by finding the level where both psoas muscles are visible, before the iliac crest appears
- Studied full in-depth explanation into DICOM files: https://www.youtube.com/watch?v=eLS9nDVJx5Y
- found notes on CT scans and dicom on Nucleo founder's X: https://oil-exhaust-7d6.notion.site/CT-scans-and-dicom-files-1d4ec46124188093a0f8dbc8c1185fc8 
All quantitative analysis was performed in native Hounsfield Unit space, with windowing applied only for visualization.
- pydicom: read series, sort, compute HU volume, extract pixel spacing
- implemented conversion from raw pixel arrays to the Housenfield Unit (HU) which is used to measure the radiodensity of physical tissue
- NumPy: slice extraction, synthetic follow-up generation math, saving .npy
- learned about the types RECIST responses including PD, PR, CR, SD
- find and extract pixel spacing
- L3 refers to third vertebra in my lower back (lumbar spine) - includes major muscle groups (i.e. psoas - pronounced so-as, paraspinals, abdominal wall)
- CSA (cross-sectional muscle area) is the total skeletal muscle area visible in a single slice (i.e. cross section) of that body at the L3 level
- so essentially, instead of scanning the whole body to determine the entire body muscle mass, the standard practice is to find an L3 slice and take a single measurement of that cross section's total muscle area and this can correlate well to assess entire body mass
- we extract pixel spacing to represent how much space a pixel represents in real life (i.e. 0.7 mm x 0.7 mm)
- tldr; built a CT-ingestion pipeline that sorts DICOM slices anatomically, then manually identified L3 slice for assessing body masss, then converted said slice's raw pixel data to HU for actual clinically-relevant tissue informatiom, then extracted physical imaging metadata for conducting downstream clinical tasks

## Day 2

- sarcopenia is loss of skeletal muscle mass
- in cancer patients, bmi and weight (standard metrics) are not enough -> need to look at muscle mass and body composition
- use body comp to discern between skeletal muscle and fat (visceral fat and subcutaneous fat) - these are specific biomarkers
- validated HU range in L3 slice seeing minimum of -2048 HU and max 1466 HU 
- use total segmentator : https://github.com/wasserth/TotalSegmentator
- perform tissue segmentation on a localized L3 region rather than the full CT volume to reflect standard sarcopenia assessment protocols
- created a 3d slab around the L3 slice ~40 slices at 1mm thickness each

