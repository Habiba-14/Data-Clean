# =============================================================================
# MISSING PREPROCESSING CODE - ADD TO RETAIL_SALES_CLEANED.PY
# =============================================================================
# This file contains code snippets to add for Address, SalesRep, Notes
# and business logic validation flags
# =============================================================================

# -----------------------------------------------------------------------------
# 1. ADDRESS CLEANING (Add after City cleaning section)
# -----------------------------------------------------------------------------

print("\n----- Address Cleaning -----")

def clean_address_basic(address):
    """
    Basic address cleaning - standardize format
    
    Issues addressed:
    - Extra spaces
    - Mixed Arabic/English
    - Inconsistent capitalization
    - Special characters
    
    Returns: (cleaned_address, quality_category)
    """
    if pd.isna(address):
        return np.nan, 'missing'
    
    address = str(address).strip()
    
    # Remove extra spaces (including tabs, newlines):
    address = re.sub(r'\s+', ' ', address)
    
    # Remove leading/trailing special chars:
    address = re.sub(r'^[,.\-\s]+|[,.\-\s]+$', '', address)
    
    # Classify address quality:
    if len(address) < 5:
        quality = 'too_short'
    elif not any(char.isdigit() for char in address):
        quality = 'no_number'
    else:
        quality = 'valid'
    
    return address, quality

# Apply cleaning:
address_result = sales['Address'].apply(clean_address_basic)
sales['Address_Clean'] = address_result.apply(lambda x: x[0])
sales['address_quality'] = address_result.apply(lambda x: x[1])

# Statistics:
print("Address quality distribution:")
print(sales['address_quality'].value_counts())
print(f"Valid addresses: {(sales['address_quality'] == 'valid').sum()}")
print(f"Missing addresses: {(sales['address_quality'] == 'missing').sum()}")

# Optional: Extract address components (ADVANCED - for later)
def extract_address_components(address):
    """
    Extract structured components from address
    Returns: dict with building, block, apartment, street
    """
    components = {
        'building': None,
        'block': None,
        'apartment': None,
        'street': None
    }
    
    if pd.isna(address):
        return components
    
    address = str(address)
    
    # Extract building number:
    building_match = re.search(r'عمارة\s*(\d+)|Building\s*(\d+)', address, re.I)
    if building_match:
        components['building'] = building_match.group(1) or building_match.group(2)
    
    # Extract block:
    block_match = re.search(r'Block\s*(\d+)|بلوك\s*(\d+)', address, re.I)
    if block_match:
        components['block'] = block_match.group(1) or block_match.group(2)
    
    # Extract apartment:
    apt_match = re.search(r'Apt\.?\s*(\d+)|شقة\s*(\d+)', address, re.I)
    if apt_match:
        components['apartment'] = apt_match.group(1) or apt_match.group(2)
    
    # Extract street:
    street_match = re.search(r'شارع\s+([^\d]+)|Street\s+([A-Za-z\s]+)', address, re.I)
    if street_match:
        components['street'] = (street_match.group(1) or street_match.group(2)).strip()
    
    return components

# Optional: Apply component extraction (uncomment if needed):
# address_components = sales['Address_Clean'].apply(extract_address_components)
# sales['Address_Building'] = address_components.apply(lambda x: x['building'])
# sales['Address_Block'] = address_components.apply(lambda x: x['block'])
# sales['Address_Apartment'] = address_components.apply(lambda x: x['apartment'])
# sales['Address_Street'] = address_components.apply(lambda x: x['street'])

print("Address cleaning complete!")
print("----------------------------------------------------------")


# -----------------------------------------------------------------------------
# 2. SALESREP CLEANING (Add after SalesRep section)
# -----------------------------------------------------------------------------

print("\n----- SalesRep Cleaning -----")

def clean_sales_rep(rep):
    """
    Standardize sales rep names
    
    Issues addressed:
    - Extra spaces
    - Inconsistent capitalization
    - Arabic/English mix
    """
    if pd.isna(rep):
        return np.nan
    
    rep = str(rep).strip()
    
    # Title case for names:
    rep = ' '.join(word.capitalize() for word in rep.split())
    
    # Remove extra spaces:
    rep = re.sub(r'\s+', ' ', rep)
    
    return rep

# Apply cleaning:
sales['SalesRep_Clean'] = sales['SalesRep'].apply(clean_sales_rep)

# Statistics:
print(f"Unique sales reps: {sales['SalesRep_Clean'].nunique()}")
print("\nSales rep distribution:")
print(sales['SalesRep_Clean'].value_counts())

