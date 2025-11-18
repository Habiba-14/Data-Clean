# PART D: DATA WAREHOUSE MODEL DESIGN
## EG Retail Sales - Case Study 1

**Prepared by:** Salma Abdelkader  
**Date:** November 18, 2024  
**Purpose:** Star Schema design for retail sales data warehouse

---

## 1. DATA WAREHOUSE SCHEMA DESIGN

### 1.1 Schema Type Selection

**Chosen Schema: STAR SCHEMA**

**Rationale:**
- **Simplicity:** Easier to understand and query (single JOIN from fact to dimension)
- **Query Performance:** Faster queries due to fewer JOINs
- **Better for BI Tools:** Power BI, Tableau optimize for star schemas
- **Appropriate for Dataset:** No deep hierarchies requiring snowflake normalization
- **User-Friendly:** Business users can easily understand the model

**Alternative Considered:** Snowflake Schema
- **Rejected because:** Adds complexity without significant benefits for this dataset size
- **When to use:** Multi-level hierarchies (e.g., Product → Subcategory → Category → Department)

---

## 2. FACT TABLE DESIGN

### 2.1 Fact_Sales (Main Fact Table)

**Grain:** One row per order line item (one product per order)

**Purpose:** Captures transactional sales data with additive measures

#### Schema:

```sql
CREATE TABLE Fact_Sales (
    -- Primary Key
    SaleID                  INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Foreign Keys (Dimension References)
    OrderID_cleaned         VARCHAR(20) NOT NULL,
    DateKey                 INT NOT NULL,
    DeliveryDateKey         INT NULL,
    ReturnDateKey           INT NULL,
    CustomerKey             INT NULL,
    ProductKey              INT NOT NULL,
    LocationKey             INT NOT NULL,
    PaymentMethodKey        INT NOT NULL,
    PaymentStatusKey        INT NOT NULL,
    ShipperKey              INT NULL,
    ChannelKey              INT NOT NULL,
    StatusKey               INT NOT NULL,
    
    -- Measures (Numeric, Additive Facts)
    Quantity                DECIMAL(10,2),
    UnitPrice_EGP           DECIMAL(12,2),
    Subtotal_EGP            DECIMAL(12,2),
    Discount_Rate           DECIMAL(5,4),
    Discount_Amount_EGP     DECIMAL(12,2),
    ShippingCost_EGP        DECIMAL(10,2),
    TotalAmount_EGP         DECIMAL(12,2),
    
    -- Delivery Performance Measures
    Delivery_Time_Days      INT,
    Delivery_Delayed_Flag   BOOLEAN,
    
    -- Flags & Degenerate Dimensions
    is_OrderID_Duplicated   BOOLEAN,
    is_Return               BOOLEAN,
    Valid_Delivery_Flag     BOOLEAN,
    Valid_Return_Flag       BOOLEAN,
    Investigation_Flag      VARCHAR(50),  -- For data quality tracking
    
    -- Audit Fields
    Created_Date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_Date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (DateKey) REFERENCES Dim_Date(DateKey),
    FOREIGN KEY (DeliveryDateKey) REFERENCES Dim_Date(DateKey),
    FOREIGN KEY (ReturnDateKey) REFERENCES Dim_Date(DateKey),
    FOREIGN KEY (CustomerKey) REFERENCES Dim_Customer(CustomerKey),
    FOREIGN KEY (ProductKey) REFERENCES Dim_Product(ProductKey),
    FOREIGN KEY (LocationKey) REFERENCES Dim_Location(LocationKey),
    FOREIGN KEY (PaymentMethodKey) REFERENCES Dim_PaymentMethod(PaymentMethodKey),
    FOREIGN KEY (PaymentStatusKey) REFERENCES Dim_PaymentStatus(PaymentStatusKey),
    FOREIGN KEY (ShipperKey) REFERENCES Dim_Shipper(ShipperKey),
    FOREIGN KEY (ChannelKey) REFERENCES Dim_Channel(ChannelKey),
    FOREIGN KEY (StatusKey) REFERENCES Dim_Status(StatusKey),
    
    -- Indexes for Performance
    INDEX idx_order_id (OrderID_cleaned),
    INDEX idx_date (DateKey),
    INDEX idx_customer (CustomerKey),
    INDEX idx_product (ProductKey),
    INDEX idx_location (LocationKey)
);
```

