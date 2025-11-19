import pandas as pd # A cleaning engine for data manipulation and analysis. It is used to read, filter, clean, and transform data
import numpy as np # Helps you handle missing values; Scientific computing ; Used for working with multidimensional arrays and mathematical functions.
from dateutil import parser # Converts messy date strings into proper dates and time formats
import re # Regular Expression module, which allows us to search for complex patterns (like currency codes embedded in numbers) within a string.
import seaborn as sns
import matplotlib.pyplot as plt

# file_path is a string variable that holds the name of the Excel workbook.Prevent typing it out four times.It does not open or read the actual file.
file_path = "/Users/salmaabdelkader/PycharmProjects/RetailCaseStudy/EG_Retail_Sales_Raw_CaseStudy 1.xlsx"

# Read all sheets into a dictionary. You point to the Excel file you uploaded
all_sheets = pd.read_excel(file_path, sheet_name=None)

# Now you can access/read each sheet (DataFrame) from the dictionary. Now you have 4 datasets in memory
sales = all_sheets["Sales_Orders_Raw"]
products = all_sheets["Products_Raw"]
govs = all_sheets["Governorates_Lookup_Noise"]
customers = all_sheets["Customers_Raw"]


# Set display options for easy inspection
pd.set_option('display.max_columns', None)
# This tells pandas to display all columns regardless of how many there are; in all dataframes
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 2000)
pd.set_option('display.float_format', lambda x: '%.5f' % x)


# --- 1. Initial Data Inspection ---
print("\n----- Initial Sales Data Inspection -----")
print("\nNumber of Rows and Columns:")
print(sales.shape)
print("\nNumber of Null Values per Column:")
print(sales.isnull().sum())
print("\nData types:")
#print(sales.info()) # To display a brief summary of the DataFrame, including data types and non-null values:
print(sales.dtypes)
print("\nStatistical summary:")
print(sales.describe()) #Looking at numeric info
print("\nExample of data:")
print(sales.head(5)) #Data Preview (first 5 rows)
print("\nNumber of duplicated rows:")
print(sales.duplicated().sum())
print("----------------------------------------------------------")

#print(sales.duplicated())
#print("----------------------------------------------------------")

# -------------------------------------------------------------------------
# OrderID Handling and Cleaning:
# -------------------------------------------------------------------------
# Check for inconsistencies within duplicated OrderIDs
print("\n--- Checking for inconsistent customer data within duplicated OrderIDs ---")
# Find order IDs that are duplicated and check how many unique customer IDs they have
inconsistent_orders = sales.groupby('OrderID').filter(lambda x: x['CustomerID'].nunique() > 1)
if not inconsistent_orders.empty:
    print("Found OrderIDs with conflicting customer information:")
    print(inconsistent_orders.sort_values('OrderID').head(10))
else:
    print("No conflicting customer information found for duplicated OrderIDs.")

# Create a new, cleaned ID column for problematic records
# This creates a new unique ID for each record with conflicting customer info
def create_cleaned_id(df):
    df_copy = df.copy()

    # Find the indices of all rows with duplicated OrderIDs, regardless of customer conflict
    # This is a more robust way to handle all duplicated IDs.
    duplicated_mask = df_copy['OrderID'].duplicated(keep=False)

    # Initialize the new cleaned column with original OrderIDs
    df_copy['OrderID_cleaned'] = df_copy['OrderID']

    # For the duplicated rows, generate a new unique ID
    if duplicated_mask.any():
        # Use cumcount to create a unique suffix for each duplicate group
        cum_count = df_copy[duplicated_mask].groupby('OrderID').cumcount().astype(str)

        # Format the suffix to match the desired pattern (e.g., NEW00001)
        # We start a new counter based on the number of original duplicates
        unique_suffix_mapping = (pd.Series(range(1, len(cum_count) + 1), index=cum_count.index)
                                 .apply(lambda x: f"NEW{x:05d}"))

        df_copy.loc[duplicated_mask, 'OrderID_cleaned'] = unique_suffix_mapping

    return df_copy

sales = create_cleaned_id(sales)

# Create a flag for records that were originally duplicated
# This flags ALL records that had a duplicated OrderID, not just the inconsistent ones
sales['is_OrderID_duplicated_flag'] = sales['OrderID'].duplicated(keep=False)

# Rename the original OrderID column
sales.rename(columns={'OrderID': 'Original OrderID'}, inplace=True)

# Reorder the columns to put 'OrderID_cleaned' at the beginning
cols = list(sales.columns)
cols.insert(1, cols.pop(cols.index('OrderID_cleaned')))
sales = sales[cols]

print("\n--- Validation of new OrderID_cleaned column ---")
print(f"Number of unique OrderID_cleaned: {sales['OrderID_cleaned'].nunique()}")
print(f"Total number of records: {len(sales)}")
print("New 'is_OrderID_duplicated_flag' added:", 'is_OrderID_duplicated_flag' in sales.columns)

# Show an example of the cleaned data with the new columns
print("\nExample of data after cleaning:")
print(sales.sort_values('Original OrderID').head(15))

print("--------------------------")

# -------------------------------------------------------------------------
#  OrderDate, DeliveryDate, ReturnDate Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- OrderDate Format Preview ---")
print(sales['OrderDate'].value_counts().head(20))


def clean_date_robust(x):
    try:
        # Pass locale='ar' to dateparser or set default locale for dateutil if needed,
        # but dateutil's parser is often smart enough for mixed English and Arabic months.
        return parser.parse(str(x), dayfirst=True)
    except (ValueError, TypeError):
        return pd.NaT

# Apply the function to your date columns
sales["OrderDate"] = sales["OrderDate"].apply(clean_date_robust)
sales["DeliveryDate"] = sales["DeliveryDate"].apply(clean_date_robust)
sales["ReturnDate"] = sales["ReturnDate"].apply(clean_date_robust)

#Checking that the fn is working and data type changed
# print(sales[['OrderDate', 'DeliveryDate', 'ReturnDate']].dtypes)

print("\n--- Value counts for original ReturnFlag ---")
print(sales['ReturnFlag'].value_counts())

# Map to standardized values
return_flag_map = {'نعم': 'Yes','Y' : 'Yes', '1' : 'Yes', 'لا': 'No', '0': 'No' , 'N' : 'No' }
sales['ReturnFlag_Clean'] = sales['ReturnFlag'].replace(return_flag_map)
# mesh ayza aamel new column ayza aadel aal adem

#Checking that the map is working and values changed
print(sales['ReturnFlag_Clean'].value_counts())

#print(sales.head())

# For rows where ReturnFlag is 'No', and ReturnDate is NaT, fill with a descriptive string.
#sales.loc[(sales['ReturnFlag_Clean'] == 'No') & sales['ReturnDate'].isna(), 'ReturnDate'] = 'No Return'
#moshkelet el data type okay
#print(sales.head())

#Check order date against delivery
sales['delivery_is_before_order'] = sales['DeliveryDate'] < sales['OrderDate']
print("\n--- Orders with impossible delivery dates ---")
print(sales[sales['delivery_is_before_order']].head())

#Check return date against order and delivery
# Assuming ReturnDate is still of type datetime64[ns]
sales['return_is_before_order'] = sales['ReturnDate'] < sales['OrderDate']
sales['return_is_before_delivery'] = sales['ReturnDate'] < sales['DeliveryDate']

print("\n--- Orders with impossible return dates (before order) ---")
print(sales[sales['return_is_before_order']].head())
print("\n--- Orders with impossible return dates (before delivery) ---")
print(sales[sales['return_is_before_delivery']].head())

print(sales[['OrderDate', 'DeliveryDate', 'ReturnDate']].isnull().sum())

sales['orderdate_is_null'] = sales['OrderDate'].isnull()
sales['deliverydate_is_null'] = sales['DeliveryDate'].isnull()

print("New flags added to the DataFrame.")
print(sales.head())

