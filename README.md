Data Warehouse Member G.
1. 673020246-9 ชลธิชา หอมพรมมา
2. 673020254-0 ธัณญ์ฌัณญา วงค์จันทร์
3. 673020258-2 ปวริศา โง่นสูงเนิน
4. 673020268-9 อนัญญา ทองปน
5. 673020487-7 กนกวรรณ หงษ์โสภา

## มุมมองด้านรายได้และภาพรวม (Revenue & Overview)

1. รายได้รวมจากการขายตั๋วภาพยนตร์เป็นเท่าใด?

- รายได้รวมจากการขายตั๋วภาพยนตร์ทั้งหมด (Total Ticket Revenue):เท่ากับ $1,338,110.00 (จากจำนวนตั๋วทั้งหมด 5,279 ใบ)

    <img width="1537" height="972" alt="สกรีนช็อต 2026-08-30 165813" src="https://github.com/user-attachments/assets/4643a273-b460-4f23-a5d5-2fd715e5b112" />

2. ช่วงเวลาใดของวัน (Time Slot: เช้า, บ่าย, เย็น, ดึก) ที่สร้างรายได้จากการขายตั๋วมากที่สุด?

- ช่วงเวลา (Time Slot) ที่ทำรายได้สูงที่สุด:

อันดับ 1 (สูงสุด): ช่วง Morning (เช้า) ทำรายได้สูงถึง $661,090.00 (คิดเป็นเกือบ 50% ของรายได้ตั๋วทั้งหมด)

อันดับ 2: ช่วง Afternoon (บ่าย) ทำรายได้ $400,240.00

อันดับ 3: ช่วง Evening (เย็น/ค่ำ) ทำรายได้ $276,780.00
    
   <img width="1557" height="645" alt="image" src="https://github.com/user-attachments/assets/5f490bb9-bf43-44b1-8820-48a34535fbdf" />

3. ยอดขายสินค้า Concession รวมคิดเป็นยอดซื้อเฉลี่ยต่อผู้เข้าชม 1 คน (Spend Per Head) เป็นเท่าใด?

- ยอดขาย Concession รวมจริง: $73,320.00

- จำนวนตั๋วรวมจริง: 5,279 ใบ

- Concession Spend Per Head จริง: $13.89 ต่อคน

   <img width="675" height="102" alt="image" src="https://github.com/user-attachments/assets/db76d299-7077-447a-8e3e-26642b63ebe3" />
   
   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT SUM(total_price) AS total_concession_rev, 5279 AS total_tickets, ROUND(SUM(total_price) / 5279.0, 2) AS spend_per_head FROM fact_concession_sales').df())"
   
   <img width="528" height="43" alt="image" src="https://github.com/user-attachments/assets/89e1b22e-8515-44b6-8a34-6828564a432a" />
   
python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT COALESCE(m.member_tier, \'Non-Member\') AS member_tier, SUM(t.final_price) AS total_spending, COUNT(DISTINCT t.ticket_id) AS total_tickets, ROUND(SUM(t.final_price) / COUNT(DISTINCT t.ticket_id), 2) AS avg_spending_per_ticket FROM fact_ticket_sales t LEFT JOIN dim_customers m ON t.customer_id = m.customer_id GROUP BY m.member_tier ORDER BY total_spending DESC').df())"

4.สัดส่วนรายได้รวมระหว่างยอดขายตั๋ว (Ticket Revenue) กับยอดขาย Concession คิดเป็นกี่เปอร์เซ็นต์?

- ตั๋ว 94.8% ($1,338,110)
- Concession 5.2% ($73,320)

5.ราคาตั๋วเฉลี่ยต่อใบ (Average Ticket Price) ของภาพยนตร์ทั้งหมดเป็นเท่าใด?

- ประมาณ $253.48 ต่อใบ

## ด้านภาพยนตร์และโรงฉาย (Movies & Showtimes)

6. ภาพยนตร์เรื่องใดทำรายได้รวม (Box Office) สูงสุด 5 อันดับแรก

- ภาพยนตร์ที่ทำรายได้สูงสุด 5 อันดับแรก (Top 5 Movies by Revenue):
    
อันดับที่ 1 Speak No Evil: $65,420
    
อันดับที่ 2 Twisters: ~$64,180
    
อันดับที่ 3 Civil War: ~$58,540
    
อันดับที่ 4 Despicable Me 4: ~$57,090
    
อันดับที่ 5 Furiosa: A Mad Max Saga: ~$50,120

7. หมวดหมู่ภาพยนตร์ใดที่ทำรายได้สูงสุด (Genre)?

- หมวดหมู่ภาพยนตร์ที่ทำรายได้สูงสุด (Revenue by Product Category)คือ
    
อันดับที่ 1 Horror (สยองขวัญ): $302,510
    
อันดับที่ 2 Drama (ดราม่า): ~$235,350
    
อันดับที่ 3 Action (แอ็กชัน): ~$234,940
    
