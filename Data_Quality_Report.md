# DATA QUALITY REPORT
## EG Retail Sales - Case Study 1

**Date:** November 18, 2024  
**Analyst:** Salma Abdelkader  
**Dataset:** EG_Retail_Sales_Raw_CaseStudy 1.xlsx  
**Total Records Analyzed:** 150 orders

---

## EXECUTIVE SUMMARY

This report documents the comprehensive data quality assessment of the EG Retail Sales dataset across four sheets (Sales_Orders_Raw, Products_Raw, Governorates_Lookup_Noise, Customers_Raw). The analysis revealed **significant data quality issues** across all DAMA dimensions, requiring extensive cleaning and standardization.

**Key Findings:**
- **0% complete duplicate rows**, but **multiple OrderIDs with conflicting data**
- **Mixed language data** (Arabic/English) in 15+ columns
- **Date inconsistencies** affecting 40%+ of records
- **Calculation errors** in monetary fields (Subtotal, TotalAmount)
- **Geographic data issues** in coordinates and governorate names
- **No data validation** at entry point across all channels

---

## 1. DATA QUALITY ISSUES BY DAMA DIMENSION

### 1.1 COMPLETENESS (Missing Values)

| Column | Nulls Count | % Missing | Impact Level |
|--------|-------------|-----------|--------------|
| ReturnDate | 120 | 80% | Medium (expected for non-returned items) |
| DeliveryDate | 25 | 16.7% | High (cannot calculate delivery time) |
| OrderDate | 12 | 8% | Critical (breaks time-series analysis) |
| Phone | 18 | 12% | High (cannot contact customers) |
| Email | 22 | 14.7% | High (cannot send notifications) |
| Latitude/Longitude | 35 | 23.3% | Medium (limits geo-analysis) |
| ProductSKU | 15 | 10% | High (cannot track inventory) |
| ShippingCost | 28 | 18.7% | Medium (affects revenue calculations) |
| CustomerID | 8 | 5.3% | High (cannot link customer history) |
| Status | 13 | 8.7% | Medium (cannot track order lifecycle) |
| Address | 0 | 0% | - (but quality issues exist) |

**Root Causes:**
- No mandatory field validation at data entry
- Different data collection processes across channels (WhatsApp, Tel-Sales have higher missing rates)
- Status field missing primarily for "Unpaid" or "Pending" payment statuses

---

### 1.2 ACCURACY (Correctness of Values)

#### 1.2.1 Date Logic Violations

| Issue | Count | % of Total |
|-------|-------|------------|
| Delivery Date BEFORE Order Date | 12 | 8% |
| Return Date BEFORE Order Date | 5 | 3.3% |
| Return Date BEFORE Delivery Date | 8 | 5.3% |

**Examples:**
- Order ORD-001: OrderDate = 2024-05-15, DeliveryDate = 2024-05-10 (impossible)

#### 1.2.2 Calculation Mismatches

| Issue | Count | % of Total |
|-------|-------|------------|
| Subtotal ≠ UnitPrice × Quantity | 45 | 30% |
| TotalAmount miscalculated | 38 | 25.3% |
| Negative or Zero Quantity | 8 | 5.3% |
| Unit Price outliers (>99th percentile) | 12 | 8% |

**Examples:**
- Order with 2 t-shirts showing total amount in millions EGP
- Quantity = -1 or 0 (logically impossible)

#### 1.2.3 Geographic Data Errors

| Issue | Count | % of Total |
|-------|-------|------------|
| Coordinates outside global bounds (±90/±180) | 1 | 0.7% |
| Coordinates outside Egypt bounds (22-32N, 25-35E) | 15 | 10% |
| Swapped Latitude/Longitude | 1 | 0.7% |
| Decimal separator errors (comma instead of period) | 45 | 30% |

**Root Causes:**
- Manual coordinate entry without validation
- Copy-paste errors leading to swapped values
- Regional number formats (comma as decimal separator)

---

### 1.3 CONSISTENCY (Standardization Issues)

#### 1.3.1 Language Mixing (Arabic/English)

| Column | Variations | Example Values |
|--------|------------|----------------|
| Governorate | 50+ | "Cairo", "القاهرة", "Al Cairo", "القاهره" |
| Gender | 6 | "M", "F", "ذكر", "أنثى", "Male", "Female" |
| ReturnFlag | 7 | "Yes", "No", "Y", "N", "نعم", "لا", "1", "0" |
| PaymentStatus | 4 | "Paid", "Unpaid", "مدفوع", "غير مدفوع" |
| PaymentMethod | 5 | "Cash", "COD", "Cash on Delivery", "فوري" |
| Status | 4 | "Delivered", "Cancelled", "ملغي", "Pending" |
| ShipperName | 6 | "Egypt Post", "بريد مصر", "Aramex", etc. |
| Channel | 5 | "E-com", "تجارة إلكترونية", "Store", "WhatsApp" |
| Category | 8 | "Electronics", "إلكترونيات", "Electrnics", "electronics" |

