## 🔄 06. Data Pipeline & ETL Transformations

เอกสารฉบับนี้อธิบายกระบวนการการเคลื่อนย้ายข้อมูล (Data Movement) และการแปลงสภาพข้อมูล (Data Transformation) จากข้อมูลดิบ (Raw Datasets) ไปยังคลังข้อมูล (Data Warehouse) โดยใช้ dbt (data build tool) ร่วมกับ DuckDB

---

## 🏗️ 1. Pipeline Architecture (Medallion Pattern)

โปรเจกต์นี้ใช้โครงสร้างสถาปัตยกรรมข้อมูลแบบ 3-Tier Layering ตามแนวทาง Medallion Architecture:

**Raw Datasets (.csv) ➔ Staging Layer (stg_*) ➔ Data Warehouse Layer (dim_* / fact_*)**

1. **Source Layer:** ไฟล์ข้อมูลดิบรูปแบบ CSV ภายในโฟลเดอร์ `datasets/`

2. **Staging Layer (stg_*):** ดึงข้อมูลจาก Source Tables และเพิ่ม `ingestion_timestamp` เพื่อบันทึกเวลาที่ข้อมูลเข้าสู่กระบวนการ Transformation

3. **Data Warehouse Layer (dim_* / fact_*):** ปรับโครงสร้างข้อมูลสำหรับการวิเคราะห์ ทำ Deduplication, Parse ค่า Date/Time และรวมข้อมูลยอดขายสำหรับการวิเคราะห์

---

## 📥 2. Data Sources & Extract

ข้อมูลต้นทางของโปรเจกต์อยู่ในรูปแบบ CSV ภายในโฟลเดอร์ `movie_dw/datasets/` ประกอบด้วย:

- `customers.csv`
- `movies.csv`
- `showtimes.csv`
- `ticket_sales_5000.csv`
- `concession_sales.csv`

dbt กำหนด Source Tables ผ่านไฟล์ `models/staging/src_movie.yml` โดยใช้ DuckDB เป็น Database Engine สำหรับจัดเก็บและประมวลผลข้อมูล ก่อนนำไปสร้าง Staging, Dimension และ Fact Models

---

## 🧹 3. Staging Models (models/staging/)

Staging Layer ทำหน้าที่ดึงข้อมูลจาก Source Tables ที่กำหนดไว้ใน `src_movie.yml` และเตรียมข้อมูลเบื้องต้นก่อนเข้าสู่กระบวนการ Transformation

- `stg_customers.sql`: ดึงข้อมูลลูกค้า และเพิ่ม `current_localtimestamp() as ingestion_timestamp`
- `stg_movies.sql`: ดึงข้อมูลภาพยนตร์ และเพิ่ม `ingestion_timestamp`
- `stg_showtimes.sql`: ดึงข้อมูลรอบฉายภาพยนตร์ และเพิ่ม `ingestion_timestamp`
- `stg_ticket_sales.sql`: ดึงข้อมูลธุรกรรมการขายตั๋ว และเพิ่ม `ingestion_timestamp`
- `stg_concession_sales.sql`: ดึงข้อมูลการขายสินค้า Concession และเพิ่ม `ingestion_timestamp`

ตัวอย่างการเพิ่ม Timestamp ใน Staging Layer:

```sql
select
    *,
    current_localtimestamp() as ingestion_timestamp
from {{ source('movie_source', 'customers') }}
```

---

## ⚙️ 4. Core Transformations & Techniques

### 4.1 Data Deduplication (การกำจัดข้อมูลซ้ำซ้อน)

ในตาราง Dimension และ Fact มีการป้องกันข้อมูลซ้ำโดยใช้ Window Function `ROW_NUMBER()` เพื่อแบ่งกลุ่มข้อมูลตาม Primary Identifier และเก็บข้อมูลไว้เพียง 1 แถวต่อ Identifier

ตัวอย่างโค้ดใน `dim_movies.sql`:

```sql
with source as (
    select
        movie_id,
        title,
        genre,
        duration_min,
        rating,
        ingestion_timestamp as insertion_timestamp
    from {{ ref('stg_movies') }}
),

unique_source as (
    select
        *,
        row_number() over(partition by movie_id) as row_num
    from source
)

select * exclude (row_num)
from unique_source
where row_num = 1;
```

วิธีนี้ช่วยลดปัญหาข้อมูลซ้ำของ Identifier เดียวกันก่อนนำข้อมูลไปใช้ในการวิเคราะห์

### 4.2 Date Parsing & Standardization (การแปลงและปรับฟอร์แมตวันที่)

เนื่องจากข้อมูล `show_date` อาจอยู่ในหลายรูปแบบ จึงใช้ `TRY_STRPTIME()`, `TRY_CAST()` และ `COALESCE()` เพื่อแปลงข้อมูลให้อยู่ในรูปแบบวันที่ที่สามารถนำไปวิเคราะห์ได้