#### Measures Definition:

| Measure | Type | Additivity | Description |
|---------|------|------------|-------------|
| Quantity | Decimal | ✅ Fully Additive | Units sold |
| UnitPrice_EGP | Decimal | ❌ Non-Additive | Price per unit (use AVG) |
| Subtotal_EGP | Decimal | ✅ Fully Additive | Quantity × UnitPrice |
| Discount_Rate | Decimal | ❌ Non-Additive | Discount as rate (0-1) |
| Discount_Amount_EGP | Decimal | ✅ Fully Additive | Actual discount value |
| ShippingCost_EGP | Decimal | ✅ Fully Additive | Shipping cost |
| TotalAmount_EGP | Decimal | ✅ Fully Additive | Final order amount |
| Delivery_Time_Days | Integer | ❌ Semi-Additive | Days to deliver (use AVG) |

---

## 3. DIMENSION TABLES DESIGN

### 3.1 Dim_Date (Date Dimension)

**Purpose:** Time intelligence for all date-based analysis

**Type:** Conformed Dimension (shared across all date foreign keys)

```sql
CREATE TABLE Dim_Date (
    DateKey                 INT PRIMARY KEY,        -- Format: YYYYMMDD (e.g., 20240115)
    Date                    DATE NOT NULL UNIQUE,
    
    -- Day Attributes
    DayOfWeek               INT,                    -- 1-7 (Monday-Sunday)
    DayName                 VARCHAR(10),            -- Monday, Tuesday, ...
    DayOfMonth              INT,                    -- 1-31
    DayOfYear               INT,                    -- 1-366
    
    -- Week Attributes
    WeekOfYear              INT,                    -- 1-53
    WeekStart               DATE,
    WeekEnd                 DATE,
    
    -- Month Attributes
    Month                   INT,                    -- 1-12
    MonthName               VARCHAR(10),            -- January, February, ...
    MonthAbbrev             VARCHAR(3),             -- Jan, Feb, ...
    YearMonth               VARCHAR(7),             -- 2024-01
    
    -- Quarter Attributes
    Quarter                 INT,                    -- 1-4
    QuarterName             VARCHAR(6),             -- Q1, Q2, Q3, Q4
    YearQuarter             VARCHAR(7),             -- 2024-Q1
    
    -- Year Attributes
    Year                    INT,                    -- 2024
    
    -- Fiscal Period (if different from calendar)
    FiscalQuarter           INT,
    FiscalYear              INT,
    
    -- Business Flags
    IsWeekend               BOOLEAN,
    IsHoliday               BOOLEAN,
    HolidayName             VARCHAR(50),
    IsLastDayOfMonth        BOOLEAN,
    IsFirstDayOfMonth       BOOLEAN,
    
    -- Indexes
    INDEX idx_date (Date),
    INDEX idx_year_month (Year, Month),
    INDEX idx_year_quarter (Year, Quarter)
);
```

**Sample Records:**
```
DateKey    | Date       | DayName | Month | Quarter | Year | YearMonth
-----------|------------|---------|-------|---------|------|----------
20240115   | 2024-01-15 | Monday  | 1     | 1       | 2024 | 2024-01
20240116   | 2024-01-16 | Tuesday | 1     | 1       | 2024 | 2024-01
```

---

### 3.2 Dim_Customer (Customer Dimension)

**Purpose:** Store customer demographic and contact information

**Type:** Slowly Changing Dimension (SCD) Type 2 recommended