#### 1.3.2 Format Inconsistencies

| Column | Issue | Examples |
|--------|-------|----------|
| OrderDate | Mixed formats | "2024-01-15", "15/01/2024", "01-15-24", "15 يناير 2024" |
| Phone | No standard format | "+201234567890", "0123 456 7890", "01234567890" |
| Email | Multiple issues | Missing "@", Arabic text, no domain, "test@" |
| ProductSKU | Case & hyphen variations | "ELEC-001", "elec001", "ELEC001", "elec-001" |
| ProductName | Mixed case & language | "Laptop i7 16GB", "labtop i7 16gb", with Arabic suffixes |
| Currency | Multiple formats | "EGP", "E£", "ج.م", "EGP 1500", "1500 EGP", "USD" |
| Discount | 3 different formats | "10%" (percent), "0.1" (rate), "50" (amount) |
| CustomerName | Mixed case | "Ahmed Ali", "ahmed ali", "AHMED ALI" |
| CustomerID | Format variations | "CUS-001", "C001", "cus001", different casing |
| Address | Unstructured text | "88Apt 18Block 7", "عمارة7", "139 شارع Tahrir" (no standard structure) |

**Root Causes:**
- Bilingual team without data entry standards
- No dropdown lists or controlled vocabularies
- Multiple data entry systems without integration
- No data normalization at database level

---

### 1.4 VALIDITY (Business Rule Violations)

| Rule Violation | Count | % of Total |
|----------------|-------|------------|
| Channel=Store WITH ShippingCost/ShipperName | 15 | 10% |
| ReturnFlag=No WITH ReturnDate populated | 8 | 5.3% |
| PaymentStatus=Unpaid WITH Status=Delivered | 12 | 8% |
| Discount > Subtotal (over 100%) | 3 | 2% |
| Quantity = 0 or negative | 8 | 5.3% |
| ShippingCost = 0 for non-Store channels | 18 | 12% |

**Examples:**
- Order shows Channel="Store" but has ShipperName="Aramex" and ShippingCost=50 EGP
- Order marked as "Delivered" but PaymentStatus="Unpaid"

**Root Causes:**
- No business logic validation rules
- Cross-field dependencies not enforced
- Manual data entry errors

---

### 1.5 UNIQUENESS (Duplicate & ID Issues)

#### 1.5.1 OrderID Duplicates - CRITICAL ISSUE

| Finding | Details |
|---------|---------|
| Rows with duplicate OrderIDs | 45 (30% of dataset) |
| Unique duplicate patterns | Same OrderID with COMPLETELY different data |
| Attributes affected | CustomerID, ProductSKU, TotalAmount, ALL fields different |

**Analysis:**
- This is NOT standard "duplicate rows" (same data entered twice)
- This appears to be **OrderID reuse** or **ID generation failure**
- Same OrderID shows different customers, products, amounts, dates
- **No reliable anchor column** to determine which record is correct

**Examples:**
- OrderID "ORD-100" appears 3 times with 3 different CustomerIDs and products
- No pattern to suggest which is the "correct" record

#### 1.5.2 Product Duplicates

| Finding | Count |
|---------|-------|
| Duplicate rows in Products_Raw | 25 |
| Caused by variations in same product | 100% |

**Examples:**
- "Laptop i7 16GB" vs "labtop i7 16gb" vs "Laptop i7 16GB - لابتوب"
- All same product, but spelling/language variations prevent proper grouping

---

### 1.6 INTEGRITY (Referential & Cross-Table Issues)

| Issue | Count | Impact |
|-------|-------|--------|
| ProductSKU in Sales not in Products table | 8 | Medium |
| CustomerID format mismatches | 15 | High |
| Governorate spelling preventing joins | 30+ | Medium |

**Root Causes:**
- No foreign key constraints
- No master data management (MDM)
- Data entered without lookup validation

---

## 2. DATA QUALITY SCORES BY COLUMN

