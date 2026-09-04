## 🔄 06. Data Pipeline & ETL Transformations
เอกสารฉบับนี้อธิบายกระบวนการการเคลื่อนย้ายข้อมูล (Data Movement) และการแปลงสภาพข้อมูล (Data Transformation) จากระบบปฏิบัติการดิบ (OLTP / Raw Datasets) ไปยังคลังข้อมูล (Data Warehouse) โดยใช้ dbt (data build tool) ร่วมกับ DuckDB

## 🏗️ 1. Pipeline Architecture (Medallion Pattern)
โปรเจกต์นี้ใช้โครงสร้างสถาปัตยกรรมข้อมูลแบบ 3-Tier Layering ตามแนวทาง Medallion Architecture:

Raw Datasets (.csv) ➔ Staging Layer (stg_*) ➔ Data Warehouse Layer (dim_* / fact_*)

1.Source Layer: ไฟล์ข้อมูลดิบรูปแบบ CSV ในโฟลเดอร์ datasets/

2.Staging Layer (stg_*): แปลงโครงสร้างข้อมูลดิบเบื้องต้น ลบอักขระส่วนเกิน และบันทึกเวลาการนำเข้าข้อมูล

3.Data Warehouse Layer (dim_* / fact_*): ปรับรูปแบบเป็น Star Schema, ทำ Deduplication, Parse ค่า Date/Time และทำการ Unify ยอดขายทั้งหมด

## 🧹 2. Staging Models (models/staging/)
การสร้าง Staging Layer ทำหน้าที่ดึงข้อมูลจาก src_movie.yml และเตรียมโครงสร้างเบื้องต้น:

stg_customers.sql: ดึงข้อมูลลูกค้า และเพิ่ม current_localtimestamp() as ingestion_timestamp

stg_movies.sql: ดึงข้อมูลภาพยนตร์ และเพิ่ม ingestion_timestamp

stg_showtimes.sql: ดึงข้อมูลรอบฉายภาพยนตร์ และเพิ่ม ingestion_timestamp

stg_ticket_sales.sql: ดึงข้อมูลธุรกรรมการขายตั๋ว และเพิ่ม ingestion_timestamp

stg_concession_sales.sql: ดึงข้อมูลการขายสินค้าป๊อปคอร์นและเครื่องดื่ม และเพิ่ม ingestion_timestamp

## ⚙️ 3. Core Transformations & Techniques

3.1 Data Deduplication (การกำจัดข้อมูลซ้ำซ้อน)
ในตารางมิติข้อมูล (Dimension) มีการป้องกันปัญหาข้อมูลซ้ำโดยใช้ Window Function ROW_NUMBER() เพื่อเลือกเฉพาะแถวล่าสุดเพียง 1 แถวต่อ Primary Key:

ตัวอย่างโค้ดใน dim_movies.sql:
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
        row_number() over(partition by movie_id order by insertion_timestamp desc) as row_num
    from source
)
select * exclude (row_num)
from unique_source
where row_num = 1;

3.2 Date Parsing & Standardization (การแปลงและปรับฟอร์แมตวันที่)

เนื่องจากข้อมูล show_date มีรูปแบบข้อความที่ไม่สม่ำเสมอ จึงใช้ TRY_STRPTIME() ร่วมกับ COALESCE() เพื่อแปลงเป็นประเภทข้อมูล DATE ที่ถูกต้อง:

ตัวอย่างโค้ดใน fact_ticket_sales.sql:
cast(
    coalesce(
        try_strptime(s.show_date, '%m/%d/%Y %H:%M:%S'),
        try_strptime(s.show_date, '%Y-%m-%d'),
        try_strptime(s.show_date, '%m/%d/%Y')
    ) as date
) as show_date
3.3 Data Unification (การรวมตารางยอดขาย)
ตาราง fact_sales.sql เกิดจากการรวมข้อมูลระหว่างการขายตั๋วหนัง (fact_ticket_sales) และสินค้าหน้าโรง (fact_concession_sales) ด้วยคำสั่ง UNION ALL พร้อมระบุคอลัมน์ sales_type เพื่ออำนวยความสะดวกในการวิเคราะห์รายได้รวม (Total Revenue)

## ✅ 4. Data Quality & Testing Framework
มีการกำหนดมาตรฐาน Data Validation ไว้ใน models/schema.yml สำหรับทดสอบความถูกต้องของคลังข้อมูล:

unique & not_null: บังคับใช้กับ Primary Key ของทุกตาราง เช่น customer_id, movie_id, showtime_id, ticket_id, concession_sale_id

relationships: ตรวจสอบ Referential Integrity ความเชื่อมโยงระหว่าง Foreign Key ใน Fact Table กับ Primary Key ใน Dimension Table
การรัน Pipeline & Testing:
# ประมวลผล Data Transformation ทั้งหมด
dbt run

# ทดสอบ Data Quality ทั้งหมดตาม schema.yml
dbt test