อันดับที่ 4 Animation (แอนิเมชัน): ~$207,350
    
อันดับที่ 5 Sci-Fi (ไซไฟ): ~$186,690
    
อันดับที่ 6 Comedy (ตลก): ~$171,270

<img width="1533" height="646" alt="สกรีนช็อต 2026-08-30 171218" src="https://github.com/user-attachments/assets/32ae3b6d-dbee-4212-bdb3-cb0bf334af03" />

<img width="1608" height="652" alt="สกรีนช็อต 2026-08-30 171237" src="https://github.com/user-attachments/assets/2a2ba3fd-4279-42e6-9818-1ce1009defa0" />

8.ภาพยนตร์ที่มีระดับความเหมาะสม (Rating เช่น R, PG-13, PG) แบบใดที่ทำรายได้รวมสูงที่สุด?

9.โรงฉายหมายเลขใด (Screen Number) ที่ทำรายได้รวมจากการขายตั๋วสูงที่สุด?

# ด้านพฤติกรรมลูกค้าและที่นั่ง (Member & Seat Behavior)

10. สมาชิกระดับต่างๆ (Member Tier: Silver, Gold, Platinum) มียอด spending รวมต่างกันอย่างไร?

- สมาชิกระดับ Platinum มียอด spending รวม คือ $493,440
  
- สมาชิกระดับ Silver มียอด spending รวม คือ $476,870
  
- สมาชิกระดับ Gold มียอด spending รวม คือ $424,120
   
   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT c.member_tier, SUM(t.final_price) AS ticket_spending FROM dim_customers c LEFT JOIN fact_ticket_sales t ON c.customer_id = t.customer_id GROUP BY c.member_tier ORDER BY ticket_spending DESC').df())"
  
   <img width="292" height="87" alt="image" src="https://github.com/user-attachments/assets/b2ddc166-b163-4294-8661-9d3070a47ea7" />

11. ยอดขายตั๋วรวม (Total Tickets) จำแนกตามประเภทสมาชิก (Member Tier) เป็นอย่างไร?

- ระดับ Platinum: จำนวนตั๋ว: 1,959 ใบ

- ระดับ Silver: จำนวนตั๋ว: 1,878 ใบ

- ระดับ Gold: จำนวนตั๋ว: 1,663 ใบ

   <img width="700" height="322" alt="image" src="https://github.com/user-attachments/assets/1d0e1478-123d-40cb-9a31-53ef87cade24" />

12.ลูกค้าระดับ Platinum นิยมซื้อประเภทที่นั่งแบบใดมากที่สุด (Normal, Honeymoon, VIP)?

- ลูกค้าระดับ Platinum นิยมซื้อประเภทที่นั่งแบบ Normal มากที่สุดจำนวน 1,369 ใบ

    <img width="742" height="671" alt="image" src="https://github.com/user-attachments/assets/1c2b9bbb-bb33-4ddb-9af7-7d5e88a31c76" />

13.ประเภทที่นั่งแบบใด (Seat Type: Normal, Honeymoon, VIP) ที่สร้างรายได้รวมให้โรงหนังมากที่สุด?

- ประเภทที่นั่งแบบ Normal สร้างรายได้รวมมากที่สุด

   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT t.seat_type, COUNT(t.ticket_id) AS total_seats_booked, SUM(t.final_price) AS total_spending FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id WHERE c.member_tier = \'Platinum\' GROUP BY t.seat_type ORDER BY total_seats_booked DESC').df())"
   
   <img width="467" height="87" alt="image" src="https://github.com/user-attachments/assets/5d74b6da-52e4-4518-bb53-ec42338d2b6f" />
   
   <img width="1487" height="427" alt="image" src="https://github.com/user-attachments/assets/b30322fc-a879-488a-8937-cfe14096e9c2" />

## ด้านสินค้า Concession (Concession Performance)

14. สินค้า Concession ประเภทใดที่เป็นที่นิยมซื้อมากที่สุดของกลุ่มสมาชิกระดับ Gold และ Platinum?

- สินค้า Concession ที่ขายดีที่สุด

อันดับ 1 Popcorn Cheese (ป๊อปคอร์นรสชีส)
  
อันดับ 2 Popcorn Sweet (ป๊อปคอร์นรสหวาน)

อันดับ 3 Combo Set A (ชุดคอมโบเซ็ต A)

อันดับ 4 Popcorn Original (ป๊อปคอร์นรสออริจินัล)

   <img width="707" height="676" alt="image" src="https://github.com/user-attachments/assets/871d18f9-9c81-4ea2-a302-81a6a755ecb0" />

15.หมวดหมู่สินค้า Concession (Product Category: Popcorn, Beverage, Combo Set) ใดทำรายได้รวมสูงที่สุด?

- หมวด Popcorn ทำรายได้รวมสูงที่สุด
   
<img width="1897" height="773" alt="image" src="https://github.com/user-attachments/assets/8d57b90c-1926-4de8-9b1b-14fe8f4a108b" />