#✔ DeliveryTime = DeliveryDate – OrderDate
#sales['Delivery_Time_days'] = (sales['DeliveryDate'] - sales['OrderDate']).dt.days
#sales['Delivery_Time_Invalid'] = sales['Delivery_Time_days'] < 0

#print(sales[['OrderDate', 'DeliveryDate', 'ReturnDate']].dtypes)

# ------------------------------------------------------------
# BI-READY DATE COLUMNS (no imputation, no altering raw dates)
# ------------------------------------------------------------

# Extract safe features
sales['Order_Year'] = sales['OrderDate'].dt.year
sales['Order_Month'] = sales['OrderDate'].dt.month
sales['Order_Quarter'] = sales['OrderDate'].dt.quarter

sales['Delivery_Year'] = sales['DeliveryDate'].dt.year
sales['Delivery_Month'] = sales['DeliveryDate'].dt.month
sales['Delivery_Quarter'] = sales['DeliveryDate'].dt.quarter

sales['Return_Year'] = sales['ReturnDate'].dt.year
sales['Return_Month'] = sales['ReturnDate'].dt.month
sales['Return_Quarter'] = sales['ReturnDate'].dt.quarter

# Year-Month labels (better for pivot tables)
sales['Order_YearMonth'] = sales['OrderDate'].dt.to_period('M').astype(str)
sales['Delivery_YearMonth'] = sales['DeliveryDate'].dt.to_period('M').astype(str)
sales['Return_YearMonth'] = sales['ReturnDate'].dt.to_period('M').astype(str)

# Delivery time in days (NaN if missing or invalid)
sales['Delivery_Time_Days'] = (sales['DeliveryDate'] - sales['OrderDate']).dt.days
sales['Delivery_Delayed'] = sales['Delivery_Time_Days'] > 5

# Return time in days (NaN if missing or invalid)
sales['Return_Time_Days'] = (sales['ReturnDate'] - sales['DeliveryDate']).dt.days

# Validity flags
sales['Valid_Delivery'] = np.where(
    (sales['DeliveryDate'].notna()) & (sales['OrderDate'].notna()) &
    (sales['DeliveryDate'] >= sales['OrderDate']),
    True, False
)

sales['Valid_Return'] = np.where(
    (sales['ReturnDate'].notna()) & (sales['DeliveryDate'].notna()) &
    (sales['ReturnDate'] >= sales['DeliveryDate']),
    True, False
)

print("\n--- BI Date Columns Added ---")
print([
    'Order_Year','Order_Month','Order_Quarter','Order_YearMonth',
    'Delivery_Year','Delivery_Month','Delivery_Quarter','Delivery_YearMonth',
    'Return_Year','Return_Month','Return_Quarter','Return_YearMonth',
    'Delivery_Time_Days','Return_Time_Days',
    'Valid_Delivery','Valid_Return'
])


print("--------------------------")

# -------------------------------------------------------------------------
#  CustomerName Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- CustomerName Value Counts (Initial) ---")
print(sales['CustomerName'].value_counts(dropna=False).head(20))
#print(f"\nMissing CustomerName values: {sales['CustomerName'].isnull().sum()}") no nulls

# --- 2. Standardize and Clean ---
# Create a new column for the cleaned name
sales['CustomerName_clean'] = sales['CustomerName'].astype(str).str.strip().str.lower()

#print(sales.head())

# -------------------------------------------------------------------------
#  Phone Handling and Cleaning:
# -------------------------------------------------------------------------
# Check for nulls and preview the formats
print("--- Phone Column Preview ---")
print(sales['Phone'].value_counts(dropna=False).head(20))

# Get a count of the null values
print(f"\nNumber of null Phone values: {sales['Phone'].isnull().sum()}")

# Clean and standardize phone numbers to Egyptian format
def clean_phone(phone):
    if pd.isna(phone):
        return np.nan

    phone = str(phone).strip()
    # Remove everything except digits
    phone = re.sub(r'[^0-9]', '', phone)

    # Remove leading country codes
    phone = re.sub(r'^(20|0020|00020|000020|0+20)', '', phone)

    # Remove leading zeros that appear because of reformatting
    phone = re.sub(r'^0+', '0', phone)

    # If length is exactly 11 and starts with valid prefixes
    valid_prefixes = ('010', '011', '012', '015', '014')
    if len(phone) == 11 and phone.startswith(valid_prefixes):
        return f'+2{phone}'

    return np.nan  # everything else invalid


sales['Phone_Clean'] = sales['Phone'].apply(clean_phone)
sales['phone_is_valid'] = sales['Phone_Clean'].notna()

print("\n--- Phone After Cleaning ---")
print(f"Valid phones: {sales['phone_is_valid'].sum()}")
print(f"Invalid phones: {(~sales['phone_is_valid']).sum()}")
print(sales['Phone_Clean'].value_counts(dropna=False).head(10))

"""
print("\n--- Duplicate Phone Numbers After Cleaning ---")

# Count duplicates (excluding NaN)
cleaned_phones = sales['Phone_Clean'].dropna()

# Number of duplicated values
num_dupes = cleaned_phones.duplicated().sum()
print(f"Number of duplicated phone numbers: {num_dupes}")

# Which phone numbers are duplicated
dupe_values = cleaned_phones[cleaned_phones.duplicated()].unique()
print("\nDuplicated phone values:")
print(dupe_values)

# Show rows containing duplicated phone numbers
if len(dupe_values) > 0:
    print("\nRows with duplicated phone numbers:")
    print(
        sales[sales['Phone_Clean'].isin(dupe_values)]
        [['OrderID_cleaned', 'CustomerName_clean', 'Phone', 'Phone_Clean']]
        .sort_values('Phone_Clean')
    )
else:
    print("No duplicate phone numbers found.")
"""

# -------------------------------------------------------------------------
#  Email Handling and Cleaning:
# -------------------------------------------------------------------------
print("\n--- Email Column Preview ---")
print(sales['Email'].value_counts(dropna=False).head(20))
print(f"\nNumber of null Email values: {sales['Email'].isnull().sum()}")

# Validate and clean email addresses
def validate_email(email):
    """
    Validates email format using regex
    Returns NaN for invalid emails (including those with Arabic characters)
    """
    if pd.isna(email):
        return np.nan
    email = str(email).strip().lower()
    email = email.replace(" ", "")     # Remove all spaces inside the email
    
    # Remove emails with Arabic characters
    if bool(re.search(r'[\u0600-\u06FF]', email)):
        return np.nan

    # Basic email regex: something@domain.ext
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return np.nan

sales['Email_Clean'] = sales['Email'].apply(validate_email)
sales['email_is_valid'] = sales['Email_Clean'].notna()

print("\n--- Email After Cleaning ---")
print(f"Valid emails: {sales['email_is_valid'].sum()}")
print(f"Invalid emails: {(~sales['email_is_valid']).sum()}")
print(sales['Email_Clean'].value_counts(dropna=False).head(10))

# -------------------------------------------------------------------------
#  CustomerId Handling and Cleaning:
# -------------------------------------------------------------------------
# Get a preview of existing CustomerID formats
print("--- CustomerID Value Counts (Initial) ---")
print(sales['CustomerID'].value_counts(dropna=False).head(10))
print(f"\nNumber of null CustomerID values: {sales['CustomerID'].isnull().sum()}")

# Standardize CustomerID format
def clean_customer_id(cust_id):
    """
    Standardizes CustomerID format: uppercase, remove "CUS-" prefix variations
    Target format: C + number (e.g., C001, C100)
    """
    if pd.isna(cust_id):
        return np.nan
    cust_id = str(cust_id).upper().strip()
    # Standardize format: remove "CUS-" prefix, keep just C prefix
    cust_id = cust_id.replace('CUS-', 'C').replace('CUS', 'C')
    return cust_id

sales['CustomerID_clean'] = sales['CustomerID'].apply(clean_customer_id)

#----------------------------------------------------------

#------------------------------------------------------
# Get a preview of standardized CustomerID formats

