# FINAL REPRODUCIBILITY

- **Source/Freeze Commit**: 1134f37aed1773bc25b8d9d19d645aa2622161ab
- **Final Tag**: icamma-2026-evidence-final-v4
- **Branch**: fix/final-prescriptive-validity-audit
- **Python Version**: 3.13.1 (tags/v3.13.1:0671451, Dec  3 2024, 19:06:28) [MSC v.1942 64 bit (AMD64)]
- **Random Seed**: 42
- **Raw Dataset**: USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv (Not packaged in evidence bundle)
- **Target Definition**: late_delivery = 1 when On Time (OTD) == 'N'. OTD = delivery within the defined window from 14 days before through 7 days after the Agreed Delivery Date.
- **Note on 2024**: 2024 contains partial/available observations.

## Temporal Splits
- **Protocol A train**: observations up to end of 2021
- **Protocol B train**: observations up to end of 2022
- **Validation**: forward rolling windows
- **Test**: 2023 and available 2024 observations

## Strict Feature List
- Order Entry Date, calendar_month, Fulfillment Method, Transportation Mode, Order Type, Product Category, D365 Health Element, Fiscal_Year_Funding, D365 Funding Source, Vendor Incoterm, Country, Illustrative Price, UOM, Framework Contract, Destination Incoterm, Order Number

## Execution Commands
`ash
python -m src.run_final_audit
python -m src.freeze_final_bundle
`

## Environment Versions
`
aiohappyeyeballs==2.6.1
aiohttp==3.12.6
aiosignal==1.3.2
annotated-types==0.7.0
anyio==4.9.0
attrs==25.3.0
audioop-lts==0.2.1
bip-utils==2.9.3
bitarray==3.4.2
cachetools==5.5.2
catboost==1.2.10
cbor2==5.6.5
certifi==2024.12.14
cffi==2.0.0
charset-normalizer==3.4.2
ckzg==2.1.1
click==8.2.1
coincurve==21.0.0
colorama==0.4.6
construct==2.10.68
construct-typing==0.6.2
contourpy==1.3.3
crcmod==1.7
cryptography==48.0.1
cycler==0.12.1
cytoolz==1.0.1
distlib==0.3.9
ecdsa==0.19.1
ed25519-blake2b==1.4.1
et_xmlfile==2.0.0
eth-account==0.13.7
eth-hash==0.7.1
eth-keyfile==0.8.1
eth-keys==0.7.0
eth-rlp==2.2.0
eth-typing==5.2.1
eth-utils==5.3.0
eth_abi==5.2.0
fastapi==0.115.12
filelock==3.16.1
fonttools==4.62.1
frozenlist==1.6.0
google-ai-generativelanguage==0.6.15
google-api-core==2.25.0rc1
google-api-python-client==2.170.0
google-auth==2.40.2
google-auth-httplib2==0.2.0
google-generativeai==0.8.5
googleapis-common-protos==1.70.0
graphviz==0.21
grpcio==1.71.0
grpcio-status==1.71.0
h11==0.16.0
hexbytes==1.3.1
httpcore==1.0.9
httplib2==0.22.0
httpx==0.28.1
idna==3.10
iniconfig==2.3.0
joblib==1.5.3
jsonalias==0.1.1
kiwisolver==1.5.0
matplotlib==3.10.8
mnemonic==0.21
multidict==6.4.4
narwhals==2.25.0
numpy==2.2.6
openpyxl==3.1.5
packaging==24.2
pandas==2.2.3
parsimonious==0.10.0
pdfminer.six==20251230
pdfplumber==0.11.9
pillow==12.1.0
pipenv==2024.4.0
platformdirs==4.3.6
plotly==6.9.0
pluggy==1.6.0
propcache==0.3.1
proto-plus==1.26.1
protobuf==5.29.5
psycopg2==2.9.10
PuLP==3.3.2
py-sr25519-bindings==0.2.2
pyasn1==0.6.1
pyasn1_modules==0.4.2
PyAudio==0.2.14
pycparser==2.22
pycryptodome==3.23.0
pydantic==2.11.5
pydantic-settings==2.12.0
pydantic_core==2.33.2
pyfiglet==1.0.4
Pygments==2.19.2
PyMuPDF==1.27.2.3
PyNaCl==1.5.0
pyparsing==3.2.3
pypdfium2==5.9.0
pytest==9.0.2
python-calamine==0.6.1
python-dateutil==2.9.0.post0
python-dotenv==1.1.0
python-multipart==0.0.22
pytz==2025.2
pyunormalize==16.0.0
pywin32==310
regex==2024.11.6
reportlab==4.4.9
requests==2.32.3
rlp==4.1.0
rsa==4.9.1
scikit-learn==1.9.0
scipy==1.15.3
setuptools==75.6.0
six==1.17.0
sniffio==1.3.1
solana==0.36.7
solders==0.26.0
sounddevice==0.5.2
SpeechRecognition==3.14.3
standard-aifc==3.13.0
standard-chunk==3.13.0
starlette==0.46.2
tabulate==0.10.0
tenacity==9.1.2
threadpoolctl==3.6.0
toolz==1.0.0
tqdm==4.67.1
types-requests==2.32.0.20250515
typing-inspection==0.4.1
typing_extensions==4.13.2
tzdata==2025.2
uritemplate==4.1.1
urllib3==2.4.0
uvicorn==0.34.2
virtualenv==20.28.0
web3==7.12.0
websockets==15.0.1
xgboost==3.4.1
yarl==1.20.0
z3-solver==4.15.4.0
`

## Output Manifest
- outputs/tables/final_predictive_ablation.csv
- outputs/tables/final_bootstrap_differences.csv
- outputs/tables/final_protocol_contrast.csv
- outputs/tables/final_ice_curves.csv
- outputs/tables/final_temporal_response_stability.csv
- outputs/tables/final_empirical_holdout.csv
- outputs/tables/final_empirical_product_summary.csv
- outputs/figures/*.png and *.pdf