| Column | Completeness | Accuracy | Consistency | Validity | Overall Score |
|--------|--------------|----------|-------------|----------|---------------|
| OrderID | 100% | 30%* | 95% | 70% | **49%** |
| OrderDate | 92% | 92% | 60% | 92% | **84%** |
| DeliveryDate | 83% | 75% | 60% | 83% | **75%** |
| ReturnDate | 20% | 85% | 60% | 20% | **46%** |
| CustomerName | 100% | 95% | 70% | 100% | **91%** |
| Gender | 95% | 100% | 50% | 95% | **85%** |
| Phone | 88% | 70% | 40% | 88% | **72%** |
| Email | 85% | 60% | 50% | 85% | **70%** |
| Governorate | 100% | 90% | 30% | 100% | **80%** |
| Latitude/Longitude | 77% | 70% | 60% | 77% | **71%** |
| ProductSKU | 90% | 95% | 50% | 90% | **81%** |
| ProductName | 100% | 95% | 60% | 100% | **89%** |
| Category | 100% | 90% | 50% | 100% | **85%** |
| UnitPrice | 100% | 75% | 70% | 92% | **84%** |
| Quantity | 100% | 95% | 100% | 95% | **98%** |
| Subtotal | 97% | 70% | 90% | 85% | **86%** |
| TotalAmount | 98% | 75% | 85% | 90% | **87%** |
| Currency | 100% | 95% | 50% | 100% | **86%** |
| ShippingCost | 81% | 85% | 95% | 82% | **86%** |
| PaymentStatus | 100% | 100% | 60% | 90% | **88%** |

*OrderID accuracy score is low due to duplication with conflicting data

---

## 3. CHANNEL-SPECIFIC DATA QUALITY ANALYSIS

| Channel | Record Count | Avg DQ Score | Main Issues |
|---------|--------------|--------------|-------------|
| E-com | 45 | 85% | Better overall quality, fewer nulls |
| Store | 38 | 78% | Shipping fields incorrectly populated |
| WhatsApp | 35 | 68% | High missing rates (Status, Phone, Email) |
| Tel-Sales | 32 | 70% | Similar to WhatsApp, missing Status fields |

**Insight:** E-commerce channel has significantly better data quality, suggesting automated validation. Manual channels (WhatsApp, Tel-Sales) show poor quality.

---

## 4. IMPACT ASSESSMENT

### 4.1 Business Impact

| Analysis Type | Impact Level | Reason |
|---------------|--------------|--------|
| Revenue Reporting | **HIGH** | Calculation errors, missing totals, currency mixing |
| Customer Analytics | **CRITICAL** | Duplicate OrderIDs prevent accurate customer journey tracking |
| Inventory Management | **HIGH** | Missing/inconsistent ProductSKU prevents stock tracking |
| Delivery Performance | **HIGH** | Date errors and missing DeliveryDate prevent SLA tracking |
| Geographic Analysis | **MEDIUM** | Coordinate issues limit 23% of records from mapping |
| Payment Risk Analysis | **MEDIUM** | Missing Status makes it hard to track unpaid orders |

### 4.2 Recommended Actions Priority

**CRITICAL (Fix Immediately):**
1. OrderID duplication issue - requires business investigation
2. Date format standardization and validation
3. Calculation formulas (Subtotal, TotalAmount) enforcement
4. Mandatory field validation for core fields

**HIGH (Fix in Sprint 1):**
1. Governorate/Category/Product standardization via lookup tables
2. Phone/Email format validation
3. Currency standardization
4. Cross-field business rule validation

**MEDIUM (Fix in Sprint 2):**
1. Coordinate validation and imputation
2. Address structuring
3. Notes/SalesRep standardization

---

## 5. ROOT CAUSE ANALYSIS

### Primary Root Causes

1. **No Data Entry Validation**
   - Text fields accept any input without constraints
   - No dropdown lists for categorical fields
   - No format validation for phone/email/dates

2. **Multiple Disconnected Systems**
   - E-com, Store, WhatsApp, Tel-Sales use different entry methods
   - No centralized data capture
   - No integration layer for normalization

3. **Bilingual Operations Without Standards**
   - Team members enter data in Arabic or English randomly
   - No standardized language policy
   - No translation/mapping tables

4. **Manual Data Entry**
   - Heavy reliance on manual typing (not selection)
   - No auto-calculation for derived fields
   - Human error in coordinate/calculation entry

5. **No Master Data Management (MDM)**
   - No product catalog enforcement
   - No customer master data
   - No geographic reference data

6. **Lack of Business Logic Enforcement**
   - No validation rules for cross-field dependencies
   - Store orders can have shipping costs
   - Delivered orders can be unpaid

---

## 6. RECOMMENDATIONS

### 6.1 Immediate Technical Controls (see Part A document)

### 6.2 Process Improvements

1. **Implement MDM for Products, Customers, Locations**
2. **Centralize data entry through single validated system**
3. **Add data quality monitoring dashboard**
4. **Establish data stewardship roles**
5. **Regular data quality audits (monthly)**
6. **Train data entry staff on standards**

### 6.3 Long-term Strategic

1. **Implement Data Governance Framework**
2. **Establish Data Quality KPIs**
3. **Build automated data quality checks in ETL pipeline**
4. **Integrate all channels into unified system**
5. **Implement real-time validation at point of entry**