#duplicated_customers = sales[sales['CustomerID_clean'].duplicated(keep=False)]
#print(duplicated_customers[['CustomerID_clean','CustomerName','Phone','Email','Address']].head(20))

print("\n--- CustomerID Value Counts (Standardized) ---")
print(sales['CustomerID_clean'].value_counts(dropna=False).head(20))

# 1. Detect duplicated CustomerIDs
dup_mask = sales['CustomerID_clean'].duplicated(keep=False)

# 2. Show grouped duplicated CustomerIDs
duplicated_customers = sales[dup_mask].sort_values('CustomerID_clean')

print("\n--- Duplicated CustomerID Groups ---")
for cid, group in duplicated_customers.groupby('CustomerID_clean'):
    print(f"\nCustomerID = {cid}")
    print(group[['CustomerID_clean', 'CustomerName_clean', 'Phone_Clean', 'Email_Clean', 'Address']])
#---------------
# Create a fingerprint for matching customers when ID is missing
sales['customer_fingerprint'] = (
    sales['Phone_Clean'].fillna('') + "_" +
    sales['Email_Clean'].fillna('') + "_" +
    sales['Address'].fillna('').astype(str).str.strip().str.lower()
)


def impute_customer_id(df):
    df = df.copy()

    # Create a running counter for guest IDs
    guest_counter = 1

    # Create a lookup for fast searching
    # We drop duplicates so we don’t pick conflicting rows
    ref = df[['CustomerID_clean', 'Phone_Clean', 'Email_Clean', 'Address']] \
        .dropna(subset=['CustomerID_clean']).copy()

    # Iterate over rows where CustomerID is missing
    for idx, row in df[df['CustomerID_clean'].isna()].iterrows():

        phone = row['Phone_Clean']
        email = row['Email_Clean']
        address = row['Address']

        # -------------------------------
        # 1. Try exact phone match
        # -------------------------------
        if pd.notna(phone):
            phone_match = ref[ref['Phone_Clean'] == phone]
            if len(phone_match) > 0:
                df.at[idx, 'CustomerID_clean'] = phone_match['CustomerID_clean'].iloc[0]
                continue

        # -------------------------------
        # 2. Try email match
        # -------------------------------
        if pd.notna(email):
            email_match = ref[ref['Email_Clean'] == email]
            if len(email_match) > 0:
                df.at[idx, 'CustomerID_clean'] = email_match['CustomerID_clean'].iloc[0]
                continue

        # -------------------------------
        # 3. Try address match (last resort)
        # -------------------------------
        if pd.notna(address):
            address_match = ref[ref['Address'] == address]
            if len(address_match) > 0:
                df.at[idx, 'CustomerID_clean'] = address_match['CustomerID_clean'].iloc[0]
                continue

        # -------------------------------
        # 4. No matches → assign new Guest ID
        # -------------------------------
        new_guest_id = f"GUEST{guest_counter:04d}"
        df.at[idx, 'CustomerID_clean'] = new_guest_id
        guest_counter += 1

    return df

sales = impute_customer_id(sales)

print("\nAfter imputation:")
print("Missing CustomerID_clean = ", sales['CustomerID_clean'].isna().sum())

print("\nExample of imputed records:")
print(sales[sales['CustomerID_clean'].str.contains("GUEST", na=False)].head())


# -------------------------------------------------------------------------
#  Gender Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- Gender Column Preview ---")
print(sales['Gender'].value_counts(dropna=False))

# Create a mapping dictionary based on your observed values
gender_map = { "M": "Male", "F": "Female", "ذكر": "Male", "أنثى": "Female" }

# Create a new, clean column using the map and handle nulls
sales['Gender_Clean'] = sales['Gender'].map(gender_map)

# Fill any remaining NaN values with 'Unknown'
sales['Gender_Clean'] = sales['Gender_Clean'].fillna('Not Specified')

#checking eno shaghal
#print("\n--- Gender Column Preview (after cleaning) ---")
#print(sales['Gender_Clean'].value_counts(dropna=False))

# -------------------------------------------------------------------------
#  Governorate Handling and Cleaning:
# -------------------------------------------------------------------------

print("--- Governorates Value Counts (Initial) ---")
print(sales['Governorate'].value_counts(dropna=False))

# --- 1. Standardize and Clean the column ---
# Create a new, clean column
sales['Governorate_Clean'] = sales['Governorate'].astype(str).str.strip()

# Based on your inspection, define the mapping dictionary.
governorate_map = {
    # Luxor Variations
    'luxor': 'Luxor',
    'Luxor': 'Luxor',
    'LUXOR': 'Luxor',
    'الأقصر': 'Luxor',
    'Al Luxor': 'Luxor',

    # Dakahlia Variations
    'dakahlia': 'Dakahlia',
    'Dakahlia': 'Dakahlia',
    'الدقهلية': 'Dakahlia',
    'DAKAHLIA': 'Dakahlia',

    # South Sinai Variations
    'south sinai': 'South Sinai',
    'South Sinai': 'South Sinai',
    'جنوب سيناء': 'South Sinai',
    'al south sinai': 'South Sinai',
    'SOUTH SINAI': 'South Sinai',
    'Al South Sinai': 'South Sinai',

    # Alexandria Variations
    'alexandria': 'Alexandria',
    'Alexandria': 'Alexandria',
    'الإسكندرية': 'Alexandria',
    'Al Alexandria': 'Alexandria',

    # Red Sea Variations
    'red sea': 'Red Sea',
    'البحر الأحمر': 'Red Sea',
    'RED SEA': 'Red Sea',
    'Al Red Sea': 'Red Sea',
    'Red Sea': 'Red Sea',

    # Gharbia Variations
    'gharbia': 'Gharbia',
    'الغربية': 'Gharbia',
    'GHARBIA': 'Gharbia',
    'Al Gharbia': 'Gharbia',
    'Gharbia': 'Gharbia',

    # Qalyubia Variations
    'qalyubia': 'Qalyubia',
    'Qalyubia': 'Qalyubia',
    'القليوبية': 'Qalyubia',
    'QALYUBIA': 'Qalyubia',

    # Aswan Variations
    'aswan': 'Aswan',
    'Aswan': 'Aswan',
    'اسوان': 'Aswan',
    'أسوان': 'Aswan',
    'Al Aswan': 'Aswan',

    # Asyut Variations
    'asyut': 'Asyut',
    'Asyut': 'Asyut',
    'ASYUT': 'Asyut',
    'أسيوط': 'Asyut',
    'Al Asyut': 'Asyut',

    # Sharqia Variations
    'sharqia': 'Sharqia',
    'Sharqia': 'Sharqia',
    'الشرقية': 'Sharqia',
    'SHARQIA': 'Sharqia',

    # Giza Variations
    'giza': 'Giza',
    'الجيزة': 'Giza',
    'gizah': 'Giza',
    'Al Giza': 'Giza',
    'GIZA': 'Giza',
    'Giza': 'Giza',
    'Gizah': 'Giza',

    # Cairo Variations
    'cairo': 'Cairo',
    'Cairo': 'Cairo',
    'القاهرة': 'Cairo',
    'القاهره': 'Cairo',

    # Add all other mappings you find during your preview
}

# Apply the map to a new, clean column.
sales['Governorate_Clean'] = sales['Governorate'].map(governorate_map)

# Handle cases that were not in your map (if any)
# This will catch typos or other missing values.
sales['Governorate_Clean'] = sales['Governorate_Clean'].fillna('Unknown')

# --- 5. Verify results --- checking sah
#print("\n--- Governorate Value Counts (Standardized) ---")
#print(sales['Governorate_Clean'].value_counts(dropna=False))

#print("\nComparison of original and standardized data:")
#print(sales[['Governorate', 'Governorate_Clean']].head(10))

# -------------------------------------------------------------------------
#  City Handling and Cleaning:
# -------------------------------------------------------------------------

#checking the values seeing if haga metkarara be spelling mokhtalef
print("--- City Value Counts (Initial) ---")
print(sales['City'].value_counts(dropna=False))

