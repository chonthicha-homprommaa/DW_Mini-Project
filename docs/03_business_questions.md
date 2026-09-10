# Business Questions
## คำถามทางธุรกิจสำหรับการวิเคราะห์คลังข้อมูลโรงภาพยนตร์

คลังข้อมูล (Data Warehouse) นี้ถูกออกแบบมาเพื่อสนับสนุนการวิเคราะห์
ข้อมูลการขายตั๋วภาพยนตร์และการขายสินค้า Concession โดยกำหนดคำถาม
ทางธุรกิจจำนวน 15 ข้อ ซึ่งสามารถตอบได้จากข้อมูลใน Data Warehouse

---

## 1. รายได้รวมและการเปรียบเทียบช่องทางขาย
### Sales & Revenue Overview

### 1. รายได้รวมจากการขายตั๋วภาพยนตร์ทั้งหมดเป็นเท่าใด?
- **Source:** Fact_Ticket_Sales
- **Measure:** SUM(Final_Price)

### 2. ช่วงเวลาใดของวัน (Morning, Afternoon, Evening) ที่สร้างรายได้จากการขายตั๋วมากที่สุด?
- **Dimension:** Dim_Showtime
- **Attribute:** Show_Date
- **Derived Attribute:** Time_Slot (คำนวณจากเวลาของ Show_Date ใน Analytical Query)
- **Measure:** SUM(Final_Price)

### 3. ยอดขายสินค้า Concession รวมคิดเป็นยอดซื้อเฉลี่ยต่อผู้เข้าชม 1 คน (Spend Per Head) เป็นเท่าใด?
- **Source:** Fact_Concession_Sales, Fact_Ticket_Sales
- **Measure:** SUM(Total_Price) / COUNT(Ticket_ID)

### 4. สัดส่วนรายได้รวมระหว่างยอดขายตั๋ว (Ticket Revenue) กับยอดขาย Concession คิดเป็นกี่เปอร์เซ็นต์?
- **Source:** Fact_Ticket_Sales, Fact_Concession_Sales
- **Measure:** SUM(Final_Price), SUM(Total_Price)

### 5. ราคาตั๋วเฉลี่ยต่อใบ (Average Ticket Price) ของภาพยนตร์ทั้งหมดเป็นเท่าใด?
- **Source:** Fact_Ticket_Sales
- **Measure:** AVG(Final_Price)

---

## 2. ประสิทธิภาพภาพยนตร์และโรงฉาย
### Movie & Screen Performance

### 6. ภาพยนตร์เรื่องใดทำรายได้รวมสูงสุด 5 อันดับแรก (Top 5 Movies)?
- **Dimension:** Dim_Movie
- **Attribute:** Title
- **Measure:** SUM(Final_Price)

### 7. หมวดหมู่ภาพยนตร์ (Genre) ใดที่ทำรายได้รวมสูงที่สุด?
- **Dimension:** Dim_Movie
- **Attribute:** Genre
- **Measure:** SUM(Final_Price)

### 8. ภาพยนตร์ที่มีระดับความเหมาะสม (Rating เช่น R, PG-13, PG) แบบใดที่ทำรายได้รวมสูงที่สุด?
- **Dimension:** Dim_Movie
- **Attribute:** Rating
- **Measure:** SUM(Final_Price)

### 9. โรงฉายหมายเลขใด (Screen Number) ที่ทำรายได้รวมจากการขายตั๋วสูงที่สุด?
- **Dimension:** Dim_Showtime
- **Attribute:** Screen_Number
- **Measure:** SUM(Final_Price)

---

## 3. พฤติกรรมลูกค้าและสมาชิก
### Customer & Member Behavior

### 10. สมาชิกระดับต่าง ๆ (Member Tier: Silver, Gold, Platinum) มียอด Spending รวมต่างกันอย่างไร?
- **Dimension:** Dim_Customer
- **Attribute:** Member_Tier
- **Measure:** SUM(Final_Price)

### 11. ยอดขายตั๋วรวม (Total Tickets) จำแนกตามประเภทสมาชิก (Member Tier) เป็นอย่างไร?
- **Dimension:** Dim_Customer
- **Attribute:** Member_Tier
- **Measure:** COUNT(Ticket_ID)

### 12. ลูกค้าระดับ Platinum นิยมซื้อประเภทที่นั่งแบบใดมากที่สุด (Normal, Honeymoon, VIP)?
- **Dimension:** Dim_Customer
- **Filter:** Member_Tier = 'Platinum'
- **Fact Attribute:** Seat_Type จาก Fact_Ticket_Sales
- **Measure:** COUNT(Ticket_ID)

### 13. ประเภทที่นั่งแบบใด (Seat Type: Normal, Honeymoon, VIP) ที่สร้างรายได้รวมให้โรงภาพยนตร์มากที่สุด?
- **Source:** Fact_Ticket_Sales
- **Fact Attribute:** Seat_Type
- **Measure:** SUM(Final_Price)

---

## 4. ยอดขายสินค้าและบริการ Concession
### Concession Performance

### 14. สินค้า Concession ประเภทใดที่เป็นที่นิยมซื้อมากที่สุดของกลุ่มสมาชิกระดับ Gold และ Platinum?
- **Dimension:** Dim_Customer
- **Filter:** Member_Tier IN ('Gold', 'Platinum')
- **Fact Attribute:** Item_Name จาก Fact_Concession_Sales
- **Measure:** SUM(Quantity)

### 15. หมวดหมู่สินค้า Concession (Product Category: Popcorn, Beverage, Combo Set) ใดทำรายได้รวมสูงที่สุด?
- **Source:** Fact_Concession_Sales
- **Fact Attribute:** Category
- **Measure:** SUM(Total_Price)