ตัวอย่างโค้ดใน `fact_ticket_sales.sql`:

```sql
cast(
    coalesce(
        try_strptime(s.show_date, '%m/%d/%Y %H:%M:%S'),
        try_strptime(s.show_date, '%m/%d/%Y %H:%M'),
        try_strptime(s.show_date, '%Y-%m-%d %H:%M:%S'),
        try_strptime(s.show_date, '%Y-%m-%d %H:%M'),
        try_strptime(s.show_date, '%Y-%m-%d'),
        try_strptime(s.show_date, '%m/%d/%Y'),
        try_cast(s.show_date as timestamp)
    ) as date
) as show_date
```

การใช้หลายรูปแบบร่วมกับ `COALESCE()` ช่วยให้ระบบรองรับข้อมูลวันที่ที่มีรูปแบบแตกต่างกัน และลดข้อผิดพลาดจากการแปลงข้อมูล

### 4.3 Data Unification (การรวมตารางยอดขาย)

ตาราง `fact_sales.sql` เกิดจากการรวมข้อมูลระหว่างการขายตั๋วหนัง (`fact_ticket_sales`) และการขายสินค้า Concession (`fact_concession_sales`) ด้วยคำสั่ง `UNION ALL`

พร้อมระบุคอลัมน์ `sales_type` เพื่อแยกประเภทของยอดขายระหว่าง Ticket และ Concession ทำให้สามารถนำข้อมูลไปวิเคราะห์รายได้รวม (Total Revenue) ได้สะดวกมากขึ้น

---

## 📦 5. Data Warehouse Loading

หลังจากข้อมูลผ่าน Staging และ Transformation แล้ว dbt จะสร้าง Dimension และ Fact Tables สำหรับใช้ในการวิเคราะห์ใน Data Warehouse

### Dimension Tables

- `dim_customers`
- `dim_movies`
- `dim_showtimes`

### Fact Tables

- `fact_ticket_sales`
- `fact_concession_sales`
- `fact_sales`

Dimension Tables ใช้เก็บข้อมูลเชิงรายละเอียดสำหรับการวิเคราะห์ เช่น ลูกค้า ภาพยนตร์ และรอบฉาย

Fact Tables ใช้เก็บข้อมูลธุรกรรมและ Measures ที่ใช้ในการวิเคราะห์ เช่น `final_price`, `quantity` และ `total_price`

ความสัมพันธ์ระหว่าง Fact และ Dimension Tables ใช้ Business/Natural Keys เช่น `customer_id`, `movie_id` และ `showtime_id`

---

## ✅ 6. Data Quality & Testing Framework

มีการกำหนด Data Validation ไว้ใน `models/datawarehouse/schema.yml` เพื่อทดสอบความถูกต้องของข้อมูลใน Data Warehouse

### Unique & Not Null

ใช้ตรวจสอบ Primary Identifier ของตาราง เช่น:

- `customer_id`
- `movie_id`
- `showtime_id`
- `ticket_id`
- `concession_sale_id`

เพื่อช่วยตรวจสอบว่า Identifier ที่สำคัญไม่มีค่า NULL และไม่มีข้อมูลซ้ำตามเงื่อนไขที่กำหนด

### Relationships

ใช้ตรวจสอบ Referential Integrity ของ Foreign Key ที่มีการกำหนด Relationship Test ไว้ระหว่าง Fact และ Dimension Tables เช่น:

- `fact_ticket_sales.customer_id` → `dim_customers.customer_id`
- `fact_ticket_sales.movie_id` → `dim_movies.movie_id`
- `fact_concession_sales.customer_id` → `dim_customers.customer_id`

การทดสอบเหล่านี้ช่วยตรวจสอบความสอดคล้องของข้อมูลระหว่าง Fact และ Dimension Tables ก่อนนำข้อมูลไปใช้ในการวิเคราะห์

---

## ▶️ 7. Running the Pipeline & Testing

เข้าสู่โฟลเดอร์ dbt project:

```bash
cd movie_dw
```

ตรวจสอบการเชื่อมต่อและ Configuration:

```bash
dbt debug
```

ประมวลผล Data Transformation และสร้าง Data Warehouse Models:

```bash
dbt run
```

ทดสอบ Data Quality ตามที่กำหนดไว้ใน `schema.yml`:

```bash
dbt test
```

กระบวนการโดยรวมสามารถสรุปได้ดังนี้:

**Raw CSV Data ➔ DuckDB Source Tables ➔ Staging Models ➔ Data Transformation ➔ Dimension & Fact Tables ➔ Data Quality Testing ➔ Data Warehouse**