# -------------------------------------------------------------------------
#  PaymentStatus Handling and Cleaning:
# -------------------------------------------------------------------------

print("--- PaymentStatus Value Counts (Initial) ---")
print(sales['PaymentStatus'].value_counts(dropna=False))

# Use .replace() to change only the specific values
# The rest of the values in the column remain unchanged
sales['PaymentStatus_Clean'] = sales['PaymentStatus'].replace({
    'غير مدفوع': 'Unpaid',
    'مدفوع': 'Paid',
})

#checking
#print(sales['PaymentStatus_Clean'].value_counts(dropna=False))

# -------------------------------------------------------------------------
#  PaymentMethod Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- PaymentMethod Value Counts (Initial) ---")
print(sales['PaymentMethod'].value_counts(dropna=False))

# Use .replace() to change only the specific values
# The rest of the values in the column remain unchanged
sales['PaymentMethod_Clean'] = sales['PaymentMethod'].replace({
    'COD': 'Cash on Delivery',
    'Cash': 'Cash on Delivery',
    'فوري': 'Fawry',
})

#checking
#print(sales['PaymentMethod_Clean'].value_counts(dropna=False))

# -------------------------------------------------------------------------
#  ShippingCost Handling and Cleaning:
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
#  Status Handling and Cleaning:
# -------------------------------------------------------------------------

print("--- Status Value Counts (Initial) ---")
print(sales['Status'].value_counts(dropna=False))

# Use .replace() to change only the specific values
# The rest of the values in the column remain unchanged
sales['Status_Clean'] = sales['Status'].replace({
    'ملغي': 'Cancelled',
})
# Handle NaN values explicitly
sales['Status_Clean'] = sales['Status_Clean'].fillna('Unknown') # mesh arfa da sah wala ehhhh

#checking
print(sales['Status_Clean'].value_counts(dropna=False))

#--------

missing_status_mask = sales['Status'].isnull()
missing_status_orders = sales[missing_status_mask]
print(missing_status_orders)

print("\n--- Channel Distribution for Orders with Missing Status ---")
print(missing_status_orders['Channel'].value_counts(dropna=False))

#Channel Distribution:
#The missing statuses are not evenly distributed across all channels.
#WhatsApp (7) and Tel-Sales (5) have a higher count of missing statuses compared to E-com and Store.
#Insight: This suggests that the data collection process might be less robust for the WhatsApp and Tel-Sales channels.
# It's possible that the order status is not automatically updated in the same way as it is for the E-commerce channel.


print("\n--- PaymentStatus Distribution for Orders with Missing Status ---")
print(missing_status_orders['PaymentStatus'].value_counts(dropna=False))

#PaymentStatus Distribution:
#Most of the missing statuses are associated with orders that have an 'Unpaid' (7) or 'Pending' (5) payment status.
#Insight: This is a very strong indicator that the order status is not updated until payment is confirmed.
# For orders where payment is not yet complete, the status remains blank.
# The one order with a 'Paid' status could be an anomaly or a data entry error.

print("\n--- OrderDate Range for Orders with Missing Status ---")
if not missing_status_orders.empty:
    earliest_date = missing_status_orders['OrderDate'].min()
    latest_date = missing_status_orders['OrderDate'].max()
    print(f"Earliest OrderDate: {earliest_date}")
    print(f"Latest OrderDate: {latest_date}")
else:
    print("No orders with missing status to analyze.")

#OrderDate Range:
#The range of dates (2024-01-06 to 2024-12-02) is quite broad, spanning nearly the entire year.
#Insight: This suggests that the issue is not related to a single, isolated incident (like a data migration problem that happened on a specific date).
#Instead, it appears to be a systemic issue that has been ongoing for some time, which aligns with the hypothesis about payment status.

# -------------------------------------------------------------------------
#  ShipperName Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- ShipperName Value Counts (Initial) ---")
print(sales['ShipperName'].value_counts(dropna=False))

# Use .replace() to change only the specific values
# The rest of the values in the column remain unchanged
sales['ShipperName_Clean'] = sales['ShipperName'].replace({
    'بريد مصر': 'Egypt Post',
})

#checking
print(sales['ShipperName_Clean'].value_counts(dropna=False))


# -------------------------------------------------------------------------
#  Channel Handling and Cleaning:
# -------------------------------------------------------------------------
print("--- Channel Value Counts (Initial) ---")
print(sales['Channel'].value_counts(dropna=False))

# Use .replace() to change only the specific values
# The rest of the values in the column remain unchanged
sales['Channel_Clean'] = sales['Channel'].replace({
    'تجارة إلكترونية': 'E-com',
})

#checking
print(sales['Channel_Clean'].value_counts(dropna=False))

# -------------------------------------------------------------------------
#  Latitude and Longitude Handling and Cleaning:
# -------------------------------------------------------------------------
# 1. Fix the decimal separator (comma to period)
# This step corrects a common formatting issue where commas are used as decimal points.
# By converting to a string first, we can use .str.replace() safely.
#sales['Latitude_Corrected'] = sales['Latitude'].astype(str).str.replace(',', '.', regex=False)
#sales['Longitude_Corrected'] = sales['Longitude'].astype(str).str.replace(',', '.', regex=False)
#.astype(str): This is a crucial first step. It ensures that all values in the column, including numbers, are treated as strings so that .str.replace() can be used without errors.
#.str.replace(',', '.', regex=False): This is the key line that directly addresses your issue. It replaces all commas (,) with periods (.) in the string. regex=False is slightly faster as it's a simple string replacement.
#pd.to_numeric(..., errors='coerce'): After correcting the decimal separator, this line can now successfully convert the strings into numeric types. Values that still cannot be converted (e.g., truly invalid or non-numeric entries) will be correctly turned into NaN.

# 1. Fix the decimal separator (comma  to period) and convert to numeric in one step
# Any non-numeric values will become NaN due to errors='coerce'.
sales['Latitude_Clean'] = pd.to_numeric(sales['Latitude'].astype(str).str.replace(',', '.', regex=False), errors='coerce')
sales['Longitude_Clean'] = pd.to_numeric(sales['Longitude'].astype(str).str.replace(',', '.', regex=False), errors='coerce')

# 2. Convert to numeric, coercing errors to become NaN
# This step converts the corrected string values into a numeric type (float).
# Any values that still can't be converted to a number (e.g., 'invalid') will become NaN.
#sales['Latitude_Clean'] = pd.to_numeric(sales['Latitude_Corrected'], errors='coerce')
#sales['Longitude_Clean'] = pd.to_numeric(sales['Longitude_Corrected'], errors='coerce')

#mesh hassa leha lazma awyyy
#print("\n--- Lat/Long Cleaning: Initial Conversion ---")
#print(f"Missing Latitude values after conversion: {sales['Latitude_Clean'].isnull().sum()}")
#print(f"Missing Longitude values after conversion: {sales['Longitude_Clean'].isnull().sum()}")

# 2. Check for invalid or potentially swapped coordinate values
# Create a mask for rows where the latitude is outside the valid range

#Latitude must be between -90 and +90.
#Longitude must be between -180 and +180.

# Record the rows that were missing data initially (Crucial for tracking imputation success)
sales['coords_initially_missing'] = sales['Latitude_Clean'].isnull() | sales['Longitude_Clean'].isnull()

# Initialize the main audit flag
sales['investigation_flag'] = 'Valid/Unknown'

# --- 2. Bounds Check and Manual Swapping ---

print("\n--- 2. Global Bounds Check and Manual Swapping ---")

# Identify potential swaps (Invalid NOW, Valid LATER) - Keep this 'if' for information
global_invalid_mask = (sales['Latitude_Clean'].abs() > 90) | (sales['Longitude_Clean'].abs() > 180)
swapped_is_valid_mask = (sales['Longitude_Clean'].abs() <= 90) & (sales['Latitude_Clean'].abs() <= 180)
potential_swap_mask = global_invalid_mask & swapped_is_valid_mask

