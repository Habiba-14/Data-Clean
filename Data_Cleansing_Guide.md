# DATA CLEANSING GUIDE (Step-by-Step)
## EG Retail Sales - Case Study 1

**Author:** Salma Abdelkader  
**Date:** November 18, 2024  
**Script Reference:** Retail_Sales_Cleaned.py  
**Purpose:** Step-by-step documentation of data cleaning procedures applied to raw data

---

## TABLE OF CONTENTS
1. [Setup & Data Loading](#1-setup--data-loading)
2. [OrderID Handling](#2-orderid-handling)
3. [Date Columns Cleaning](#3-date-columns-cleaning)
4. [Customer Information](#4-customer-information)
5. [Geographic Data](#5-geographic-data)
6. [Product Information](#6-product-information)
7. [Monetary Columns](#7-monetary-columns)
8. [Transactional Columns](#8-transactional-columns)
9. [BI-Ready Dataset Creation](#9-bi-ready-dataset-creation)

---

## 1. SETUP & DATA LOADING

### 1.1 Import Required Libraries
**Script Lines:** 1-6

```python
import pandas as pd
import numpy as np
from dateutil import parser
import re
import seaborn as sns
import matplotlib.pyplot as plt
```

**Purpose:**
- `pandas`: Data manipulation
- `numpy`: Numerical operations and NaN handling
- `dateutil.parser`: Parse mixed date formats
- `re`: Regular expressions for pattern matching (currency, text cleaning)
- `seaborn/matplotlib`: Data visualization

---

### 1.2 Load Excel File
**Script Lines:** 8-18

```python
file_path = "EG_Retail_Sales_Raw_CaseStudy 1.xlsx"
all_sheets = pd.read_excel(file_path, sheet_name=None)
sales = all_sheets["Sales_Orders_Raw"]
products = all_sheets["Products_Raw"]
govs = all_sheets["Governorates_Lookup_Noise"]
customers = all_sheets["Customers_Raw"]
```

**Action:** Load all four sheets into separate DataFrames for cleaning

---

### 1.3 Set Display Options
**Script Lines:** 21-26

**Purpose:** Configure pandas to display all columns and format floats consistently for inspection

---

## 2. ORDERID HANDLING

### 2.1 Issue Identified
**Script Lines:** 29-44

**Problem:** 
- No row-level duplicates found
- BUT: Same OrderID appears multiple times with COMPLETELY different data (CustomerID, ProductSKU, amounts, etc.)
- This suggests OrderID reuse or generation failure

### 2.2 Investigation
**Script Lines:** 53-60

**Method:**
```python
inconsistent_orders = sales.groupby('OrderID').filter(lambda x: x['CustomerID'].nunique() > 1)
```

**Result:** Identified orders where same OrderID has multiple different CustomerIDs

### 2.3 Solution: Create Unique IDs
**Script Lines:** 64-92

**Approach:**
1. Keep original OrderID in new column `Original OrderID`
2. Create `OrderID_cleaned` with unique values for all duplicates
3. For duplicated OrderIDs, generate new IDs: NEW00001, NEW00002, etc.
4. Add flag column `is_OrderID_duplicated_flag` (True/False)

**Code Logic:**
```python
def create_cleaned_id(df):
    duplicated_mask = df['OrderID'].duplicated(keep=False)
    df['OrderID_cleaned'] = df['OrderID']
    
    if duplicated_mask.any():
        cum_count = df[duplicated_mask].groupby('OrderID').cumcount()
        unique_suffix = cum_count.apply(lambda x: f"NEW{x:05d}")
        df.loc[duplicated_mask, 'OrderID_cleaned'] = unique_suffix
    
    return df
```

**Validation:**
- Verify `OrderID_cleaned` is now 100% unique
- Check that flag correctly identifies all originally duplicated records

**Business Note:** Requires investigation to determine which records are valid. Flag allows traceability.

---

## 3. DATE COLUMNS CLEANING

### 3.1 Issues Identified
**Script Lines:** 113-169

**Problems:**
1. **Mixed formats:** YYYY-MM-DD, DD/MM/YYYY, MM-DD-YY, Arabic month names
2. **Nulls:** OrderDate (12), DeliveryDate (25), ReturnDate (120)
3. **Logic violations:**
   - DeliveryDate < OrderDate (12 records)
   - ReturnDate < OrderDate (5 records)
   - ReturnDate < DeliveryDate (8 records)

### 3.2 Date Parsing Function
**Script Lines:** 120-126

```python
def clean_date_robust(x):
    try:
        return parser.parse(str(x), dayfirst=True)
    except (ValueError, TypeError):
        return pd.NaT
```

**Why `dayfirst=True`?** Egyptian date formats typically use DD/MM/YYYY

### 3.3 Apply to All Date Columns
**Script Lines:** 128-131

```python
sales["OrderDate"] = sales["OrderDate"].apply(clean_date_robust)
sales["DeliveryDate"] = sales["DeliveryDate"].apply(clean_date_robust)
sales["ReturnDate"] = sales["ReturnDate"].apply(clean_date_robust)
```

**Result:** All dates converted to pandas datetime64[ns] type, invalid values → NaT

---

### 3.4 ReturnFlag Standardization
**Script Lines:** 136-145

**Problem:** 7 variations: "نعم", "Y", "1", "لا", "0", "N"

**Solution:**
```python
return_flag_map = {'نعم': 'Yes', 'Y': 'Yes', '1': 'Yes', 
                   'لا': 'No', '0': 'No', 'N': 'No'}
sales['ReturnFlag_Clean'] = sales['ReturnFlag'].replace(return_flag_map)
```

**Result:** Only "Yes" and "No" values

---

### 3.5 Date Logic Validation Flags
**Script Lines:** 154-174

**Created Flags:**
```python
sales['delivery_is_before_order'] = sales['DeliveryDate'] < sales['OrderDate']
sales['return_is_before_order'] = sales['ReturnDate'] < sales['OrderDate']
sales['return_is_before_delivery'] = sales['ReturnDate'] < sales['DeliveryDate']
sales['orderdate_is_null'] = sales['OrderDate'].isnull()
sales['deliverydate_is_null'] = sales['DeliveryDate'].isnull()
```

**Purpose:** Flag impossible dates for investigation; DO NOT auto-correct (preserve data integrity)

---

### 3.6 BI-Ready Date Columns
**Script Lines:** 186-232

**Created Columns for Analytics:**

**Extracted Date Parts:**
```python
sales['Order_Year'] = sales['OrderDate'].dt.year
sales['Order_Month'] = sales['OrderDate'].dt.month
sales['Order_Quarter'] = sales['OrderDate'].dt.quarter
sales['Order_YearMonth'] = sales['OrderDate'].dt.to_period('M').astype(str)
```

**Calculated Metrics:**
```python
sales['Delivery_Time_Days'] = (sales['DeliveryDate'] - sales['OrderDate']).dt.days
sales['Delivery_Delayed'] = sales['Delivery_Time_Days'] > 5  # 5-day SLA
sales['Return_Time_Days'] = (sales['ReturnDate'] - sales['DeliveryDate']).dt.days
```

**Validity Flags:**
```python
sales['Valid_Delivery'] = (DeliveryDate valid) & (DeliveryDate >= OrderDate)
sales['Valid_Return'] = (ReturnDate valid) & (ReturnDate >= DeliveryDate)
```

**Applied to:** Order, Delivery, and Return dates

**Business Value:** Enable time-series analysis, trend detection, SLA tracking

---

## 4. CUSTOMER INFORMATION

### 4.1 CustomerName
**Script Lines:** 240-247

**Issue:** Mixed case, Arabic/English names

**Solution:**
```python
sales['CustomerName_clean'] = sales['CustomerName'].astype(str).str.strip().str.lower()
```

**Actions:**
- Convert to string (handle edge cases)
- Remove leading/trailing spaces
- Lowercase for consistency

---

### 4.2 Gender
**Script Lines:** 284-298

**Problem:** 6 variations: "M", "F", "ذكر", "أنثى", "Male", "Female", + nulls

**Solution:**
```python
gender_map = {"M": "Male", "F": "Female", "ذكر": "Male", "أنثى": "Female"}
sales['Gender_Clean'] = sales['Gender'].map(gender_map)
sales['Gender_Clean'] = sales['Gender_Clean'].fillna('Not Specified')
```

**Result:** Standardized to "Male", "Female", "Not Specified"

---

### 4.3 Phone & Email
**Script Lines:** 253-264 (Preview only)

**Issues:**
- **Phone:** Nulls (18), mixed formats (+20, spaces, no prefix)
- **Email:** Nulls (22), invalid formats, no @, Arabic text

**Action in Current Script:** Preview and null count only

**RECOMMENDATION TO ADD:**

```python
# Phone Cleaning
def clean_phone(phone):
    if pd.isna(phone):
        return np.nan
    phone = str(phone).strip()
    # Remove all non-digits
    phone = re.sub(r'[^0-9]', '', phone)
    # Egyptian phone: 11 digits starting with 01
    if len(phone) == 11 and phone.startswith('01'):
        return f'+20{phone}'
    elif len(phone) == 10 and phone.startswith('1'):
        return f'+20{phone}'
    else:
        return np.nan  # Invalid format

sales['Phone_Clean'] = sales['Phone'].apply(clean_phone)

# Email Validation
def validate_email(email):
    if pd.isna(email):
        return np.nan
    email = str(email).strip().lower()
    # Basic regex for email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    else:
        return np.nan  # Invalid format

sales['Email_Clean'] = sales['Email'].apply(validate_email)
```

---

### 4.4 CustomerID
**Script Lines:** 268-278 (Commented out)

**Issue:** Mixed formats (CUS-001 vs C001), case variations, nulls

**Current Approach:** Commented out - needs business decision on standard format

**RECOMMENDATION:** Uncomment and standardize:
```python
sales['CustomerID_clean'] = sales['CustomerID'].astype(str).str.upper().str.replace('CUS-', 'C', regex=False)
```

---

## 5. GEOGRAPHIC DATA

### 5.1 Governorate Standardization
**Script Lines:** 303-407

**Problem:** 50+ variations for ~12 governorates
- Languages: Arabic, English
- Case: lowercase, UPPERCASE, Title Case
- Prefixes: "Al", "al"
- Spelling variations

**Solution:** Comprehensive mapping dictionary

**Example Mappings:**
```python
governorate_map = {
    'luxor': 'Luxor',
    'LUXOR': 'Luxor',
    'الأقصر': 'Luxor',
    'Al Luxor': 'Luxor',
    
    'red sea': 'Red Sea',
    'RED SEA': 'Red Sea',
    'البحر الأحمر': 'Red Sea',
    'Al Red Sea': 'Red Sea',
    
    # ... (complete map lines 312-396)
}

sales['Governorate_Clean'] = sales['Governorate'].map(governorate_map)
sales['Governorate_Clean'] = sales['Governorate_Clean'].fillna('Unknown')
```

**Result:** Standardized to 12-13 English governorate names

---

### 5.2 City
**Script Lines:** 417-418

**Action:** Preview only, kept as-is for coordinate imputation

**Why no cleaning?** City has high cardinality and is used for hierarchical imputation

---

### 5.3 Address
**Note:** Not cleaned in script

**Issue:** Unstructured free text - "88Apt 18Block 7", "عمارة7", "139 شارع Tahrir"

**Recommendation:** Requires structured form with separate fields:
- Building Number
- Street Name
- Apartment Number
- Floor
- Landmark

**OR:** Use NLP/Address parsing library

---

### 5.4 Latitude & Longitude - COMPREHENSIVE CLEANING
**Script Lines:** 547-709

This is one of the most complex cleaning procedures.

#### Step 1: Fix Decimal Separator & Convert to Numeric
**Lines:** 558-561

**Problem:** Comma used as decimal separator (European format)

```python
sales['Latitude_Clean'] = pd.to_numeric(
    sales['Latitude'].astype(str).str.replace(',', '.', regex=False), 
    errors='coerce'
)
sales['Longitude_Clean'] = pd.to_numeric(
    sales['Longitude'].astype(str).str.replace(',', '.', regex=False),
    errors='coerce'
)
```

**Result:** All coordinates as float, invalid → NaN

---

#### Step 2: Track Initially Missing Values
**Lines:** 580-584

```python
sales['coords_initially_missing'] = sales['Latitude_Clean'].isnull() | sales['Longitude_Clean'].isnull()
sales['investigation_flag'] = 'Valid/Unknown'
```

**Purpose:** Distinguish between "always missing" vs "became missing after validation"

---

#### Step 3: Global Bounds Check & Manual Swapping
**Lines:** 587-620

**Validation Rules:**
- Latitude must be in [-90, +90]
- Longitude must be in [-180, +180]

**Identify Swapped Coordinates:**
```python
global_invalid_mask = (Latitude.abs() > 90) | (Longitude.abs() > 180)
swapped_is_valid_mask = (Longitude.abs() <= 90) & (Latitude.abs() <= 180)
potential_swap_mask = global_invalid_mask & swapped_is_valid_mask
```

**Manual Swap (Index 95):**
```python
temp_lat = sales.loc[95, 'Latitude_Clean']
sales.loc[95, 'Latitude_Clean'] = sales.loc[95, 'Longitude_Clean']
sales.loc[95, 'Longitude_Clean'] = temp_lat
sales.loc[95, 'investigation_flag'] = 'Manually Swapped'
```

**Discard Remaining Invalid:**
```python
remaining_global_invalid = (Latitude.abs() > 90) | (Longitude.abs() > 180)
sales.loc[remaining_global_invalid, ['Latitude_Clean', 'Longitude_Clean']] = np.nan
sales.loc[remaining_global_invalid, 'investigation_flag'] = 'Globally_Invalid_Discarded'
```

---

#### Step 4: Egypt Geographical Bounds Check
**Lines:** 622-649

**Egypt Bounds:**
- Latitude: 22°N to 32°N
- Longitude: 25°E to 35°E

```python
egypt_lat_min, egypt_lat_max = 22, 32
egypt_long_min, egypt_long_max = 25, 35

invalid_egypt_mask = (
    (Latitude.notna()) & (Longitude.notna()) &
    ((Latitude < 22) | (Latitude > 32) | (Longitude < 25) | (Longitude > 35))
)

sales.loc[invalid_egypt_mask, ['Latitude_Clean', 'Longitude_Clean']] = np.nan
sales.loc[invalid_egypt_mask, 'investigation_flag'] = 'Out_of_Egypt_Scope'
```

**Purpose:** Remove coordinates outside Egypt (wrong country or data entry error)

---

#### Step 5: Hierarchical Imputation
**Lines:** 651-679

**Strategy:** Fill missing coordinates using location hierarchy (most specific → least specific)

**Priority 1: Address (most specific)**
```python
sales['Latitude_Clean'] = sales.groupby('Address')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('Address')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))
```

**Priority 2: City**
```python
sales['Latitude_Clean'] = sales.groupby('City')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('City')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))
```

**Priority 3: Governorate (least specific)**
```python
sales['Latitude_Clean'] = sales.groupby('Governorate')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('Governorate')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))
```

**Logic:** If same address has valid coordinates in other rows, use that average. If not, try city average, then governorate.

---

#### Step 6: Final Flagging
**Lines:** 682-698

```python
sales['coords_is_null'] = Latitude.isnull() | Longitude.isnull()

# Flag successful imputations
imputed_mask = (~coords_is_null) & (investigation_flag == 'Initially_Missing')
sales.loc[imputed_mask, 'investigation_flag'] = 'Imputed_by_Location'

# Flag remaining nulls
unknown_mask = coords_is_null & investigation_flag.isin(['Valid/Unknown', 'Initially_Missing'])
sales.loc[unknown_mask, 'investigation_flag'] = 'Needs_Further_Investigation/Unknown'

# Mark clean data as Valid
valid_mask = investigation_flag == 'Valid/Unknown'
sales.loc[valid_mask, 'investigation_flag'] = 'Valid'
```

**Final Flag Values:**
- `Valid`: Clean from the start
- `Manually Swapped`: Coordinates were swapped
- `Globally_Invalid_Discarded`: Outside global bounds
- `Out_of_Egypt_Scope`: Outside Egypt
- `Imputed_by_Location`: Filled using address/city/governorate
- `Needs_Further_Investigation/Unknown`: Still missing after all attempts

---

## 6. PRODUCT INFORMATION

### 6.1 Standardization Function
**Script Lines:** 716-736

**Purpose:** Unified text cleaning function for product fields

```python
def standardize_text(text):
    if pd.isna(text):
        return text
    
    text = str(text)
    
    if text.lower() in ('none', 'nan', ''):
        return np.nan
    
    text = text.strip().lower()
    
    return text
```

**Applied to:** ProductSKU, ProductName, Category

---

### 6.2 ProductSKU Cleaning
**Script Lines:** 739-749

**Issues:** Mixed case (ELEC-001 vs elec001), hyphens

**Solution:**
```python
sales['ProductSKU_Clean'] = sales['ProductSKU'].apply(standardize_text)
sales['ProductSKU_Clean'] = sales['ProductSKU_Clean'].str.replace('-', '', regex=False)
```

**Result:** All lowercase, no hyphens → "elec001"

---

### 6.3 ProductName Cleaning
**Script Lines:** 751-764

**Issues:** Arabic suffixes, typos, mixed case

**Step 1: Remove Arabic suffix pattern**
```python
sales['ProductName_Clean'] = sales['ProductName_Clean'].str.replace(r'\s+-\s*[ا-ي\s]+', '', regex=True)
```

**Step 2: Manual mappings for specific typos**
```python
sales['ProductName_Clean'] = sales['ProductName_Clean'].replace({
    'bluetooth سماعة': 'bluetooth headphones',
    'puzzle 1000pcsأحجية': 'puzzle 1000pcs',
    'organic زيت زيتون 1l': 'organic olive oil 1l',
    'labtop i7 16gb': 'laptop i7 16gb'  # Fix typo
})
```

---

### 6.4 Category Cleaning
**Script Lines:** 767-774

**Issue:** Spelling variations, Arabic/English

```python
sales['Category_Clean'] = sales['Category_Clean'].replace({
    'إلكترونيات': 'electronics',
    'electrnics': 'electronics'  # Fix typo
})
```

---

### 6.5 Clean Products Sheet (Source Table)
**Script Lines:** 784-824

**Critical Step:** Apply SAME cleaning to Products_Raw table

**Why?** To enable successful join for SKU imputation

```python
products['SKU'] = products['SKU'].apply(standardize_text)
products['SKU'] = products['SKU'].str.replace('-', '', regex=False)

products['ProductName'] = products['ProductName'].apply(standardize_text)
products['ProductName'] = products['ProductName'].str.replace(r'\s+-\s*[ا-ي\s]+', '', regex=True)
products['ProductName'] = products['ProductName'].replace({...})

products['Category'] = products['Category'].replace({...})

# Remove duplicates after standardization
products = products.drop_duplicates(subset=['ProductName'], keep='first')
```

---

### 6.6 SKU Imputation via Join
**Script Lines:** 826-863

**Problem:** 15 rows with missing ProductSKU

**Solution:** Use ProductName to lookup SKU from Products table

```python
# Left join sales with products on ProductName
sales = pd.merge(
    sales,
    products[['ProductName', 'SKU']],
    how='left',
    left_on='ProductName_Clean',
    right_on='ProductName',
    suffixes=('_sales', '_imputed')
)

# Fill missing SKUs
null_sku_mask = sales['ProductSKU_Clean'].isnull()
sales['ProductSKU_Clean'] = sales['ProductSKU_Clean'].fillna(sales['SKU'])

# Flag imputed rows
sales.loc[null_sku_mask & sales['ProductSKU_Clean'].notna(), 'investigation_flag'] = 'SKU_Imputed_by_Name'

# Cleanup temporary columns
sales.drop(columns=['SKU', 'ProductName_imputed'], inplace=True)
```

**Result:** Missing SKUs filled where matching ProductName exists in lookup

---

## 7. MONETARY COLUMNS

### 7.1 Currency Standardization
**Script Lines:** 870-899

**Problem:** Multiple formats: "EGP", "ج.م", "E£", "EGP 1500", "USD"

**Solution:**

**Step 1: Extract currency code**
```python
def clean_currency(currency_str):
    text = str(currency_str).upper()
    match = re.search(r'(EGP|USD|E£|ج\.م)', text)
    if match:
        code = match.group(0)
        return currency_map.get(code, code)
    return currency_str.upper()

currency_map = {'ج.م': 'EGP', 'E£': 'EGP', 'EGP': 'EGP', 'USD': 'USD'}
sales['Currency_Clean'] = sales['Currency'].apply(clean_currency)
```

---

### 7.2 Foreign Exchange Conversion
**Script Lines:** 901-920

**Approach:** Convert all amounts to EGP for consistency

**FX Rate:**
```python
EGP_PER_USD = 45.3575  # Average 2024 rate

def get_fx_rate(currency):
    if currency == 'USD':
        return EGP_PER_USD
    return 1.0

sales['FX_Rate'] = sales['Currency_Clean'].apply(get_fx_rate)
sales['UnitPrice_EGP'] = sales['UnitPrice'] * sales['FX_Rate']
```

**Business Value:** Enables accurate revenue aggregation

---

### 7.3 Quantity Cleaning
**Script Lines:** 922-928

**Problem:** Negative or zero quantities (8 records)

```python
invalid_qty_mask = sales['Quantity'] <= 0
sales['Quantity_Clean'] = sales['Quantity']
sales.loc[invalid_qty_mask, 'Quantity_Clean'] = np.nan
```

**Why NaN not 1?** Preserve data integrity; don't guess values

---

### 7.4 Subtotal Recalculation
**Script Lines:** 930-934

**Problem:** 30% of Subtotal values don't match UnitPrice × Quantity

**Solution:** Recalculate from scratch

```python
sales['Subtotal_Calc'] = sales['UnitPrice_EGP'] * sales['Quantity_Clean']
```

**Note:** Use cleaned values (EGP-converted price, valid quantity)

---

### 7.5 Discount Standardization
**Script Lines:** 936-973

**Problem:** 3 different formats:
- Percentage: "10%", "5%"
- Decimal rate: 0.1, 0.05
- Fixed amount: 50, 100 (in original currency)

**Solution:** Convert ALL to decimal rate (0.0 to 1.0)

```python
def standardize_discount(row):
    discount = str(row['Discount']).strip()
    subtotal = row['Subtotal_Calc']
    
    # Handle missing
    if pd.isna(discount) or discount.upper() in ('NONE', 'NAN', '0'):
        return 0.0
    
    # Percentage format
    if '%' in discount:
        try:
            return float(discount.replace('%', '')) / 100
        except:
            return 0.0
    
    # Numeric
    try:
        val = float(discount)
    except:
        return 0.0
    
    # Already a rate (< 1.0)
    if val < 1.0:
        return val
    
    # Fixed amount → convert to rate
    if pd.isna(subtotal) or subtotal == 0:
        return 0.0
    discount_egp = val * row['FX_Rate']  # Convert to EGP if needed
    rate = discount_egp / subtotal
    return min(rate, 1.0)  # Cap at 100%

sales['Discount_Rate_Clean'] = sales.apply(standardize_discount, axis=1)
```

**Result:** All discounts as 0.0-1.0 rate

---

### 7.6 Outlier Capping (UnitPrice)
**Script Lines:** 975-991

**Problem:** Extreme outliers (e.g., millions EGP for 2 t-shirts)

**Solution:** Cap at 99th percentile PER SKU

**Why per SKU?** Different products have different price ranges

```python
# Calculate 99th percentile for each SKU
sku_99 = sales.groupby('ProductSKU_Clean')['UnitPrice_EGP'].quantile(0.99)

def cap_unitprice(row):
    threshold = sku_99[row['ProductSKU_Clean']]
    return min(row['UnitPrice_EGP'], threshold)

sales['UnitPrice_EGP_capped'] = sales.apply(cap_unitprice, axis=1)

# Recalculate subtotal with capped price
sales['Subtotal_Calc_Capped'] = sales['UnitPrice_EGP_capped'] * sales['Quantity_Clean']
```

**Alternative Considered:** Delete outliers → Rejected (lose data)

---

## 8. TRANSACTIONAL COLUMNS

### 8.1 PaymentStatus
**Script Lines:** 424-435

**Issue:** Arabic/English mixing

```python
sales['PaymentStatus_Clean'] = sales['PaymentStatus'].replace({
    'غير مدفوع': 'Unpaid',
    'مدفوع': 'Paid',
})
```

---

### 8.2 PaymentMethod
**Script Lines:** 440-452

**Issue:** Abbreviations and Arabic

```python
sales['PaymentMethod_Clean'] = sales['PaymentMethod'].replace({
    'COD': 'Cash on Delivery',
    'Cash': 'Cash on Delivery',
    'فوري': 'Fawry',
})
```

---

### 8.3 Status
**Script Lines:** 459-513

**Issue:** Nulls (13) and Arabic mixing

```python
sales['Status_Clean'] = sales['Status'].replace({
    'ملغي': 'Cancelled',
})
sales['Status_Clean'] = sales['Status_Clean'].fillna('Unknown')
```

**Investigation (Lines 477-513):** Analyzed missing Status patterns

**Finding:** Missing Status strongly correlated with:
- Channel: WhatsApp (7) and Tel-Sales (5)
- PaymentStatus: Unpaid (7) or Pending (5)

**Conclusion:** Status not updated until payment confirmed

---

### 8.4 ShipperName
**Script Lines:** 516-528

```python
sales['ShipperName_Clean'] = sales['ShipperName'].replace({
    'بريد مصر': 'Egypt Post',
})
```

---

### 8.5 Channel
**Script Lines:** 533-544

```python
sales['Channel_Clean'] = sales['Channel'].replace({
    'تجارة إلكترونية': 'E-com',
})
```

---

### 8.6 ShippingCost Imputation
**Script Lines:** 1052-1154

**Problem:** Nulls (28), zeros, inconsistent

**Approach:** Hierarchical imputation by location and shipper

**Step 1: Calculate medians at multiple levels**
```python
median_level1 = sales.groupby(['ShipperName_Clean', 'Governorate_Clean', 'City'])['ShippingCost'].median()
median_level2 = sales.groupby(['ShipperName_Clean', 'City'])['ShippingCost'].median()
median_level3 = sales.groupby(['ShipperName_Clean', 'Governorate_Clean'])['ShippingCost'].median()
median_level4 = sales.groupby(['ShipperName_Clean'])['ShippingCost'].median()
global_median = sales['ShippingCost'].median()
```

**Step 2: Apply hierarchical fill**
```python
def fill_shipping_cost(row):
    # If value exists and not 0, keep it
    if pd.notna(row['ShippingCost']) and row['ShippingCost'] != 0:
        return row['ShippingCost']
    
    # Try level 1 (most specific): Shipper + Governorate + City
    # Then level 2: Shipper + City
    # Then level 3: Shipper + Governorate
    # Then level 4: Shipper only
    # Finally: Global median
    ...
    return global_median

sales['ShippingCost_Filled'] = sales.apply(fill_shipping_cost, axis=1)
```

**Business Logic:** Shipping cost depends on shipper and destination

---

### 8.7 TotalAmount Recalculation
**Script Lines:** 1165-1171

**Formula:**
```python
sales['TotalAmount_Calc'] = (
    sales['Subtotal_Calc_Capped'] * (1 - sales['Discount_Rate_Clean'])
) + sales['ShippingCost_Filled']
```

**Breakdown:**
1. Start with capped subtotal
2. Apply discount as rate: Subtotal × (1 - Rate)
3. Add shipping cost

**Result:** Consistent, verifiable total amounts

---

### 8.8 Extreme Value Detection
**Script Lines:** 1173-1219

**Method:** IQR (Interquartile Range) method

```python
Q1 = sales['TotalAmount_Calc'].quantile(0.25)
Q3 = sales['TotalAmount_Calc'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

sales['TotalAmount_Extreme'] = (TotalAmount < lower_bound) | (TotalAmount > upper_bound)
```

**Purpose:** Flag for investigation, not removal

---

## 9. BI-READY DATASET CREATION

### 9.1 Select BI Columns
**Script Lines:** 1223-1241

**Selected Columns:**
```python
bi_columns = [
    'OrderID_cleaned',
    'OrderDate', 'Order_Year', 'Order_Month', 'Order_Quarter', 'Order_YearMonth',
    'DeliveryDate', 'Delivery_Time_Days', 'Delivery_Delayed',
    'ProductSKU_Clean', 'ProductName_Clean', 'Category_Clean',
    'Subtotal_Calc_Capped', 'Discount_Rate_Clean', 'ShippingCost_Filled', 'TotalAmount_Calc',
    'PaymentStatus_Clean', 'PaymentMethod_Clean'
]

bi_sales = sales[bi_columns]
```

**Criteria:** Only clean, calculated columns; ready for dashboard

---

### 9.2 Export to Excel
**Script Lines:** 1243-1245

```python
output_path = "/path/to/BI_Ready_Sales_Dataset.xlsx"
bi_sales.to_excel(output_path, index=False)
```

---

## APPENDIX A: MISSING CLEANING PROCEDURES

The following columns were **not fully cleaned** in the current script and should be added:

### A.1 Phone Number Standardization

**Add after line 264:**

```python
def clean_phone(phone):
    if pd.isna(phone):
        return np.nan
    phone = str(phone).strip()
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Egyptian format: +20 followed by 10 digits starting with 1
    if len(phone) == 11 and phone.startswith('01'):
        return f'+20{phone}'
    elif len(phone) == 10 and phone.startswith('1'):
        return f'+20{phone}'
    else:
        return np.nan

sales['Phone_Clean'] = sales['Phone'].apply(clean_phone)
sales['phone_is_valid'] = sales['Phone_Clean'].notna()
```

### A.2 Email Validation

**Add after Phone cleaning:**

```python
def validate_email(email):
    if pd.isna(email):
        return np.nan
    email = str(email).strip().lower()
    # Remove Arabic characters
    if bool(re.search(r'[\u0600-\u06FF]', email)):
        return np.nan
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return np.nan

sales['Email_Clean'] = sales['Email'].apply(validate_email)
sales['email_is_valid'] = sales['Email_Clean'].notna()
```

### A.3 CustomerID Standardization

**Uncomment and modify lines 272-278:**

```python
def clean_customer_id(cust_id):
    if pd.isna(cust_id):
        return np.nan
    cust_id = str(cust_id).upper().strip()
    # Standardize format: remove "CUS-" prefix, keep just C prefix
    cust_id = cust_id.replace('CUS-', 'C')
    return cust_id

sales['CustomerID_clean'] = sales['CustomerID'].apply(clean_customer_id)
```

### A.4 Notes & SalesRep

**These are free-text fields** - minimal cleaning recommended:

```python
# Basic cleaning only
sales['Notes_Clean'] = sales['Notes'].astype(str).str.strip()
sales['SalesRep_Clean'] = sales['SalesRep'].astype(str).str.strip().str.title()
```

---

## APPENDIX B: VALIDATION CHECKS

**Add at end of script:**

```python
# ============================================
# VALIDATION SUMMARY
# ============================================

print("\n========== DATA QUALITY VALIDATION ==========")

# 1. Uniqueness Check
print(f"\n1. OrderID Uniqueness:")
print(f"   Unique OrderID_cleaned: {sales['OrderID_cleaned'].nunique()}")
print(f"   Total rows: {len(sales)}")
print(f"   100% unique: {sales['OrderID_cleaned'].nunique() == len(sales)}")

# 2. Completeness Check
print(f"\n2. Critical Fields Completeness:")
print(f"   OrderDate nulls: {sales['OrderDate'].isnull().sum()}")
print(f"   ProductSKU_Clean nulls: {sales['ProductSKU_Clean'].isnull().sum()}")
print(f"   TotalAmount_Calc nulls: {sales['TotalAmount_Calc'].isnull().sum()}")

# 3. Accuracy Check
print(f"\n3. Calculation Accuracy:")
subtotal_test = (sales['UnitPrice_EGP_capped'] * sales['Quantity_Clean'] - sales['Subtotal_Calc_Capped']).abs().sum()
print(f"   Subtotal calculation diff: {subtotal_test} (should be ~0)")

# 4. Validity Check
print(f"\n4. Business Rules:")
print(f"   Negative quantities: {(sales['Quantity_Clean'] < 0).sum()}")
print(f"   Delivery before order: {sales['delivery_is_before_order'].sum()}")
print(f"   Discount rate > 1: {(sales['Discount_Rate_Clean'] > 1).sum()}")

# 5. Consistency Check
print(f"\n5. Standardization:")
print(f"   Governorate variations: {sales['Governorate_Clean'].nunique()}")
print(f"   Currency values: {sales['Currency_Clean'].unique()}")
print(f"   Gender values: {sales['Gender_Clean'].unique()}")

print("\n==============================================\n")
```

---

## SUMMARY OF CLEANING ACTIONS

| Column | Action Taken | Flag/New Column Created |
|--------|-------------|-------------------------|
| OrderID | Created unique IDs for duplicates | `OrderID_cleaned`, `is_OrderID_duplicated_flag` |
| OrderDate | Parsed mixed formats | `Order_Year`, `Order_Month`, `Order_Quarter`, `Order_YearMonth`, `orderdate_is_null` |
| DeliveryDate | Parsed, validated logic | `Delivery_Year/Month/Quarter`, `Delivery_Time_Days`, `Delivery_Delayed`, `Valid_Delivery` |
| ReturnDate | Parsed, validated | `Return_Year/Month/Quarter`, `Return_Time_Days`, `Valid_Return` |
| ReturnFlag | Mapped 7 variations to Yes/No | `ReturnFlag_Clean` |
| CustomerName | Lowercased, trimmed | `CustomerName_clean` |
| Gender | Mapped 6 variations | `Gender_Clean` |
| Phone | (TO ADD) Format validation | `Phone_Clean`, `phone_is_valid` |
| Email | (TO ADD) Regex validation | `Email_Clean`, `email_is_valid` |
| CustomerID | (TO ADD) Standardize format | `CustomerID_clean` |
| Governorate | Mapped 50+ variations | `Governorate_Clean` |
| City | Kept for imputation | - |
| Address | Kept as-is (needs NLP) | - |
| Latitude/Longitude | Decimal fix, bounds check, swap, imputation | `Latitude_Clean`, `Longitude_Clean`, `investigation_flag`, `coords_is_null` |
| ProductSKU | Lowercased, removed hyphens, imputed | `ProductSKU_Clean` |
| ProductName | Standardized, removed Arabic, fixed typos | `ProductName_Clean` |
| Category | Mapped variations | `Category_Clean` |
| UnitPrice | Converted to EGP, capped outliers | `UnitPrice_EGP`, `UnitPrice_EGP_capped`, `FX_Rate` |
| Quantity | Set invalid to NaN | `Quantity_Clean` |
| Subtotal | Recalculated | `Subtotal_Calc`, `Subtotal_Calc_Capped` |
| Discount | Unified to rate format | `Discount_Rate_Clean` |
| ShippingCost | Hierarchical imputation | `ShippingCost_Filled` |
| TotalAmount | Recalculated | `TotalAmount_Calc`, `TotalAmount_Extreme` |
| Currency | Extracted code | `Currency_Clean` |
| PaymentStatus | Mapped Arabic | `PaymentStatus_Clean` |
| PaymentMethod | Standardized | `PaymentMethod_Clean` |
| ShipperName | Mapped Arabic | `ShipperName_Clean` |
| Channel | Mapped Arabic | `Channel_Clean` |
| Status | Mapped, filled nulls | `Status_Clean` |
| Notes | (TO ADD) Basic cleaning | `Notes_Clean` |
| SalesRep | (TO ADD) Title case | `SalesRep_Clean` |

---

**END OF GUIDE**