```sql
CREATE TABLE Dim_Customer (
    CustomerKey             INT PRIMARY KEY AUTO_INCREMENT,  -- Surrogate Key
    CustomerID              VARCHAR(20),                     -- Natural Key (Business Key)
    
    -- Customer Information
    CustomerName            VARCHAR(100),
    Gender                  VARCHAR(20),                     -- Male, Female, Not Specified
    
    -- Contact Information
    Phone                   VARCHAR(20),
    Email                   VARCHAR(100),
    
    -- Location (Denormalized for performance)
    Governorate             VARCHAR(50),
    City                    VARCHAR(50),
    Address                 TEXT,
    
    -- Customer Segmentation (Derived Attributes)
    CustomerSegment         VARCHAR(20),                     -- VIP, Regular, New
    CustomerLifetimeValue   DECIMAL(12,2),
    
    -- Data Quality Flags
    Phone_IsValid           BOOLEAN,
    Email_IsValid           BOOLEAN,
    
    -- SCD Type 2 Attributes
    Effective_Date          DATE,
    Expiration_Date         DATE,
    Is_Current              BOOLEAN DEFAULT TRUE,
    
    -- Audit
    Created_Date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_Date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    UNIQUE INDEX idx_customer_id_current (CustomerID, Is_Current),
    INDEX idx_customer_name (CustomerName),
    INDEX idx_governorate (Governorate)
);
```

**SCD Type 2 Example:**
```
CustomerKey | CustomerID | CustomerName | Phone          | Effective_Date | Expiration_Date | Is_Current
------------|------------|--------------|----------------|----------------|-----------------|------------
1           | C001       | Ahmed Ali    | +201234567890  | 2024-01-01     | 2024-06-30      | FALSE
2           | C001       | Ahmed Ali    | +201098765432  | 2024-07-01     | 9999-12-31      | TRUE
```

---

### 3.3 Dim_Product (Product Dimension)

**Purpose:** Store product catalog information

**Type:** Slowly Changing Dimension Type 2

```sql
CREATE TABLE Dim_Product (
    ProductKey              INT PRIMARY KEY AUTO_INCREMENT,  -- Surrogate Key
    ProductSKU              VARCHAR(20) NOT NULL,            -- Natural Key
    
    -- Product Information
    ProductName             VARCHAR(200) NOT NULL,
    Category                VARCHAR(50),
    
    -- Product Attributes (Future enhancements)
    Brand                   VARCHAR(50),
    Supplier                VARCHAR(100),
    UnitCost                DECIMAL(10,2),                   -- For margin analysis
    Weight_KG               DECIMAL(8,2),
    Dimensions              VARCHAR(50),                     -- L×W×H
    
    -- Product Lifecycle
    ProductStatus           VARCHAR(20),                     -- Active, Discontinued, Seasonal
    LaunchDate              DATE,
    DiscontinuedDate        DATE,
    
    -- SCD Type 2
    Effective_Date          DATE,
    Expiration_Date         DATE,
    Is_Current              BOOLEAN DEFAULT TRUE,
    
    -- Indexes
    UNIQUE INDEX idx_product_sku_current (ProductSKU, Is_Current),
    INDEX idx_product_name (ProductName),
    INDEX idx_category (Category)
);
```

---

### 3.4 Dim_Location (Location Dimension)

**Purpose:** Store geographic information for analysis and mapping

**Type:** Type 1 SCD (overwrite changes)

```sql
CREATE TABLE Dim_Location (
    LocationKey             INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Geographic Hierarchy (Denormalized)
    Governorate             VARCHAR(50) NOT NULL,
    City                    VARCHAR(50),
    Address                 TEXT,
    
    -- Coordinates
    Latitude                DECIMAL(10,8),
    Longitude               DECIMAL(11,8),
    
    -- Data Quality Flags
    Coordinates_Valid       BOOLEAN,
    Coordinates_Imputed     BOOLEAN,
    Investigation_Flag      VARCHAR(50),
    
    -- Geographic Attributes (for analysis)
    Region                  VARCHAR(50),                     -- North, South, Delta, etc.
    DistanceFromCairo_KM    INT,                            -- For logistics
    
    -- Indexes
    INDEX idx_governorate (Governorate),
    INDEX idx_city (City),
    INDEX idx_coordinates (Latitude, Longitude)
);
```