if potential_swap_mask.any():
    print(f"⚠️ **Found {potential_swap_mask.sum()} rows that COULD be valid if SWAPPED.**")
    print(sales.loc[potential_swap_mask, ['Latitude', 'Longitude', 'Latitude_Clean', 'Longitude_Clean']].head(3))
else:
    print("✅ No potential swaps found to meet global bounds (90/180).")


# Explicit Manual Swap for Index 95 (Direct operation - No IF/ELSE needed)
manual_swap_index = 95

# Use direct assignment to swap the values
temp_lat = sales.loc[manual_swap_index, 'Latitude_Clean']
sales.loc[manual_swap_index, 'Latitude_Clean'] = sales.loc[manual_swap_index, 'Longitude_Clean']
sales.loc[manual_swap_index, 'Longitude_Clean'] = temp_lat

# Flag the row immediately
sales.loc[manual_swap_index, 'investigation_flag'] = 'Manually Swapped'

# Discard remaining globally invalid coordinates AFTER the manual swap
remaining_global_invalid_mask = (sales['Latitude_Clean'].abs() > 90) | (sales['Longitude_Clean'].abs() > 180)

if remaining_global_invalid_mask.any():  # Keep this 'if' for informative printing
    print(f"**Discarding {remaining_global_invalid_mask.sum()} truly globally invalid coordinates.**")
    # Set coordinates to NaN and flag them
    sales.loc[remaining_global_invalid_mask, ['Latitude_Clean', 'Longitude_Clean']] = np.nan
    sales.loc[remaining_global_invalid_mask, 'investigation_flag'] = 'Globally_Invalid_Discarded'

# --- 3. Egypt Geographical Range Check and Discarding ---

# Define Egypt's approximate valid range.
egypt_lat_min, egypt_lat_max = 22, 32
egypt_long_min, egypt_long_max = 25, 35

print("\n--- 3. Egypt Range Check and Discarding ---")

# Mask for coordinates that are valid numbers but outside Egypt's box
invalid_egypt_coords_mask = (
    (sales['Latitude_Clean'].notna()) & (sales['Longitude_Clean'].notna()) & # <-- ADDED THIS LINE
    (
        (sales['Latitude_Clean'] < egypt_lat_min) | (sales['Latitude_Clean'] > egypt_lat_max) |
        (sales['Longitude_Clean'] < egypt_long_min) | (sales['Longitude_Clean'] > egypt_long_max)
    )
)

if invalid_egypt_coords_mask.any():  # Keep this 'if' for informative printing
    print(f"**Found {invalid_egypt_coords_mask.sum()} coordinates outside the Egypt scope.**")
    print("\nRows outside Egypt's geographical scope (Clean Lat/Long before NaN conversion):")
    print(sales.loc[invalid_egypt_coords_mask, ['Latitude_Clean', 'Longitude_Clean']].head())

    # Set coordinates outside the required Egypt range to NaN
    sales.loc[invalid_egypt_coords_mask, ['Latitude_Clean', 'Longitude_Clean']] = np.nan

    # Update the investigation flag for these rows (only if they weren't previously flagged)
    sales.loc[invalid_egypt_coords_mask & (
                sales['investigation_flag'] == 'Valid/Unknown'), 'investigation_flag'] = 'Out_of_Egypt_Scope'

# --- 4. Hierarchical Imputation (Filling NaNs) ---

# Update flag for initially missing values that are still 'Valid/Unknown'
sales.loc[sales['coords_initially_missing'] & (
            sales['investigation_flag'] == 'Valid/Unknown'), 'investigation_flag'] = 'Initially_Missing'

print("\n--- 4. Hierarchical Imputation for Missing Coordinates ---")

# Imputation Priority 1: Address (Most specific)
sales['Latitude_Clean'] = sales.groupby('Address')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('Address')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))

print(sales['Latitude_Clean'].isnull().sum())
print(sales['Longitude_Clean'].isnull().sum())


# Imputation Priority 2: City (Less specific, only fills remaining NaNs)
sales['Latitude_Clean'] = sales.groupby('City')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('City')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))

print(sales['Latitude_Clean'].isnull().sum())
print(sales['Longitude_Clean'].isnull().sum())

# Imputation Priority 3: Governorate (Least specific, only fills remaining NaNs)
sales['Latitude_Clean'] = sales.groupby('Governorate')['Latitude_Clean'].transform(lambda x: x.fillna(x.mean()))
sales['Longitude_Clean'] = sales.groupby('Governorate')['Longitude_Clean'].transform(lambda x: x.fillna(x.mean()))

print(sales['Latitude_Clean'].isnull().sum())
print(sales['Longitude_Clean'].isnull().sum())


# --- 5. Final Validation and Flagging ---

# Create the final null flag
sales['coords_is_null'] = sales['Latitude_Clean'].isnull() | sales['Longitude_Clean'].isnull()

# 1. Flag successful imputations: Rows that were 'Initially_Missing' but are now NOT null
imputed_mask = (~sales['coords_is_null']) & (sales['investigation_flag'] == 'Initially_Missing')
sales.loc[imputed_mask, 'investigation_flag'] = 'Imputed_by_Location'

# 2. Flag remaining nulls: Rows that couldn't be fixed by any step
unknown_mask = sales['coords_is_null'] & sales['investigation_flag'].isin(['Valid/Unknown', 'Initially_Missing'])
sales.loc[unknown_mask, 'investigation_flag'] = 'Needs_Further_Investigation/Unknown'

# 3. Explicitly mark all remaining 'Valid/Unknown' rows as 'Valid' (The crucial step)
# These are the rows that had clean data from the start and passed all checks.
valid_mask = sales['investigation_flag'] == 'Valid/Unknown'
sales.loc[valid_mask, 'investigation_flag'] = 'Valid'

print("\n--- ✅ Final Cleaning Summary ---")
print(f"Total rows with initially missing coordinates: {sales['coords_initially_missing'].sum()}")
print(f"Number of remaining missing coordinates (Needs Investigation): {sales['coords_is_null'].sum()}")
print("\nFinal Flag Distribution:")
print(sales['investigation_flag'].value_counts())
print("\nExample of cleaned coordinates and flags:")
print(sales[['Latitude', 'Longitude', 'Latitude_Clean', 'Longitude_Clean', 'coords_initially_missing','investigation_flag']].head(10))

print(sales['Latitude_Clean'].isnull().sum())
print(sales['Longitude_Clean'].isnull().sum())

# -------------------------------------------------------------------------
#  ProductSKU, ProductName,	Category Handling and Cleaning:
# -------------------------------------------------------------------------


def standardize_text(text):
    # 1. Handle actual None or standard NaN values explicitly
    if pd.isna(text):
        return text  # Returns np.nan or None

    # 2. Convert to string FIRST to handle mixed types (like float or int SKU numbers)
    text = str(text)

    # 3. Handle 'None' or 'Nan' strings that might have been created by the conversion
    if text.lower() in ('none', 'nan', ''):
        return np.nan  # Return a standard NaN for consistency

    # 4. Apply standardization steps

    # Remove leading/trailing spaces # Convert to lowercase
    text = text.strip().lower()

    # Handle common Arabic text variations
    #text = text.replace('أ', 'ا').replace('إ', 'ا').replace('ة', 'ه').replace('ى', 'ي')

    return text

# Apply this function to create new, clean columns in the sales sheet
sales['ProductSKU_Clean'] = sales['ProductSKU'].apply(standardize_text)
#sales['ProductSKU_Clean'] = standardize_text(sales['ProductSKU'])
sales['ProductName_Clean'] = sales['ProductName'].apply(standardize_text)
sales['Category_Clean'] = sales['Category'].apply(standardize_text)


print(sales['ProductSKU_Clean'].value_counts(dropna=False))
# 1. Use .str.replace() to systematically remove ALL hyphens in the column.
sales['ProductSKU_Clean'] = sales['ProductSKU_Clean'].str.replace('-', '', regex=False)
#checking
#print(sales['ProductSKU_Clean'].value_counts(dropna=False))