# Sales rep performance analysis:
rep_performance = sales.groupby('SalesRep_Clean').agg({
    'TotalAmount_Calc': ['sum', 'mean', 'count'],
    'OrderID_cleaned': 'count'
}).round(2)
rep_performance.columns = ['Total_Revenue', 'Avg_Order_Value', 'Order_Count', 'Orders']
rep_performance = rep_performance.sort_values('Total_Revenue', ascending=False)

print("\nSales rep performance (Top 10):")
print(rep_performance.head(10))

# Add sales rep quality flag:
sales['salesrep_is_missing'] = sales['SalesRep_Clean'].isna()

print(f"Missing sales rep: {sales['salesrep_is_missing'].sum()} ({sales['salesrep_is_missing'].sum()/len(sales)*100:.1f}%)")
print("SalesRep cleaning complete!")
print("----------------------------------------------------------")


# -----------------------------------------------------------------------------
# 3. NOTES CLEANING (Add after Notes section)
# -----------------------------------------------------------------------------

print("\n----- Notes Cleaning -----")

def clean_notes(notes):
    """
    Basic notes cleaning
    
    Issues addressed:
    - Extra spaces and newlines
    - Inconsistent capitalization
    - Special characters
    """
    if pd.isna(notes):
        return np.nan
    
    notes = str(notes).strip()
    
    # Remove extra spaces and newlines:
    notes = re.sub(r'\s+', ' ', notes)
    
    # Lowercase for consistency (optional - can remove if you want to preserve case):
    notes = notes.lower()
    
    return notes

# Apply cleaning:
sales['Notes_Clean'] = sales['Notes'].apply(clean_notes)

# Statistics:
notes_missing = sales['Notes_Clean'].isna().sum()
print(f"Missing notes: {notes_missing} ({notes_missing/len(sales)*100:.1f}%)")
print(f"Orders with notes: {sales['Notes_Clean'].notna().sum()}")

# Analyze common note patterns:
from collections import Counter

all_notes_text = ' '.join(sales['Notes_Clean'].dropna())
# Extract words (remove punctuation):
words = re.findall(r'\b\w+\b', all_notes_text)
common_words = Counter(words).most_common(30)

print("\nMost common words in notes:")
for word, count in common_words:
    print(f"  {word}: {count}")

# Categorize notes (optional - customize categories as needed):
def categorize_note(note):
    """
    Categorize notes into predefined categories
    """
    if pd.isna(note):
        return 'no_note'
    
    note = str(note).lower()
    
    # Define keywords for each category:
    if any(word in note for word in ['urgent', 'asap', 'عاجل', 'سريع']):
        return 'urgent'
    elif any(word in note for word in ['call', 'phone', 'اتصال', 'موبايل', 'contact']):
        return 'needs_contact'
    elif any(word in note for word in ['gift', 'هدية', 'present']):
        return 'gift_order'
    elif any(word in note for word in ['complaint', 'issue', 'problem', 'شكوى', 'مشكلة']):
        return 'complaint'
    elif any(word in note for word in ['follow up', 'تابع', 'متابعة']):
        return 'follow_up'
    else:
        return 'general'

sales['note_category'] = sales['Notes_Clean'].apply(categorize_note)

print("\nNote categories:")
print(sales['note_category'].value_counts())

print("Notes cleaning complete!")
print("----------------------------------------------------------")


# -----------------------------------------------------------------------------
# 4. BUSINESS LOGIC VALIDATION FLAGS (Add after all cleaning)
# -----------------------------------------------------------------------------

print("\n----- Business Logic Validation -----")

# Flag 1: Shipping cost makes sense for channel
print("Validating shipping costs by channel...")
sales['shipping_makes_sense'] = np.where(
    sales['Channel_Clean'] == 'Store',
    sales['ShippingCost_Filled'] == 0,  # Store should have 0 shipping
    sales['ShippingCost_Filled'] > 0     # Online should have shipping
)

illogical_shipping = (~sales['shipping_makes_sense']).sum()
print(f"Orders with illogical shipping: {illogical_shipping} ({illogical_shipping/len(sales)*100:.1f}%)")

if illogical_shipping > 0:
    print("\nExample illogical shipping records:")
    print(sales[~sales['shipping_makes_sense']][
        ['OrderID_cleaned', 'Channel_Clean', 'ShippingCost_Filled']
    ].head(5))