---

### 3.5 Dim_PaymentMethod (Payment Method Dimension)

**Purpose:** Store payment method types

**Type:** Type 1 SCD

```sql
CREATE TABLE Dim_PaymentMethod (
    PaymentMethodKey        INT PRIMARY KEY AUTO_INCREMENT,
    PaymentMethodCode       VARCHAR(10) UNIQUE,              -- COD, VISA, MEEZA, FAWRY
    PaymentMethodName       VARCHAR(50),                     -- Cash on Delivery, Visa, etc.
    PaymentType             VARCHAR(20),                     -- Cash, Card, Digital Wallet
    
    -- Attributes
    RequiresPrePayment      BOOLEAN,
    TransactionFee_Percent  DECIMAL(5,2),
    
    INDEX idx_code (PaymentMethodCode)
);
```

---

### 3.6 Dim_PaymentStatus (Payment Status Dimension)

**Purpose:** Track payment lifecycle

**Type:** Type 1 SCD

```sql
CREATE TABLE Dim_PaymentStatus (
    PaymentStatusKey        INT PRIMARY KEY AUTO_INCREMENT,
    PaymentStatusCode       VARCHAR(10) UNIQUE,              -- PAID, UNPAID, PENDING, REFUNDED
    PaymentStatusName       VARCHAR(50),
    
    -- Business Logic
    IsPaymentComplete       BOOLEAN,
    AllowsShipment          BOOLEAN,
    
    INDEX idx_code (PaymentStatusCode)
);
```

---

### 3.7 Dim_Shipper (Shipper/Logistics Dimension)

**Purpose:** Store shipping company information

**Type:** Type 1 SCD

```sql
CREATE TABLE Dim_Shipper (
    ShipperKey              INT PRIMARY KEY AUTO_INCREMENT,
    ShipperCode             VARCHAR(10) UNIQUE,
    ShipperName             VARCHAR(100),
    
    -- Shipper Attributes
    ServiceLevel            VARCHAR(20),                     -- Standard, Express, Same-Day
    AvgDeliveryTime_Days    DECIMAL(4,1),
    CoverageArea            VARCHAR(100),                    -- Nationwide, Cairo only, etc.
    
    INDEX idx_shipper_code (ShipperCode)
);
```

---

### 3.8 Dim_Channel (Sales Channel Dimension)

**Purpose:** Track order source channels

**Type:** Type 1 SCD

```sql
CREATE TABLE Dim_Channel (
    ChannelKey              INT PRIMARY KEY AUTO_INCREMENT,
    ChannelCode             VARCHAR(10) UNIQUE,              -- ECOM, STORE, WHATSAPP, TELESALES
    ChannelName             VARCHAR(50),
    
    -- Channel Attributes
    IsOnline                BOOLEAN,
    RequiresShipping        BOOLEAN,
    
    INDEX idx_channel_code (ChannelCode)
);
```

---

### 3.9 Dim_Status (Order Status Dimension)

**Purpose:** Track order lifecycle status

**Type:** Type 1 SCD

```sql
CREATE TABLE Dim_Status (
    StatusKey               INT PRIMARY KEY AUTO_INCREMENT,
    StatusCode              VARCHAR(20) UNIQUE,
    StatusName              VARCHAR(50),
    StatusDescription       TEXT,
    
    -- Workflow
    StatusOrder             INT,                             -- 1=Pending, 2=Confirmed, 3=Shipped, etc.
    IsFinalStatus           BOOLEAN,
    
    INDEX idx_status_code (StatusCode)
);
```

---

## 4. STAR SCHEMA DIAGRAM