print(sales['ProductName_Clean'].value_counts(dropna=False))
# 1. REMOVE the " - [Arabic Word]" pattern (The original goal)
# Using \s+ to catch multiple spaces and ensure robustness
sales['ProductName_Clean'] = sales['ProductName_Clean'].str.replace(r'\s+-\s*[ا-ي\s]+', '', regex=True)

sales['ProductName_Clean'] = sales['ProductName_Clean'].replace({
    'bluetooth سماعة': 'bluetooth headphones',
    'puzzle 1000pcsأحجية': 'puzzle 1000pcs',
    'organic زيت زيتون 1l': 'organic olive oil 1l',
    'labtop i7 16gb': 'laptop i7 16gb'
})

#checking
#print(sales['ProductName_Clean'].value_counts(dropna=False))


print(sales['Category_Clean'].value_counts(dropna=False))

sales['Category_Clean'] = sales['Category_Clean'].replace({
    'إلكترونيات': 'electronics',
    'electrnics': 'electronics'
})
#checking
#print(sales['Category_Clean'].value_counts(dropna=False))


#print(sales.head())



#------------------------------------------------------------------------------------
#                   IN PRODUCTS SHEET

# --- STEP 4: CLEANING THE SOURCE TABLE (products_raw) ---

print("\n--- 4. Standardizing and Preparing Product Lookup Table ---")
# 4.1. Apply Standardization DIRECTLY to the original columns (OVERWRITING)
# NOTE: The original SKU column is named 'SKU'.
products['SKU'] = products['SKU'].apply(standardize_text)
products['ProductName'] = products['ProductName'].apply(standardize_text)
products['Category'] = products['Category'].apply(standardize_text)

# 4.2. Apply SKU Normalization (Hyphen Removal)
products['SKU'] = products['SKU'].str.replace('-', '', regex=False)
print(products['SKU'].value_counts(dropna=False).head(10))

# 4.3. Apply ProductName Normalization (Regex and Manual Mapping)
# Remove the hyphen-space-Arabic pattern
products['ProductName'] = products['ProductName'].str.replace(r'\s+-\s*[ا-ي\s]+', '', regex=True)

# Apply specific manual replacements to the overwritten column
products['ProductName'] = products['ProductName'].replace({
    'bluetooth سماعة': 'bluetooth headphones',
    'puzzle 1000pcsأحجية': 'puzzle 1000pcs',
    'organic زيت زيتون 1l': 'organic olive oil 1l',
    'labtop i7 16gb': 'laptop i7 16gb'
})

# 4.4. Apply Category Normalization
products['Category'] = products['Category'].replace({
    'إلكترونيات': 'electronics',
    'electrnics': 'electronics'
})
print(products['Category'].value_counts(dropna=False))

# --- 4.5. Create Final Unique Lookup Table ---
# Drop duplicates based on the ProductName (the key you will use for merging).
products = products.drop_duplicates(subset=['ProductName'], keep='first')
#sku_lookup = products.drop_duplicates(subset=['ProductName'], keep='first')
#print(products['SKU'].value_counts(dropna=False))

#print(sku_lookup['ProductName'].value_counts(dropna=False))
#print(sku_lookup)

# --- 5. Direct Join for SKU Imputation ---
# --- 5. Direct Join for SKU Imputation ---

# 5.1. Perform the Left Merge
# NOTE: Renaming the columns in 5.5 now depends on this step's suffixes.
sales = pd.merge(
    sales,
    products[['ProductName', 'SKU']], # Only select Name (key) and SKU (value)
    how='left',
    left_on='ProductName_Clean', # This column is the join key from the LEFT table (sales)
    right_on='ProductName', # This column is the join key from the RIGHT table (products)
    suffixes=('_sales', '_imputed') #what it's use !!!!1
)

# 5.2. Identify the Nulls *before* filling (for the flag)
null_sku_mask = sales['ProductSKU_Clean'].isnull()

# 5.3. Fill Gaps in SKU (THE CRITICAL FIX: Assign the result back!)
sales['ProductSKU_Clean'] = sales['ProductSKU_Clean'].fillna(sales['SKU'])

# 5.4. Update the investigation flag
# Use the mask created in 5.2 to target only the rows that were originally null but are now filled.
sales.loc[null_sku_mask & sales['ProductSKU_Clean'].notna(), 'investigation_flag'] = 'SKU_Imputed_by_Name'

# 5.5. Cleanup: Drop the temporary columns created by the merge (FIXED)
# The temporary columns are: the copied join key ('ProductName') and the imputed value ('SKU').
# The suffix logic will rename 'ProductName' to 'ProductName_imputed', but 'SKU' remains 'SKU'.
# Based on your previous successful error check, the correct columns to drop are:
sales.drop(columns=['SKU', 'ProductName_imputed'], inplace=True)

print("\n✅ Missing SKUs imputed successfully. Category column was left untouched.")

# Check the null count again
print("\n--- Final Null Count in ProductSKU_Clean ---")
print(sales['ProductSKU_Clean'].value_counts(dropna=False).head())

#checking
#print("-------------")
#print(sales['ProductSKU'].value_counts(dropna=False))
#----------------------------

# -------------------------------------------------------------------------
# MONETARY COLUMNS CLEANING AND STANDARDIZATION
# -------------------------------------------------------------------------

# ---------------------------
# 1️⃣ Preview monetary columns
# ---------------------------
print(sales[['UnitPrice', 'Quantity', 'Subtotal', 'Discount', 'TotalAmount', 'Currency']].head(10))

# ---------------------------
# 2️⃣ Standardize currency variations
# ---------------------------
currency_map = {
    'ج.م': 'EGP',
    'EGP': 'EGP',
    'E£': 'EGP',
    'USD': 'USD',
}


def clean_currency(currency_str):
    """
    Standardizes different forms of currency to EGP or USD.
    """
    text = str(currency_str).upper()
    match = re.search(r'(EGP|USD|E£|ج\.م)', text)
    if match:
        code = match.group(0)
        return currency_map.get(code, code)
    return currency_str.upper()


sales['Currency_Clean'] = sales['Currency'].apply(clean_currency)
print(sales['Currency_Clean'].value_counts(dropna=False))

# ---------------------------
# 3️⃣ Apply FX rates
# ---------------------------
EGP_PER_USD = 45.3575  # average 2024


def get_fx_rate(currency):
    """Returns the exchange rate to EGP"""
    if currency == 'USD':
        return EGP_PER_USD
    return 1.0


sales['FX_Rate'] = sales['Currency_Clean'].apply(get_fx_rate)

# Standardize UnitPrice to EGP
sales['UnitPrice_EGP'] = sales['UnitPrice'] * sales['FX_Rate']

print("--- UnitPrice Standardization ---")
print(sales[['Currency_Clean', 'UnitPrice', 'FX_Rate', 'UnitPrice_EGP']].head())

# ---------------------------
# 4️⃣ Clean Quantity
# ---------------------------
invalid_qty_mask = sales['Quantity'] <= 0
sales['Quantity_Clean'] = sales['Quantity']
sales.loc[invalid_qty_mask, 'Quantity_Clean'] = np.nan
print(f"Remaining nulls in Quantity_Clean: {sales['Quantity_Clean'].isnull().sum()}")

# ---------------------------
# 5️⃣ Recalculate Subtotal
# ---------------------------
sales['Subtotal_Calc'] = sales['UnitPrice_EGP'] * sales['Quantity_Clean']
print(sales[['Subtotal', 'Subtotal_Calc']].head())

# ---------------------------
# 6️⃣ Standardize Discount
# ---------------------------
def standardize_discount(row):
    """Convert discounts to 0-1 rate using subtotal and FX"""
    discount = str(row['Discount']).strip()
    subtotal = row['Subtotal_Calc']

    # 0% for missing/invalid
    if pd.isna(discount) or discount.upper() in ('NONE', 'NAN', '0'):
        return 0.0

    # percentage
    if '%' in discount:
        try:
            return float(discount.replace('%', '')) / 100
        except:
            return 0.0

    # numeric
    try:
        val = float(discount)
    except:
        return 0.0

    # rate <1
    if val < 1.0:
        return val

    # fixed amount → convert to rate
    if pd.isna(subtotal) or subtotal == 0:
        return 0.0
    discount_egp = val * row['FX_Rate']
    rate = discount_egp / subtotal
    return min(rate, 1.0)