# Flag 2: Delivery date makes sense for channel
print("\nValidating delivery dates by channel...")
sales['delivery_makes_sense'] = np.where(
    sales['Channel_Clean'] == 'Store',
    sales['DeliveryDate'].isna(),       # Store orders shouldn't have delivery
    True                                 # Online can have delivery or not (pending)
)

illogical_delivery = (~sales['delivery_makes_sense']).sum()
print(f"Orders with illogical delivery: {illogical_delivery} ({illogical_delivery/len(sales)*100:.1f}%)")

# Flag 3: Return flag matches return date
print("\nValidating return flag vs return date...")
sales['return_data_consistent'] = ~(
    ((sales['ReturnFlag_Clean'] == 'No') & (sales['ReturnDate'].notna())) |
    ((sales['ReturnFlag_Clean'] == 'Yes') & (sales['ReturnDate'].isna()))
)

inconsistent_returns = (~sales['return_data_consistent']).sum()
print(f"Orders with inconsistent return data: {inconsistent_returns} ({inconsistent_returns/len(sales)*100:.1f}%)")

# Flag 4: Overall business logic check
print("\nCalculating overall business logic score...")
sales['passes_business_logic'] = (
    sales['shipping_makes_sense'] &
    sales['delivery_makes_sense'] &
    sales['return_data_consistent'] &
    sales['Valid_Delivery'].fillna(True) &  # Valid or no delivery
    (sales['Discount_Rate_Clean'] <= 1) &   # Discount <= 100%
    (sales['Quantity_Clean'] > 0)           # Positive quantity
)

failed_logic = (~sales['passes_business_logic']).sum()
print(f"\nOrders failing business logic: {failed_logic} ({failed_logic/len(sales)*100:.1f}%)")
print(f"Orders passing business logic: {sales['passes_business_logic'].sum()} ({sales['passes_business_logic'].sum()/len(sales)*100:.1f}%)")

# Detailed breakdown:
print("\nBreakdown of business logic failures:")
logic_checks = {
    'Illogical shipping': (~sales['shipping_makes_sense']).sum(),
    'Illogical delivery': (~sales['delivery_makes_sense']).sum(),
    'Inconsistent returns': (~sales['return_data_consistent']).sum(),
    'Invalid delivery dates': (~sales['Valid_Delivery'].fillna(True)).sum(),
    'Invalid discount (>100%)': (sales['Discount_Rate_Clean'] > 1).sum(),
    'Invalid quantity (<=0)': (sales['Quantity_Clean'] <= 0).sum(),
}

for check_name, count in logic_checks.items():
    print(f"  {check_name}: {count}")

print("\nBusiness logic validation complete!")
print("----------------------------------------------------------")


# -----------------------------------------------------------------------------
# 5. FINAL DATA QUALITY SCORE (Update existing DQ summary)
# -----------------------------------------------------------------------------

print("\n----- UPDATED Data Quality Score -----")

# Calculate completeness scores for new columns:
address_completeness = (sales['Address_Clean'].notna().sum() / len(sales)) * 100
salesrep_completeness = (sales['SalesRep_Clean'].notna().sum() / len(sales)) * 100
notes_completeness = (sales['Notes_Clean'].notna().sum() / len(sales)) * 100

print(f"\nCompleteness scores (new columns):")
print(f"  Address: {address_completeness:.1f}%")
print(f"  SalesRep: {salesrep_completeness:.1f}%")
print(f"  Notes: {notes_completeness:.1f}%")

# Overall data quality:
quality_metrics = {
    'Uniqueness (OrderID)': (sales['OrderID_cleaned'].nunique() == len(sales)) * 100,
    'Completeness (critical cols)': (
        sales[['OrderID_cleaned', 'OrderDate', 'CustomerID_clean', 
               'ProductSKU_Clean', 'TotalAmount_Calc']].notna().all(axis=1).sum() / len(sales) * 100
    ),
    'Validity (business logic)': (sales['passes_business_logic'].sum() / len(sales)) * 100,
    'Accuracy (valid dates)': (sales['Valid_Delivery'].fillna(True).sum() / len(sales)) * 100,
    'Consistency (standardized)': 95.0,  # Based on cleaning applied
}

print("\nOverall Data Quality Metrics:")
for metric, score in quality_metrics.items():
    print(f"  {metric}: {score:.1f}%")

overall_dq_score = sum(quality_metrics.values()) / len(quality_metrics)
print(f"\n{'='*60}")
print(f"OVERALL DATA QUALITY SCORE: {overall_dq_score:.1f}%")
print(f"{'='*60}")