```
                                    ┌─────────────────┐
                                    │   Dim_Date      │
                                    ├─────────────────┤
                                    │ DateKey (PK)    │
                                    │ Date            │
                                    │ Year            │
                                    │ Quarter         │
                                    │ Month           │
                                    │ Week            │
                                    │ DayOfWeek       │
                                    └────────┬────────┘
                                             │
                                             │
         ┌───────────────┐                   │
         │ Dim_Customer  │                   │
         ├───────────────┤                   │
         │ CustomerKey   │                   │
         │ CustomerID    │                   │
         │ CustomerName  │                   │
         │ Gender        │◄───┐              │
         │ Phone         │    │              │
         │ Email         │    │              │
         └───────────────┘    │              │
                              │              │
                              │              │
         ┌───────────────┐    │              │
         │ Dim_Product   │    │              │
         ├───────────────┤    │              │
         │ ProductKey    │    │              │
         │ ProductSKU    │    │              │
         │ ProductName   │◄───┤              │
         │ Category      │    │              │
         └───────────────┘    │              │
                              │              │
                              │              │
         ┌───────────────┐    │   ┌──────────┴──────────┐
         │ Dim_Location  │    │   │    Fact_Sales       │
         ├───────────────┤    │   ├─────────────────────┤
         │ LocationKey   │    ├───┤ SaleID (PK)         │
         │ Governorate   │◄───┤   │                     │
         │ City          │    │   │ OrderID_cleaned     │
         │ Latitude      │    │   │ DateKey (FK)        │
         │ Longitude     │    │   │ CustomerKey (FK)    │
         └───────────────┘    │   │ ProductKey (FK)     │
                              │   │ LocationKey (FK)    │
                              │   │ ...                 │
         ┌─────────────────┐  │   │                     │
         │ Dim_PaymentMeth │  │   │ Quantity            │
         ├─────────────────┤  ├───┤ UnitPrice_EGP       │
         │ PaymentMethodKey│◄─┤   │ Subtotal_EGP        │
         │ MethodName      │  │   │ Discount_Amount     │
         └─────────────────┘  │   │ ShippingCost_EGP    │
                              │   │ TotalAmount_EGP     │
                              │   │                     │
         ┌─────────────────┐  │   │ Delivery_Time_Days  │
         │ Dim_PaymentStat │  │   └─────────────────────┘
         ├─────────────────┤  │              │
         │ PaymentStatusKey│◄─┤              │
         │ StatusName      │  │              │
         └─────────────────┘  │              │
                              │              │
                              │              │
         ┌───────────────┐    │              │
         │ Dim_Shipper   │    │              │
         ├───────────────┤    │              │
         │ ShipperKey    │◄───┤              │
         │ ShipperName   │    │              │
         └───────────────┘    │              │
                              │              │
                              │              │
         ┌───────────────┐    │              │
         │ Dim_Channel   │    │              │
         ├───────────────┤    │              │
         │ ChannelKey    │◄───┤              │
         │ ChannelName   │    │              │
         └───────────────┘    │              │
                              │              │
                              │              │
         ┌───────────────┐    │              │
         │ Dim_Status    │    │              │
         ├───────────────┤    │              │
         │ StatusKey     │◄───┘              │
         │ StatusName    │                   │
         └───────────────┘                   │
                                             │
                                             │
                                  (Additional date FKs:
                                   DeliveryDateKey,
                                   ReturnDateKey)
```

---

## 5. ETL PROCESS DESIGN

### 5.1 ETL Overview

**Tool Options:**
1. **Python Script** (Current implementation - Ready!)
2. **SQL Server Integration Services (SSIS)** (Recommended for production)
3. **Apache Airflow** (For cloud/modern data stack)
4. **Talend / Informatica** (Enterprise ETL tools)

### 5.2 ETL Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                     ETL PROCESS FLOW                           │
└────────────────────────────────────────────────────────────────┘

1. EXTRACT
   ├── Source: Excel File (EG_Retail_Sales_Raw_CaseStudy 1.xlsx)
   ├── Sheets: Sales_Orders_Raw, Products_Raw, Governorates, Customers
   └── Load into Pandas DataFrames

