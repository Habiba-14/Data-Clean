# PART D: DATA WAREHOUSE DESIGN - STAR SCHEMA
## EG Retail Sales Case Study

**Prepared by:** Salma Abdelkader  
**Date:** November 18, 2024

---

## TABLE OF CONTENTS

1. [Understanding the Fact Table](#1-understanding-the-fact-table)
   - What is a Fact Table?
   - How to Identify a Fact Table
   - Our Fact Table Design

2. [Why Star Schema?](#2-why-star-schema)
   - Star Schema Structure
   - When to Use Star Schema
   - Advantages of Star Schema

3. [Problems Solved by Star Schema](#3-problems-solved-by-star-schema)
   - Problem 1: Data Redundancy
   - Problem 2: Inconsistent Data
   - Problem 3: Slow Queries
   - Summary: Problems Solved

4. [Star Schema Design Overview](#4-star-schema-design-overview)
   - Schema Details
   - Star Schema Diagram

5. [Fact and Dimension Tables](#5-fact-and-dimension-tables)
   - Fact_Sales (Main Transaction Table)
   - Dimension Tables (9 Total)

6. [Business Questions Answered](#6-business-questions-answered)
   - What are total sales by month?
   - Who are my top 10 customers?
   - Which products sell best in Cairo?
   - What's average delivery time by shipper?
   - Revenue at risk from unpaid orders?
   - Why These Queries Run Fast

7. [ETL Process](#7-etl-process-extract-transform-load)
   - Extract
   - Transform
   - Load

8. [Benefits Summary](#8-benefits-summary)
   - Business Benefits
   - Technical Benefits

9. [Conclusion](#conclusion)

---

## 1. UNDERSTANDING THE FACT TABLE

### What is a Fact Table?

The **FACT table** is chosen based on **what business process you want to analyze**.

**Simple Rule:** The FACT table stores **EVENTS** or **TRANSACTIONS** - things that HAPPEN and can be MEASURED.

### How to Identify a Fact Table

Ask yourself three key questions:

**Question 1: "What is the business activity we want to track?"**
- In our case: **SALES** (the act of selling a product)

**Question 2: "What can we COUNT or ADD UP?"**
- Quantity sold
- Money earned  
- Discounts given
- These become your **MEASURES** in the fact table

**Question 3: "What happens repeatedly?"**
- Sales happen many times per day
- Each sale is **ONE ROW** in the fact table

### Our Fact Table Design

- Each row represents **ONE SALE** (one product sold in one order)
- This becomes the **Fact_Sales** table
- Contains measures: **Quantity, UnitPrice, TotalAmount, Discount**

---

## 2. WHY STAR SCHEMA?

### Star Schema Structure

Star Schema has **one fact table** in the center with **dimension tables** directly connected:

```
         [Customer]       [Product]
              ↓               ↓
         [FACT_SALES TABLE]
              ↓               ↓
         [Location]        [Date]
```

### When to Use Star Schema

Star Schema is ideal when you have:

✅ **Simple data** (like our retail sales dataset)  
✅ **Performance is priority** (need fast queries for dashboards)  
✅ **Business users need to query** (must be easy to understand)  
✅ **BI tools** (Power BI and Tableau work best with star schemas)

### Advantages of Star Schema

- **Fastest queries** - Fewer JOIN operations needed
- **Easy to understand** - Simple structure for business users
- **Simple maintenance** - Easy to modify and extend
- **Best for reporting** - Optimized for business intelligence tools

---

## 3. PROBLEMS SOLVED BY STAR SCHEMA

### Problem 1: Data Redundancy

**BEFORE (Excel - Messy):**

| OrderID | CustomerName | Phone         | Product  | Price |
|---------|--------------|---------------|----------|-------|
| ORD-001 | Ahmed Ali    | +201234567890 | Laptop   | 15000 |
| ORD-002 | Ahmed Ali    | +201234567890 | Mouse    | 500   |
| ORD-003 | Ahmed Ali    | +201234567890 | Keyboard | 800   |

**Issues:**
- ❌ "Ahmed Ali" written 3 times (repeated 10x if he makes 10 orders!)
- ❌ Phone number written 3 times
- ❌ Wastes storage space, difficult to update

**AFTER (Star Schema - Clean):**

**Fact_Sales Table:**
| SaleID | CustomerKey | ProductKey | Price |
|--------|-------------|------------|-------|
| 1      | C001        | P001       | 15000 |
| 2      | C001        | P002       | 500   |
| 3      | C001        | P003       | 800   |

**Dim_Customer Table (stored ONCE):**
| CustomerKey | Name      | Phone         |
|-------------|-----------|---------------|
| C001        | Ahmed Ali | +201234567890 |

**Solution:**
- ✅ Ahmed's information stored **ONCE** only
- ✅ Update phone in **ONE place** - no errors
- ✅ Saves significant storage space

---

### Problem 2: Inconsistent Data

**BEFORE (Excel):**
- Same customer entered 4 different ways:
  - "Ahmed Ali"
  - "ahmed ali"
  - "Ahmed  Ali" (extra space)
  - "أحمد علي" (Arabic)

**AFTER (Star Schema with ETL):**
- During data loading (ETL), we **standardize** to "ahmed ali"
- Create **ONE customer record** only
- All sales correctly linked to same customer

---

### Problem 3: Slow Queries

**BEFORE (Excel):**
- Excel must **scan ALL 150 rows** for every query
- Searches through repeated data
- Gets slower as data grows

**AFTER (Star Schema):**
- Database uses **indexes** for fast lookup
- Queries run **10-100x faster**
- Performance stays good even with millions of rows

---

### Summary: Problems Solved

| Problem        | Excel (Before)       | Star Schema (After) | Benefit Gained        |
|----------------|----------------------|---------------------|-----------------------|
| Redundancy     | Ahmed's name 10 times| Stored once         | 90% space saving      |
| Inconsistency  | 4 different spellings| Standardized        | Accurate reports      |
| Performance    | Slow queries         | Fast queries        | 10x faster            |
| Analysis       | Complex formulas     | Simple SQL          | Easy to query         |
| Updates        | Change 10 rows       | Change 1 row        | No errors             |

---

## 4. STAR SCHEMA DESIGN OVERVIEW

### Schema Details

- **Schema Type:** Star Schema
- **Total Tables:** 10 tables
  - **1 Fact Table:** Fact_Sales (transactions)
  - **9 Dimension Tables:** Customer, Product, Date, Location, Payment Method, Payment Status, Shipper, Channel, Status
- **Granularity:** One row per sale transaction

### Star Schema Diagram

```
                      Dim_Date
                    (When - Calendar)
                           |
                           |
    Dim_Customer ----------|---------- Dim_Product
    (Who bought)           |           (What was sold)
                           |
                           ↓
                    ╔═════════════╗
                    ║ FACT_SALES  ║  ← Center of Star
                    ║ (Measures)  ║
                    ╚═════════════╝
                           ↑
                           |
    Dim_Location ----------|---------- Dim_PaymentMethod
    (Where shipped)        |           (How paid)
                           |
                      Dim_Channel
                    (Order source)

            + Dim_PaymentStatus
            + Dim_Shipper  
            + Dim_Status
```

---

## 5. FACT AND DIMENSION TABLES

### Fact_Sales (Main Transaction Table)

**Purpose:** Store all sales transactions with measurable values

**Contains:**
- **Keys:** Links to all 9 dimension tables
- **Measures:** 
  - Quantity (items sold)
  - UnitPrice (price per item)
  - Subtotal (quantity × price)
  - Discount (discount applied)
  - ShippingCost (shipping charge)
  - TotalAmount (final amount)
  - Delivery_Time_Days (delivery time)
- **Flags:** 
  - Delivery_Delayed (Yes/No)
  - Return indicators
  - Data quality flags

### Dimension Tables (9 Total)

1. **Dim_Date** - Calendar information (Year, Month, Quarter, Day)
2. **Dim_Customer** - Customer details (Name, Phone, Email, Gender)
3. **Dim_Product** - Product catalog (SKU, Name, Category)
4. **Dim_Location** - Geographic data (Governorate, City, Coordinates)
5. **Dim_PaymentMethod** - Payment types (Cash, Visa, Fawry)
6. **Dim_PaymentStatus** - Payment state (Paid, Unpaid, Pending)
7. **Dim_Shipper** - Delivery companies (Aramex, Egypt Post)
8. **Dim_Channel** - Order source (E-com, Store, WhatsApp, Tel-Sales)
9. **Dim_Status** - Order status (Pending, Shipped, Delivered, Cancelled)

---

## 6. BUSINESS QUESTIONS ANSWERED

With this star schema, we can **easily and quickly** answer important business questions:

### Question 1: "What are total sales by month?"

**Query Approach:**
- Join Fact_Sales with Dim_Date
- Group by Month
- Sum TotalAmount

**Business Value:** Track revenue trends over time

---

### Question 2: "Who are my top 10 customers?"

**Query Approach:**
- Join Fact_Sales with Dim_Customer
- Group by Customer
- Sum TotalAmount and order by total (descending)

**Business Value:** Identify high-value customers for retention programs

---

### Question 3: "Which products sell best in Cairo?"

**Query Approach:**
- Join Fact_Sales with Dim_Product and Dim_Location
- Filter: Governorate = 'Cairo'
- Group by Product
- Sum Quantity

**Business Value:** Regional product performance analysis

---

### Question 4: "What's average delivery time by shipper?"

**Query Approach:**
- Join Fact_Sales with Dim_Shipper
- Group by Shipper
- Calculate average Delivery_Time_Days

**Business Value:** Evaluate shipper performance, optimize logistics

---

### Question 5: "Revenue at risk from unpaid orders?"

**Query Approach:**
- Join Fact_Sales with Dim_PaymentStatus
- Filter: Status = 'Unpaid'
- Sum TotalAmount

**Business Value:** Identify financial risk, prioritize collection efforts

---

### Why These Queries Run Fast

All queries execute quickly because:
- ✅ **Star schema structure** - Simple JOINs (Fact → Dimension)
- ✅ **Indexed keys** - Database can quickly find related records
- ✅ **Pre-aggregated dimensions** - No need to calculate on-the-fly
- ✅ **Optimized for BI tools** - Power BI and Tableau designed for this structure

---

## 7. ETL PROCESS (EXTRACT, TRANSFORM, LOAD)

### Extract
- **Source:** Excel file (EG_Retail_Sales_Raw_CaseStudy 1.xlsx)
- **Tool:** Python pandas

### Transform
- **What:** Clean and standardize all data
- **Tool:** Python script (Retail_Sales_Cleaned.py)
- **Actions:**
  - Fix duplicate OrderIDs
  - Standardize dates, names, locations
  - Validate phone numbers and emails
  - Convert currencies to EGP
  - Recalculate amounts
  - Add data quality flags

### Load
- **What:** Populate star schema tables
- **Process:**
  1. Load dimension tables first (Customer, Product, Date, etc.)
  2. Load fact table with references to dimensions
- **Tool:** Python → SQL Database (or SSIS for production)

---

## 8. BENEFITS SUMMARY

### Business Benefits

✅ **Fast Decision Making** - Queries return results in seconds  
✅ **Accurate Reports** - Standardized, clean data  
✅ **Easy Analysis** - Business users can query without IT help  
✅ **Scalable** - Handles growth from 150 to millions of rows  
✅ **Historical Tracking** - Keep full history of all transactions

### Technical Benefits

✅ **Simple Structure** - Easy to understand and maintain  
✅ **Query Performance** - Optimized for analytical queries  
✅ **Data Quality** - Single source of truth  
✅ **Flexibility** - Easy to add new dimensions or measures  
✅ **BI Tool Compatible** - Works seamlessly with Power BI, Tableau

---

## CONCLUSION

The **Star Schema** design transforms our messy Excel file into a clean, efficient, and fast data warehouse that enables powerful business intelligence and reporting capabilities.

**Key Takeaway:** By organizing data into one central fact table surrounded by dimension tables, we eliminate redundancy, improve performance, ensure consistency, and enable fast, accurate business analysis.

---

**END OF DOCUMENT**