sales['Discount_Rate_Clean'] = sales.apply(standardize_discount, axis=1)

# ---------------------------
# 7️⃣ Identify and cap extreme UnitPrice outliers (per SKU)
# ---------------------------
# Compute 99th percentile per SKU
sku_99 = sales.groupby('ProductSKU_Clean')['UnitPrice_EGP'].quantile(0.99)


def cap_unitprice(row):
    threshold = sku_99[row['ProductSKU_Clean']]
    return min(row['UnitPrice_EGP'], threshold)


sales['UnitPrice_EGP_capped'] = sales.apply(cap_unitprice, axis=1)

# Recalculate subtotal after capping
sales['Subtotal_Calc_Capped'] = sales['UnitPrice_EGP_capped'] * sales['Quantity_Clean']

# ---------------------------
# 8️⃣ Quick visualization
# ---------------------------
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.boxplot(x='UnitPrice_EGP', data=sales)
plt.title("Before Capping")

plt.subplot(1, 2, 2)
sns.boxplot(x='UnitPrice_EGP_capped', data=sales)
plt.title("After Capping")
plt.show()

# ---------------------------
# ✅ Summary of new columns
# ---------------------------
print("New columns created:")
print([
    'Quantity_Clean',
    'UnitPrice_EGP',
    'UnitPrice_EGP_capped',
    'Subtotal_Calc',
    'Subtotal_Calc_Capped',
    'Discount_Rate_Clean',
    'Currency_Clean',
    'FX_Rate'
])

# 1️⃣ Basic stats before and after capping
print("--- UnitPrice_EGP Stats Before Capping ---")
print(sales['UnitPrice_EGP'].describe())

print("\n--- UnitPrice_EGP Stats After Capping ---")
print(sales['UnitPrice_EGP_capped'].describe())

# 2️⃣ Check top 10 highest prices before and after
print("\n--- Top 10 UnitPrice_EGP Before Capping ---")
print(sales['UnitPrice_EGP'].sort_values(ascending=False).head(10))

print("\n--- Top 10 UnitPrice_EGP After Capping ---")
print(sales['UnitPrice_EGP_capped'].sort_values(ascending=False).head(10))

# 3️⃣ Count of rows above the 99th percentile (to see how many were affected)
cap_value = sales['UnitPrice_EGP'].quantile(0.99)
print(f"\n99th percentile value (cap threshold): {cap_value}")

print("Number of rows above 99th percentile (before capping):", (sales['UnitPrice_EGP'] > cap_value).sum())
print("Number of rows above 99th percentile (after capping):", (sales['UnitPrice_EGP_capped'] > cap_value).sum())


#print(sales['TotalAmount'].value_counts(dropna=False).head(10))
#print(sales['ShippingCost'].value_counts(dropna=False).head(10))

#print(sales.head(15))


# -------------------------------------------------------------------------
# Inconsistency in COLUMNS (shipper) CLEANING AND STANDARDIZATION
# -------------------------------------------------------------------------

#---------------------------
#obeservationsssss
print(sales['ShippingCost'].unique())

print(
    sales.groupby('ShipperName_Clean')['ShippingCost']
         .median()
         .sort_values()
)

print(
    sales.groupby('Governorate_Clean')['ShippingCost']
         .median()
         .sort_values()
)

print(
    sales.groupby('City')['ShippingCost']
         .median()
         .sort_values()
)

#------------------

shipping_median_city = sales.groupby(
    ['Channel_Clean', 'ShipperName_Clean', 'Governorate_Clean', 'City']
)['ShippingCost'].median().reset_index()

print(shipping_median_city.sample(20))

#fill shipping cost

# 1️⃣ Calculate medians at different levels
median_level1 = sales.groupby(['ShipperName_Clean', 'Governorate_Clean', 'City'])['ShippingCost'].median()
median_level2 = sales.groupby(['ShipperName_Clean', 'City'])['ShippingCost'].median()
median_level3 = sales.groupby(['ShipperName_Clean', 'Governorate_Clean'])['ShippingCost'].median()
median_level4 = sales.groupby(['ShipperName_Clean'])['ShippingCost'].median()
global_median = sales['ShippingCost'].median()  # fallback if nothing else
print(f"Global median: {global_median}")

# 2️⃣ Define function to fill shipping cost per row
def fill_shipping_cost(row):
    # Treat NaN or 0 as missing
    if pd.notna(row['ShippingCost']) and row['ShippingCost'] != 0:
        return row['ShippingCost']

    # Level 1
    key1 = (row['ShipperName_Clean'], row['Governorate_Clean'], row['City'])
    val = median_level1.get(key1, np.nan)
    if pd.notna(val) and val != 0:
        return val

    # Level 2
    key2 = (row['ShipperName_Clean'], row['City'])
    val = median_level2.get(key2, np.nan)
    if pd.notna(val) and val != 0:
        return val

    # Level 3
    key3 = (row['ShipperName_Clean'], row['Governorate_Clean'])
    val = median_level3.get(key3, np.nan)
    if pd.notna(val) and val != 0:
        return val

    # Level 4
    key4 = row['ShipperName_Clean']
    val = median_level4.get(key4, np.nan)
    if pd.notna(val) and val != 0:
        return val

    # Last fallback: global median
    return global_median  # guaranteed number

# 3️⃣ Apply the function to fill missing shipping cost
sales['ShippingCost_Filled'] = sales.apply(fill_shipping_cost, axis=1)

# 4️⃣ Quick check
missing_before = sales['ShippingCost'].isna().sum()
missing_after = sales['ShippingCost_Filled'].isna().sum()
print(f"Missing before: {missing_before}")
print(f"Missing after: {missing_after}")

# 5️⃣ Optional: summary of fill levels
sales['fill_tracker'] = np.where(
    sales['ShippingCost'].notna(), 'original',
    np.where(sales['ShippingCost_Filled'].notna(), 'filled', 'still_missing')
)
print(sales['fill_tracker'].value_counts())


print(sales['ShippingCost_Filled'].value_counts())

#print(sales[sales['Channel_Clean'] == 'Store']['ShippingCost'].describe())

#observationssssssssssss
# Quick summary of shipping costs per channel
channel_summary = sales.groupby('Channel_Clean')['ShippingCost_Filled'].describe()
print(channel_summary)

# Count of unique shipping costs per channel
for channel in sales['Channel_Clean'].unique():
    print(f"\nChannel: {channel}")
    print(sales[sales['Channel_Clean'] == channel]['ShippingCost_Filled'].value_counts().sort_index())
#-----------------------


# Rows where ShippingCost is missing
#missing_shipping = sales[sales['ShippingCost'].isna()]
#print(missing_shipping[['OrderID_cleaned', 'Channel_Clean', 'ShipperName_Clean', 'Governorate_Clean', 'City', 'ShippingCost']])

# Show all related columns together for inspection
#print(sales.loc[mask_store_issue, ['OrderID_cleaned', 'Channel_Clean', 'ShipperName_Clean', 'ShippingCost']])

sales['TotalAmount_Calc'] = (sales['Subtotal_Calc_Capped'] * (1 - sales['Discount_Rate_Clean'])) + sales['ShippingCost_Filled']

print("total amout calcualted")
print(sales['TotalAmount_Calc'].describe())
print(sales['TotalAmount_Calc'].isna().sum())
print(sales['Subtotal_Calc_Capped'].isna().sum())
#print(sales['Quantity_Cleaned'].isna().sum())


