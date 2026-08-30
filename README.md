Data Warehouse Member G.
1. 673020246-9 ชลธิชา หอมพรมมา
2. 673020254-0 ธัณญ์ฌัณญา วงค์จันทร์
3. 673020258-2 ปวริศา โง่นสูงเนิน
4. 673020268-9 อนัญญา ทองปน
5. 673020487-7 กนกวรรณ หงษ์โสภา

## มุมมองด้านรายได้และการขาย (Revenue & Sales Analysis)
1. รายได้รวมจากการขายตั๋วชมภาพยนตร์และสินค้าหน้าโรง (Concession) ในแต่ละเดือน/ไตรมาส เป็นเท่าใด?
    <img width="1537" height="972" alt="สกรีนช็อต 2026-08-30 165813" src="https://github.com/user-attachments/assets/4643a273-b460-4f23-a5d5-2fd715e5b112" />
  - รายได้รวมภาพรวม (Total Revenue): $1,338,110
  - จำนวนตั๋วที่ขายได้ทั้งหมด (Tickets Sold): 5,279 ใบ (จำนวน 5,279 รายการ)
  - สรุปรายได้รายเดือน (Monthly Breakdown):
    - เดือนที่สร้างรายได้สูงสุด (Peak Month): คือ August (สิงหาคม) มียอดขายสูงสุดแตะระดับมากกว่า $120,000
    - กลุ่มเดือนรายได้สูง (High Performing Months): รองลงมาได้แก่ March, May, April และ November ซึ่งมียอดขายเฉลี่ยต่อเดือนอยู่ที่ประมาณ $115,000 - $118,000
    - กลุ่มเดือนรายได้ปานกลางถึงต่ำ (Low Performing Months): คือ December, October และ September โดยมีรายได้อยู่ที่ประมาณ $100,000 - $105,000 ต่อเดือน
    - สรุปภาพรวมรายไตรมาส (Quarterly Overview): รายได้มีการกระจายตัวค่อนข้างสม่ำเสมอตลอดทั้งปี โดยไตรมาสที่ 3 (Q3: Jul - Sep) มีผลประกอบการโดดเด่นที่สุดเนื่องจากยอดขายในเดือนสิงหาคมพุ่งสูงขึ้นอย่างชัดเจน

2. ภาพยนตร์เรื่องใดทำรายได้รวม (Box Office) สูงสุด 5 อันดับแรกในแต่ละประเภทหนัง (Genre)?
<img width="1533" height="646" alt="สกรีนช็อต 2026-08-30 171218" src="https://github.com/user-attachments/assets/32ae3b6d-dbee-4212-bdb3-cb0bf334af03" />
<img width="1608" height="652" alt="สกรีนช็อต 2026-08-30 171237" src="https://github.com/user-attachments/assets/2a2ba3fd-4279-42e6-9818-1ce1009defa0" />
   - ภาพยนตร์ที่ทำรายได้สูงสุด 5 อันดับแรก (Top 5 Movies by Revenue):
    - Speak No Evil: $65,420
    - Twisters: ~$64,180
    - Civil War: ~$58,540
    - Despicable Me 4: ~$57,090
    - Furiosa: A Mad Max Saga: ~$50,120
   - หมวดหมู่ภาพยนตร์ที่ทำรายได้สูงสุด (Revenue by Product Category):
    - Horror (สยองขวัญ): $302,510
    - Drama (ดราม่า): ~$235,350
    - Action (แอ็กชัน): ~$234,940
    - Animation (แอนิเมชัน): ~$207,350
    - Sci-Fi (ไซไฟ): ~$186,690
    - Comedy (ตลก): ~$171,270
3. ช่วงเวลาใดของวัน (Time Slot: เช้า, บ่าย, เย็น, ดึก) ที่สร้างรายได้จากการขายตั๋วมากที่สุด?
   <img width="1557" height="645" alt="image" src="https://github.com/user-attachments/assets/5f490bb9-bf43-44b1-8820-48a34535fbdf" />
   - ช่วงเวลาที่สร้างรายได้สูงสุด (Peak Time Slot): ช่วง Morning (เช้า) สร้างรายได้สูงที่สุดแบบทิ้งห่างช่วงอื่นอย่างชัดเจน อยู่ที่ $661,090.00 (คิดเป็นเกือบ 50% ของรายได้ทั้งหมด)
   - ช่วงเวลารองลงมา:
   - Afternoon (บ่าย): ทำรายได้เป็นอันดับ 2 อยู่ที่ประมาณ $348,000.00
   - Evening (เย็น): ทำรายได้เป็นอันดับ 3 อยู่ที่ประมาณ $329,000.00
     