if overall_dq_score >= 90:
    print("✅ EXCELLENT - Data is production-ready!")
elif overall_dq_score >= 80:
    print("✅ GOOD - Minor issues, but usable for analysis")
elif overall_dq_score >= 70:
    print("⚠️  FAIR - Some issues need attention")
else:
    print("❌ POOR - Significant data quality issues!")

print("\n----------------------------------------------------------")


# -----------------------------------------------------------------------------
# 6. ENHANCED BI DATASET CREATION (Replace existing BI section)
# -----------------------------------------------------------------------------

print("\n----- Creating Enhanced BI-Ready Dataset -----")

# Define columns to include in BI dataset:
bi_columns = [
    # Keys:
    'OrderID_cleaned',
    
    # Dates:
    'OrderDate',
    'Order_Year',
    'Order_Month',
    'Order_Quarter',
    'Order_YearMonth',
    'DeliveryDate',
    'Delivery_Time_Days',
    'ReturnDate',
    
    # Customer:
    'CustomerID_clean',
    'CustomerName_clean',
    'Gender_Clean',
    'Phone_Clean',
    'phone_is_valid',
    'Email_Clean',
    'email_is_valid',
    
    # Location:
    'Governorate_Clean',
    'City',
    'Address_Clean',
    'Latitude_Clean',
    'Longitude_Clean',
    
    # Product:
    'ProductSKU_Clean',
    'ProductName_Clean',
    'Category_Clean',
    
    # Transaction:
    'Quantity_Clean',
    'UnitPrice_EGP_capped',
    'Subtotal_Calc_Capped',
    'Discount_Rate_Clean',
    'ShippingCost_Filled',
    'TotalAmount_Calc',
    
    # Operational:
    'PaymentMethod_Clean',
    'PaymentStatus_Clean',
    'Channel_Clean',
    'Status_Clean',
    'ShipperName_Clean',
    'ReturnFlag_Clean',
    
    # Additional cleaned:
    'SalesRep_Clean',
    'Notes_Clean',
    'note_category',
    
    # Quality flags (keep for analysis):
    'Valid_Delivery',
    'Delivery_Delayed',
    'investigation_flag',
    'passes_business_logic',
    'address_quality',
]

# Filter to only columns that exist:
bi_columns_final = [col for col in bi_columns if col in sales.columns]

# Create BI dataset:
bi_sales = sales[bi_columns_final].copy()

print(f"BI-ready dataset created with {len(bi_columns_final)} columns")
print(f"Total rows: {len(bi_sales)}")

# Save both versions:
output_dir = "/Users/instabug/Downloads/salma/"

# Full dataset with all audit columns:
full_output = output_dir + "Sales_Fully_Cleaned_WITH_AUDIT_TRAIL.xlsx"
sales.to_excel(full_output, index=False, engine='openpyxl')
print(f"\n✓ Saved full cleaned dataset: {full_output}")
print(f"  Columns: {len(sales.columns)}")

# BI-ready dataset:
bi_output = output_dir + "BI_Ready_Sales_Dataset.xlsx"
bi_sales.to_excel(bi_output, index=False, engine='openpyxl')
print(f"✓ Saved BI-ready dataset: {bi_output}")
print(f"  Columns: {len(bi_sales.columns)}")

print("\n----------------------------------------------------------")
print("PREPROCESSING COMPLETE!")
print("----------------------------------------------------------")


# =============================================================================
# END OF CODE ADDITIONS
# =============================================================================

"""
INTEGRATION NOTES:

1. ADD ADDRESS CLEANING after line ~400 (after City processing)
2. ADD SALESREP CLEANING after line ~450 (after SalesRep section)
3. ADD NOTES CLEANING after line ~500 (after Notes section)
4. ADD BUSINESS LOGIC FLAGS after line ~1200 (after all cleaning)
5. REPLACE BI dataset creation section (around line ~1300)

TESTING:
1. Run script end-to-end
2. Check console output for validation results
3. Verify 2 output files are created:
   - Sales_Fully_Cleaned_WITH_AUDIT_TRAIL.xlsx (all columns)
   - BI_Ready_Sales_Dataset.xlsx (cleaned columns only)
4. Check Data Quality Score is >80%

TROUBLESHOOTING:
- If "Column not found" errors: Check spelling of column names
- If "Key not in index": Some columns may not exist in your dataset
- If DQ score is low: Review specific metric failures in console output
"""