# --- Distribution before cleaning ---
plt.figure(figsize=(12,6))
sns.histplot(sales['TotalAmount_Calc'], bins=50, kde=True)
plt.title('Distribution of TotalAmount_Calc')
plt.xlabel('Total Amount')
plt.ylabel('Count')
plt.show()

# --- Boxplot with log transformation to handle skew ---
plt.figure(figsize=(12,4))
sns.boxplot(x=np.log1p(sales['TotalAmount_Calc']))
plt.title('Log-transformed TotalAmount_Calc Boxplot')
plt.xlabel('Log(Total Amount + 1)')
plt.show()

# --- Identify extreme values using IQR ---
Q1 = sales['TotalAmount_Calc'].quantile(0.25)
Q3 = sales['TotalAmount_Calc'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

sales['TotalAmount_Extreme'] = (sales['TotalAmount_Calc'] < lower_bound) | (sales['TotalAmount_Calc'] > upper_bound)

# Summary of extreme values
print("Count of extreme orders:")
print(sales['TotalAmount_Extreme'].value_counts())

print("\nTop extreme orders:")
print(sales[sales['TotalAmount_Extreme']].sort_values('TotalAmount_Calc', ascending=False))

# --- Optional: visualize extreme vs normal orders ---
plt.figure(figsize=(12,6))
sns.histplot(sales[~sales['TotalAmount_Extreme']]['TotalAmount_Calc'], bins=50, color='blue', label='Normal', alpha=0.6)
sns.histplot(sales[sales['TotalAmount_Extreme']]['TotalAmount_Calc'], bins=50, color='red', label='Extreme', alpha=0.6)
plt.title('Normal vs Extreme TotalAmount_Calc')
plt.xlabel('Total Amount')
plt.ylabel('Count')
plt.legend()
plt.show()
#print(sales.head())

sales['Test_Subtotal'] = sales['UnitPrice_EGP_capped'] * sales['Quantity_Clean']
print( (sales['Test_Subtotal'] - sales['Subtotal_Calc_Capped']).abs().sum() )


print(sales.columns.tolist())

# -----------------------------------------
# CREATE BI-READY DATASET FOR DASHBOARDS
# -----------------------------------------

bi_columns = [
    'CustomerName_clean',  # <-- ADD THIS
    'OrderID_cleaned',
    'OrderDate','Order_Year','Order_Month','Order_Quarter','Order_YearMonth',
    'DeliveryDate','Delivery_Time_Days','Delivery_Delayed',
    'CustomerID_clean','CustomerName_clean','Gender_Clean',
    'Governorate_Clean','City',
    'ProductSKU_Clean','ProductName_Clean','Category_Clean',
    'Quantity_Clean','UnitPrice_EGP_capped',
    'Subtotal_Calc_Capped','Discount_Rate_Clean','ShippingCost_Filled','TotalAmount_Calc',
    'PaymentStatus_Clean','PaymentMethod_Clean','Channel_Clean','Status_Clean','ShipperName_Clean'
]

bi_sales = sales[bi_columns]

print("BI-ready dataset created and saved successfully.")
print("Shape:", bi_sales.shape)
print("Columns:", bi_sales.columns.tolist())

# Save file
output_path = "/Users/salmaabdelkader/PycharmProjects/RetailCaseStudy/BI_Ready_Sales_Dataset.xlsx"

bi_sales.to_excel(output_path, index=False)
print(f"BI-Ready dataset saved to: {output_path}")

# ============================================
# DATA QUALITY VALIDATION SUMMARY
# ============================================

print("\n" + "="*60)
print("DATA QUALITY VALIDATION SUMMARY")
print("="*60)

# 1. Uniqueness Check
print(f"\n1. UNIQUENESS:")
print(f"   Unique OrderID_cleaned: {sales['OrderID_cleaned'].nunique()}")
print(f"   Total rows: {len(sales)}")
print(f"   100% unique: {sales['OrderID_cleaned'].nunique() == len(sales)}")
print(f"   Original duplicated OrderIDs: {sales['is_OrderID_duplicated_flag'].sum()}")

# 2. Completeness Check
print(f"\n2. COMPLETENESS (Critical Fields):")
print(f"   OrderDate nulls: {sales['OrderDate'].isnull().sum()} ({sales['OrderDate'].isnull().sum()/len(sales)*100:.1f}%)")
print(f"   ProductSKU_Clean nulls: {sales['ProductSKU_Clean'].isnull().sum()} ({sales['ProductSKU_Clean'].isnull().sum()/len(sales)*100:.1f}%)")
print(f"   TotalAmount_Calc nulls: {sales['TotalAmount_Calc'].isnull().sum()} ({sales['TotalAmount_Calc'].isnull().sum()/len(sales)*100:.1f}%)")
print(f"   Quantity_Clean nulls: {sales['Quantity_Clean'].isnull().sum()} ({sales['Quantity_Clean'].isnull().sum()/len(sales)*100:.1f}%)")

# 3. Accuracy Check
print(f"\n3. ACCURACY (Calculations):")
subtotal_test = (sales['UnitPrice_EGP_capped'] * sales['Quantity_Clean'] - sales['Subtotal_Calc_Capped']).abs().sum()
print(f"   Subtotal calculation diff: {subtotal_test:.2f} (should be ~0)")
print(f"   Records with invalid dates: {sales['delivery_is_before_order'].sum()}")

# 4. Validity Check
print(f"\n4. VALIDITY (Business Rules):")
print(f"   Negative/Zero quantities (now NaN): {(sales['Quantity_Clean'] <= 0).sum()}")
print(f"   Delivery before order: {sales['delivery_is_before_order'].sum()}")
print(f"   Discount rate > 1: {(sales['Discount_Rate_Clean'] > 1).sum()}")
print(f"   Extreme TotalAmount (flagged): {sales['TotalAmount_Extreme'].sum()}")

# 5. Consistency Check
print(f"\n5. CONSISTENCY (Standardization):")
print(f"   Governorate variations: {sales['Governorate_Clean'].nunique()} (expected ~12-13)")
print(f"   Currency values: {list(sales['Currency_Clean'].unique())}")
print(f"   Gender values: {list(sales['Gender_Clean'].unique())}")
print(f"   ReturnFlag values: {list(sales['ReturnFlag_Clean'].unique())}")

# 6. Contact Information Quality
print(f"\n6. CONTACT INFORMATION:")
print(f"   Valid phones: {sales['phone_is_valid'].sum()} ({sales['phone_is_valid'].sum()/len(sales)*100:.1f}%)")
print(f"   Invalid phones: {(~sales['phone_is_valid']).sum()} ({(~sales['phone_is_valid']).sum()/len(sales)*100:.1f}%)")
print(f"   Valid emails: {sales['email_is_valid'].sum()} ({sales['email_is_valid'].sum()/len(sales)*100:.1f}%)")
print(f"   Invalid emails: {(~sales['email_is_valid']).sum()} ({(~sales['email_is_valid']).sum()/len(sales)*100:.1f}%)")

# 7. Geographic Data Quality
print(f"\n7. GEOGRAPHIC DATA:")
print(f"   Valid coordinates: {(sales['investigation_flag'] == 'Valid').sum()}")
print(f"   Imputed coordinates: {(sales['investigation_flag'] == 'Imputed_by_Location').sum()}")
print(f"   Still missing: {(sales['investigation_flag'] == 'Needs_Further_Investigation/Unknown').sum()}")
print(f"   Manually swapped: {(sales['investigation_flag'] == 'Manually Swapped').sum()}")

# 8. Data Quality Score Summary
print(f"\n8. OVERALL DATA QUALITY:")
completeness_score = (1 - sales[['OrderDate', 'ProductSKU_Clean', 'TotalAmount_Calc']].isnull().mean().mean()) * 100
print(f"   Completeness Score (critical fields): {completeness_score:.1f}%")
print(f"   Total records processed: {len(sales)}")
print(f"   Total columns in BI dataset: {len(bi_columns)}")

print("\n" + "="*60)
print("Validation complete! Check flags for rows requiring investigation.")
print("="*60 + "\n")