4. ยอดขายสินค้า Concession เฉลี่ยต่อผู้เข้าชม 1 คน (Concession Spending Per Head) เป็นเท่าใด?
   <img width="675" height="102" alt="image" src="https://github.com/user-attachments/assets/db76d299-7077-447a-8e3e-26642b63ebe3" />
   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT SUM(total_price) AS total_concession_rev, 5279 AS total_tickets, ROUND(SUM(total_price) / 5279.0, 2) AS spend_per_head FROM fact_concession_sales').df())"
   <img width="528" height="43" alt="image" src="https://github.com/user-attachments/assets/89e1b22e-8515-44b6-8a34-6828564a432a" />
   - ยอดขาย Concession รวมจริง: $73,320.00
   - จำนวนตั๋วรวมจริง: 5,279 ใบ
   - Concession Spend Per Head จริง: $13.89 ต่อคน
python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT COALESCE(m.member_tier, \'Non-Member\') AS member_tier, SUM(t.final_price) AS total_spending, COUNT(DISTINCT t.ticket_id) AS total_tickets, ROUND(SUM(t.final_price) / COUNT(DISTINCT t.ticket_id), 2) AS avg_spending_per_ticket FROM fact_ticket_sales t LEFT JOIN dim_customers m ON t.customer_id = m.customer_id GROUP BY m.member_tier ORDER BY total_spending DESC').df())"

# มุมมองด้านลูกค้าและสมาชิก (Customer & Membership Analysis)
5. สมาชิกแต่ละระดับ (Member Tier: Silver, Gold, Platinum) มียอด spending รวมต่างกันอย่างไร?
   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT c.member_tier, SUM(t.final_price) AS ticket_spending FROM dim_customers c LEFT JOIN fact_ticket_sales t ON c.customer_id = t.customer_id GROUP BY c.member_tier ORDER BY ticket_spending DESC').df())"
   <img width="292" height="87" alt="image" src="https://github.com/user-attachments/assets/b2ddc166-b163-4294-8661-9d3070a47ea7" />

6. ลูกค้าระดับ Platinum นิยมซื้อประเภทที่นั่งแบบใดมากที่สุด (Normal, Honeymoon, VIP)?
   python3 -c "import duckdb; con = duckdb.connect('movie_dw/dev.duckdb'); print(con.execute('SELECT t.seat_type, COUNT(t.ticket_id) AS total_seats_booked, SUM(t.final_price) AS total_spending FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id WHERE c.member_tier = \'Platinum\' GROUP BY t.seat_type ORDER BY total_seats_booked DESC').df())"
   <img width="467" height="87" alt="image" src="https://github.com/user-attachments/assets/5d74b6da-52e4-4518-bb53-ec42338d2b6f" />
   <img width="1487" height="427" alt="image" src="https://github.com/user-attachments/assets/b30322fc-a879-488a-8937-cfe14096e9c2" />
   <img width="742" height="671" alt="image" src="https://github.com/user-attachments/assets/1c2b9bbb-bb33-4ddb-9af7-7d5e88a31c76" />

7. สมาชิกกลุ่มใดที่ซื้อสินค้า Concession มากที่สุด และสินค้าประเภทใดที่เป็นที่นิยมของกลุ่ม Gold/Platinum?
   <img width="707" height="676" alt="image" src="https://github.com/user-attachments/assets/871d18f9-9c81-4ea2-a302-81a6a755ecb0" />
<img width="1897" height="773" alt="image" src="https://github.com/user-attachments/assets/8d57b90c-1926-4de8-9b1b-14fe8f4a108b" />

8. ยอดขายตั๋วจำแนกตามประเภทสมาชิกในแต่ละไตรมาสเป็นอย่างไร?
   <img width="700" height="322" alt="image" src="https://github.com/user-attachments/assets/1d0e1478-123d-40cb-9a31-53ef87cade24" />

# มุมมองด้านภาพยนตร์และการฉาย (Movie & Showtimes Performance Analysis)
9. หนังประเภท (Genre) ใดที่ทำรายได้รวมสูงที่สุดในโรงภาพยนตร์?
10. ภาพยนตร์ที่มีระดับความเหมาะสม (Rating เช่น R, PG-13, PG) แบบใดที่ดึงดูดผู้ฟังและทำรายได้สูงสุด?
11. โรงฉายหมายเลขใด (Screen Number) มีอัตราการสร้างรายได้เฉลี่ยต่อรอบสูงสุด?
12. ภาพยนตร์เรื่องใดที่มีความยาวหนัง (Duration) เกิน 150 นาที แล้วกระทบต่อจำนวนรอบฉายและรายได้รวมหรือไม่?
# มุมมองด้านที่นั่งและพฤติกรรมการบริโภค (Seat & Concession Trend Analysis)
13. ที่นั่งประเภทใด (Normal, Honeymoon, VIP) ทำรายได้รวมสูงสุด และมีสัดส่วนเป็นกี่เปอร์เซ็นต์ของรายได้ตั๋วทั้งหมด?
14. สินค้า Concession ประเภทใด (Combo Set, Popcorn, Water, Soda) ที่ขายดีที่สุดในเชิงปริมาณ (Quantity) และเชิงรายได้ (Total Price)?
15. การชมภาพยนตร์ช่วงวันหยุด/วันทำงาน สัมพันธ์กับการซื้อ Combo Set หน้าโรงอย่างไร?