---

## APPENDIX A: Column-by-Column Issue Summary

### Sales_Orders_Raw Sheet

**OrderID**
- Issue: Duplicates with conflicting data (45 records)
- Action: Created OrderID_cleaned with unique IDs + flag

**OrderDate**
- Issue: Mixed formats, nulls (12), dates in future
- Action: Parsed all formats to datetime, flagged nulls

**DeliveryDate**
- Issue: Mixed formats, nulls (25), some before OrderDate (12)
- Action: Parsed, validated logic, created validity flags

**ReturnDate**
- Issue: Nulls (120), some before order/delivery
- Action: Parsed, validated, flagged impossible dates

**ReturnFlag**
- Issue: 7 variations (Yes/No/Y/N/نعم/لا/1/0)
- Action: Mapped to standardized "Yes"/"No"

**CustomerName**
- Issue: Mixed case, Arabic/English
- Action: Lowercased and trimmed

**CustomerID**
- Issue: Nulls (8), mixed formats (CUS-001 vs C001)
- Action: Flagged nulls, needs business rule for standardization

**Gender**
- Issue: 6 variations (M/F/ذكر/أنثى/Male/Female), nulls
- Action: Mapped to "Male"/"Female"/"Not Specified"

**Phone**
- Issue: Nulls (18), multiple formats, spaces, missing +20
- Action: Flagged nulls, needs regex validation

**Email**
- Issue: Nulls (22), invalid formats, Arabic text, no @
- Action: Flagged nulls, needs regex validation

**Governorate**
- Issue: 50+ variations for 12 governorates
- Action: Created mapping dictionary (Arabic/English/typos → Standard)

**City**
- Issue: Similar to Governorate but higher variability
- Action: Preserved as-is, used for coordinate imputation

**Address**
- Issue: Unstructured free text, mixed language, no standard fields
- Action: Kept as-is (requires NLP or structured form)

**Latitude/Longitude**
- Issue: Nulls (35), comma decimals, out of bounds, swapped
- Action: Fixed decimals, validated bounds, swapped manually, imputed by Address→City→Governorate

**ProductSKU**
- Issue: Nulls (15), mixed case, hyphen variations
- Action: Lowercased, removed hyphens, imputed from ProductName

**ProductName**
- Issue: Mixed case, Arabic suffixes, typos
- Action: Lowercased, removed Arabic patterns, manual mappings

**Category**
- Issue: Spelling variations, Arabic/English
- Action: Mapped to standard English names

**UnitPrice**
- Issue: Currency mixing, extreme outliers
- Action: Converted all to EGP, capped at 99th percentile per SKU

**Quantity**
- Issue: Zeros and negatives (8)
- Action: Set invalid to NaN

**Subtotal**
- Issue: Nulls, doesn't match UnitPrice × Quantity (45)
- Action: Recalculated = UnitPrice_EGP_capped × Quantity_Clean

**Discount**
- Issue: 3 formats (%, rate, amount), nulls
- Action: Standardized all to decimal rate (0-1)

**ShippingCost**
- Issue: Nulls (28), zeros, present for Store channel
- Action: Imputed by Shipper→Governorate→City→Global median

**TotalAmount**
- Issue: Negatives, miscalculated (38)
- Action: Recalculated = (Subtotal - Discount) + ShippingCost

**Currency**
- Issue: Multiple formats (EGP/E£/ج.م/USD with amounts)
- Action: Extracted currency code, applied FX rates

**PaymentMethod**
- Issue: Arabic/English mixing, abbreviations
- Action: Mapped to standard English terms

**PaymentStatus**
- Issue: Arabic/English mixing
- Action: Mapped "مدفوع"→"Paid", "غير مدفوع"→"Unpaid"

**ShipperName**
- Issue: Arabic/English mixing
- Action: Mapped "بريد مصر"→"Egypt Post"

**Channel**
- Issue: Arabic/English mixing
- Action: Mapped "تجارة إلكترونية"→"E-com"

**Status**
- Issue: Nulls (13), Arabic/English mixing
- Action: Mapped "ملغي"→"Cancelled", nulls→"Unknown"

**Notes**
- Issue: Mixed language, unstructured
- Action: No cleaning performed (free text)

**SalesRep**
- Issue: Mixed language, case variations
- Action: No cleaning performed

---

## APPENDIX B: Products_Raw Sheet Issues

**Duplicate Records**
- Issue: 25 duplicate rows due to spelling/language variations
- Action: Standardized SKU/Name/Category, then dropped duplicates

**Same issues as Sales sheet for:**
- ProductSKU: Case, hyphens
- ProductName: Language, case, typos
- Category: Spelling, language

---

**END OF REPORT**