2. TRANSFORM (Data Cleaning - Already Implemented!)
   ├── OrderID: Create unique IDs, flag duplicates
   ├── Dates: Parse mixed formats, validate logic
   ├── Customer: Clean name, gender, phone, email
   ├── Location: Standardize governorates, validate coordinates
   ├── Products: Standardize SKU/Name/Category
   ├── Monetary: Convert currencies, calculate fields
   ├── Flags: Add data quality flags
   └── Output: Cleaned DataFrames

3. LOAD (Dimension & Fact Loading)
   
   3.1 Load Dimensions (in order):
       ├── Dim_Date (pre-populate calendar table)
       ├── Dim_Customer (from cleaned customer data)
       ├── Dim_Product (from cleaned products)
       ├── Dim_Location (from cleaned location data)
       ├── Dim_PaymentMethod (lookup table)
       ├── Dim_PaymentStatus (lookup table)
       ├── Dim_Shipper (lookup table)
       ├── Dim_Channel (lookup table)
       └── Dim_Status (lookup table)
   
   3.2 Load Fact Table:
       ├── Join cleaned sales data with dimension tables
       ├── Retrieve surrogate keys for foreign keys
       ├── Calculate derived measures
       └── Insert into Fact_Sales

4. VALIDATE
   ├── Row counts match source
   ├── Foreign key integrity checks
   ├── Measure sum validation
   └── Data quality report
```

---

### 5.3 Python ETL Implementation (Sample)

```python
# ==================================================
# ETL Script: Load Star Schema from Cleaned Data
# ==================================================

import pandas as pd
from sqlalchemy import create_engine

# Database connection
engine = create_engine('mysql+pymysql://user:password@localhost/retail_dw')

# --------------------------------------------------
# STEP 1: LOAD CLEANED DATA
# --------------------------------------------------
bi_sales = pd.read_excel("BI_Ready_Sales_Dataset.xlsx")

# --------------------------------------------------
# STEP 2: LOAD DIMENSION TABLES
# --------------------------------------------------

# 2.1 Dim_Date (Pre-populate)
date_range = pd.date_range(start='2024-01-01', end='2024-12-31')
dim_date = pd.DataFrame({
    'DateKey': date_range.strftime('%Y%m%d').astype(int),
    'Date': date_range,
    'Year': date_range.year,
    'Quarter': date_range.quarter,
    'Month': date_range.month,
    'MonthName': date_range.strftime('%B'),
    'DayOfWeek': date_range.dayofweek + 1,
    'DayName': date_range.strftime('%A'),
    'WeekOfYear': date_range.isocalendar().week,
    'IsWeekend': date_range.dayofweek >= 5
})
dim_date.to_sql('Dim_Date', engine, if_exists='replace', index=False)

# 2.2 Dim_Customer
dim_customer = bi_sales[['CustomerID_clean', 'CustomerName_clean', 'Gender_Clean', 
                         'Governorate_Clean', 'City']].drop_duplicates()
dim_customer = dim_customer.reset_index(drop=True)
dim_customer['CustomerKey'] = range(1, len(dim_customer) + 1)
dim_customer.to_sql('Dim_Customer', engine, if_exists='replace', index=False)

# 2.3 Dim_Product
dim_product = bi_sales[['ProductSKU_Clean', 'ProductName_Clean', 
                        'Category_Clean']].drop_duplicates()
dim_product = dim_product.reset_index(drop=True)
dim_product['ProductKey'] = range(1, len(dim_product) + 1)
dim_product.to_sql('Dim_Product', engine, if_exists='replace', index=False)

# 2.4 Dim_Location (Unique combinations of Governorate + City)
dim_location = bi_sales[['Governorate_Clean', 'City']].drop_duplicates()
dim_location = dim_location.reset_index(drop=True)
dim_location['LocationKey'] = range(1, len(dim_location) + 1)
dim_location.to_sql('Dim_Location', engine, if_exists='replace', index=False)

# 2.5 Dim_PaymentMethod
dim_payment_method = bi_sales[['PaymentMethod_Clean']].drop_duplicates()
dim_payment_method['PaymentMethodKey'] = range(1, len(dim_payment_method) + 1)
dim_payment_method.to_sql('Dim_PaymentMethod', engine, if_exists='replace', index=False)

