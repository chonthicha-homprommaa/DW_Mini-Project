# Data Dictionary (OLTP Source Tables)

เอกสารนี้อธิบายรายละเอียดโครงสร้างตาราง ชนิดข้อมูล (Data Type) ข้อกำหนดคีย์ (Key Constraints) และคำอธิบายความหมายของแต่ละฟิลด์ สำหรับตารางต้นทาง (OLTP) ทั้ง 5 ตารางในระบบโรงภาพยนตร์

---

## 1. Table: `movies`
เก็บข้อมูลรายละเอียดของภาพยนตร์ที่จัดฉายในโรงภาพยนตร์

| Column Name | Data Type | Key Constraint | Description |
| :--- | :--- | :--- | :--- |
| `movie_id` | INT | Primary Key | รหัสประจำตัวภาพยนตร์ |
| `title` | VARCHAR(255) | - | ชื่อเรื่องของภาพยนตร์ |
| `genre` | VARCHAR(50) | - | ประเภทภาพยนตร์ (เช่น Horror, Sci-Fi, Drama) |
| `duration_min` | INT | - | ความยาวของภาพยนตร์ (นาที) |
| `rating` | VARCHAR(10) | - | เรตติ้งจำกัดอายุผู้ชม (เช่น R, PG-13, G) |

---

## 2. Table: `customers`
เก็บข้อมูลรายละเอียดของลูกค้าและระดับสมาชิก

| Column Name | Data Type | Key Constraint | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | INT | Primary Key | รหัสประจำตัวลูกค้า |
| `first_name` | VARCHAR(100) | - | ชื่อจริงของลูกค้า |
| `last_name` | VARCHAR(100) | - | นามสกุลของลูกค้า |
| `email` | VARCHAR(150) | - | อีเมลสำหรับติดต่อ |
| `member_tier` | VARCHAR(50) | - | ระดับสมาชิก (Platinum, Gold, Silver) |

---

## 3. Table: `showtimes`
เก็บข้อมูลตารางและรอบเวลาฉายภาพยนตร์

| Column Name | Data Type | Key Constraint | Description |
| :--- | :--- | :--- | :--- |
| `showtime_id` | INT | Primary Key | รหัสประจำตัวรอบฉาย |
| `movie_id` | INT | Foreign Key | รหัสภาพยนตร์ที่จัดฉาย (อ้างอิง `movies.movie_id`) |
| `screen_number` | INT | - | หมายเลขโรงภาพยนตร์ที่ฉาย |
| `show_date` | DATETIME | - | วันและเวลาที่เริ่มฉายภาพยนตร์ |
| `ticket_price` | DECIMAL(10,2)| - | ราคาตั๋วตั้งต้นของรอบฉายนั้น |

---

## 4. Table: `ticket_sales`
เก็บรายการธุรกรรมการขายตั๋วภาพยนตร์

| Column Name | Data Type | Key Constraint | Description |
| :--- | :--- | :--- | :--- |
| `ticket_id` | INT | Primary Key | รหัสการขายตั๋วภาพยนตร์ |
| `showtime_id` | INT | Foreign Key | รหัสรอบฉาย (อ้างอิง `showtimes.showtime_id`) |
| `customer_id` | INT | Foreign Key | รหัสลูกค้าผู้ซื้อ (อ้างอิง `customers.customer_id`) |
| `seat_number` | VARCHAR(10) | - | หมายเลขที่นั่งในโรงภาพยนตร์ |
| `seat_type` | VARCHAR(50) | - | ประเภทที่นั่ง (Normal, Honeymoon, VIP) |
| `final_price` | DECIMAL(10,2)| - | ยอดเงินสุทธิที่ชำระจริง |

---

## 5. Table: `concession_sales`
เก็บรายการธุรกรรมการขายสินค้าป๊อปคอร์นและเครื่องดื่ม

| Column Name | Data Type | Key Constraint | Description |
| :--- | :--- | :--- | :--- |
| `sale_id` | INT | Primary Key | รหัสการขายสินค้า |
| `customer_id` | INT | Foreign Key | รหัสลูกค้าผู้ซื้อ (อ้างอิง `customers.customer_id`) |
| `item_name` | VARCHAR(100) | - | ชื่อสินค้า (เช่น Combo Set B, Water, Soda (L)) |
| `quantity` | INT | - | จำนวนชิ้นที่สั่งซื้อ |
| `unit_price` | DECIMAL(10,2)| - | ราคาต่อหน่วยของสินค้า |
| `total_price` | DECIMAL(10,2)| - | ยอดรวมเงินส่วนสินค้า |
| `sale_date` | DATETIME | - | วันและเวลาที่ซื้อสินค้า |
