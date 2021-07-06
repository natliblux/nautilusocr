## Important

The actions **train-epr**, **ocr**, **test-ocr** require this directory (`models/final/`) to include the following models:
* ocr model for every targeted font class (included in file name) ending in *.mlmodel*
* fcr model ending in *.h5*

The **enhance** action can optionally make use of:
* epr model ending in *jsonl*