# (Similar for other lookup dimensions...)

# --------------------------------------------------
# STEP 3: LOAD FACT TABLE
# --------------------------------------------------

# Join to get surrogate keys
fact_sales = bi_sales.copy()

# Merge with Customer dimension to get CustomerKey
fact_sales = fact_sales.merge(
    dim_customer[['CustomerID_clean', 'CustomerKey']], 
    on='CustomerID_clean', 
    how='left'
)

# Merge with Product dimension to get ProductKey
fact_sales = fact_sales.merge(
    dim_product[['ProductSKU_Clean', 'ProductKey']], 
    on='ProductSKU_Clean', 
    how='left'
)

# Merge with Location dimension to get LocationKey
fact_sales = fact_sales.merge(
    dim_location[['Governorate_Clean', 'City', 'LocationKey']], 
    on=['Governorate_Clean', 'City'], 
    how='left'
)

# (Continue for all dimension keys...)

# Select fact table columns
fact_columns = [
    'OrderID_cleaned', 'CustomerKey', 'ProductKey', 'LocationKey',
    'Quantity_Clean', 'UnitPrice_EGP_capped', 'Subtotal_Calc_Capped',
    'Discount_Rate_Clean', 'ShippingCost_Filled', 'TotalAmount_Calc',
    'Delivery_Time_Days', 'Delivery_Delayed'
]

fact_final = fact_sales[fact_columns]

# Load to database
fact_final.to_sql('Fact_Sales', engine, if_exists='replace', index=False)

print("✅ ETL Complete!")
```

---

### 5.4 SSIS Implementation Approach

**For production-grade ETL, SSIS package would include:**

1. **Control Flow:**
   - Execute SQL Task: Truncate staging tables
   - Data Flow Task: Load Dimensions (sequential)
   - Data Flow Task: Load Fact (after dimensions)
   - Execute SQL Task: Update statistics
   - Execute SQL Task: Generate data quality report

2. **Data Flow Components:**
   - **Source:** Excel Source → Read raw files
   - **Transformations:**
     - Derived Column (for calculations)
     - Lookup (to get dimension surrogate keys)
     - Data Conversion (data types)
     - Conditional Split (for error handling)
   - **Destination:** OLE DB Destination → SQL Server

3. **Error Handling:**
   - Redirect error rows to staging tables
   - Log errors to audit table
   - Email notification on failure

4. **Performance Optimization:**
   - Bulk insert for large fact tables
   - Parallel dimension loading
   - Incremental load (detect changes)

---

## 6. SAMPLE QUERIES (Analytics Use Cases)

### 6.1 Total Revenue by Month

```sql
SELECT 
    d.YearMonth,
    SUM(f.TotalAmount_EGP) AS Total_Revenue,
    COUNT(DISTINCT f.OrderID_cleaned) AS Order_Count,
    AVG(f.TotalAmount_EGP) AS Avg_Order_Value
FROM Fact_Sales f
JOIN Dim_Date d ON f.DateKey = d.DateKey
GROUP BY d.YearMonth
ORDER BY d.YearMonth;
```

### 6.2 Top 10 Products by Revenue

```sql
SELECT 
    p.ProductName,
    p.Category,
    SUM(f.TotalAmount_EGP) AS Total_Revenue,
    SUM(f.Quantity) AS Total_Units_Sold
FROM Fact_Sales f
JOIN Dim_Product p ON f.ProductKey = p.ProductKey
GROUP BY p.ProductName, p.Category
ORDER BY Total_Revenue DESC
LIMIT 10;
```

### 6.3 Customer Lifetime Value (Top 20 Customers)

```sql
SELECT 
    c.CustomerName,
    c.Governorate,
    COUNT(DISTINCT f.OrderID_cleaned) AS Total_Orders,
    SUM(f.TotalAmount_EGP) AS Lifetime_Value,
    AVG(f.TotalAmount_EGP) AS Avg_Order_Value,
    MAX(d.Date) AS Last_Purchase_Date
FROM Fact_Sales f
JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey
JOIN Dim_Date d ON f.DateKey = d.DateKey
GROUP BY c.CustomerName, c.Governorate
ORDER BY Lifetime_Value DESC
LIMIT 20;
```

### 6.4 Delivery Performance by Governorate

```sql
SELECT 
    l.Governorate,
    AVG(f.Delivery_Time_Days) AS Avg_Delivery_Days,
    SUM(CASE WHEN f.Delivery_Delayed_Flag = TRUE THEN 1 ELSE 0 END) AS Delayed_Orders,
    COUNT(*) AS Total_Orders,
    (SUM(CASE WHEN f.Delivery_Delayed_Flag = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS Delay_Rate_Percent
FROM Fact_Sales f
JOIN Dim_Location l ON f.LocationKey = l.LocationKey
GROUP BY l.Governorate
ORDER BY Delay_Rate_Percent DESC;
```

### 6.5 Revenue at Risk (Unpaid Orders)

```sql
SELECT 
    ps.PaymentStatusName,
    COUNT(*) AS Order_Count,
    SUM(f.TotalAmount_EGP) AS Total_Amount,
    (SUM(f.TotalAmount_EGP) * 100.0 / (SELECT SUM(TotalAmount_EGP) FROM Fact_Sales)) AS Percent_of_Total_Revenue
FROM Fact_Sales f
JOIN Dim_PaymentStatus ps ON f.PaymentStatusKey = ps.PaymentStatusKey
GROUP BY ps.PaymentStatusName
ORDER BY Total_Amount DESC;
```

### 6.6 Channel Performance Comparison

```sql
SELECT 
    ch.ChannelName,
    COUNT(DISTINCT f.OrderID_cleaned) AS Orders,
    SUM(f.TotalAmount_EGP) AS Revenue,
    AVG(f.TotalAmount_EGP) AS AOV,
    AVG(f.Delivery_Time_Days) AS Avg_Delivery_Time
FROM Fact_Sales f
JOIN Dim_Channel ch ON f.ChannelKey = ch.ChannelKey
GROUP BY ch.ChannelName
ORDER BY Revenue DESC;
```

---

## 7. DATA WAREHOUSE BENEFITS

| Benefit | Description | Business Impact |
|---------|-------------|-----------------|
| **Single Source of Truth** | Centralized, cleaned data | Eliminate conflicting reports |
| **Historical Tracking** | SCD preserves data history | Track changes over time |
| **Fast Queries** | Star schema optimized | 10x faster than OLTP queries |
| **Easy BI Integration** | Standard schema for tools | Power BI, Tableau connect easily |
| **Data Quality** | Validated during ETL | Trustworthy analytics |
| **Scalability** | Designed for growth | Handle millions of records |
| **Business Logic** | Encoded in DW structure | Consistent calculations |

---

## 8. NEXT STEPS & RECOMMENDATIONS

### 8.1 Immediate Actions

1. **Create Database:**
   ```sql
   CREATE DATABASE Retail_DW;
   ```

2. **Execute DDL Scripts:**
   - Run table creation scripts (provided above)
   - Add indexes and constraints

3. **Run ETL Script:**
   - Execute Python ETL script (already created in `Retail_Sales_Cleaned.py`)
   - Validate data loaded successfully

4. **Connect BI Tool:**
   - Connect Power BI / Tableau to data warehouse
   - Build initial dashboards

### 8.2 Phase 2 Enhancements

1. **Implement Incremental Load:**
   - Add ETL logic to process only new/changed records
   - Add `Last_Updated` timestamps

2. **Add More Dimensions:**
   - Dim_Product_Category (snowflake if needed)
   - Dim_Time (separate from Dim_Date for hourly analysis)
   - Dim_Promotion (track discounts and campaigns)

3. **Add Aggregate Tables:**
   - Monthly summary facts for performance
   - Pre-calculated KPIs

4. **Implement Data Quality Monitoring:**
   - Automated DQ checks in ETL
   - Data quality dashboard

---

**END OF PART D DESIGN**

