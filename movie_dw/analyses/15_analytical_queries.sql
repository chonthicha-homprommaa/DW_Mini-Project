-- ข้อ 1: รายได้ตั๋วหนังและ Concession รายเดือน / ไตรมาส
SELECT 
    s.show_date,
    SUM(t.final_price) AS ticket_revenue
FROM fact_ticket_sales t
JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
GROUP BY s.show_date
ORDER BY s.show_date;

-- ข้อ 2: Top 5 หนังทำรายได้สูงสุด แยกตาม Genre
WITH RankedMovies AS (
    SELECT 
        m.genre, 
        m.title, 
        SUM(t.final_price) AS total_revenue,
        ROW_NUMBER() OVER (PARTITION BY m.genre ORDER BY SUM(t.final_price) DESC) AS rank
    FROM fact_ticket_sales t
    JOIN dim_movies m ON t.movie_id = m.movie_id
    GROUP BY m.genre, m.title
)
SELECT genre, title, total_revenue
FROM RankedMovies
WHERE rank <= 5
ORDER BY genre, rank;

-- ข้อ 3: ช่วงเวลาใดของวัน (Time Slot) ที่สร้างรายได้มากที่สุด
SELECT 
    s.time_slot, 
    SUM(t.final_price) AS ticket_revenue
FROM fact_ticket_sales t
JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
GROUP BY s.time_slot 
ORDER BY ticket_revenue DESC;

-- ข้อ 4: Concession Spending Per Head
SELECT 
    SUM(c.total_price) AS total_concession_rev,
    COUNT(DISTINCT t.ticket_sale_id) AS total_tickets,
    ROUND(SUM(c.total_price) / NULLIF(COUNT(DISTINCT t.ticket_sale_id), 0), 2) AS spend_per_head
FROM fact_concession_sales c
CROSS JOIN fact_ticket_sales t;

-- ข้อ 5: ยอด Spending รวมแยกตาม Member Tier
SELECT 
    c.member_tier,
    SUM(t.final_price) AS ticket_spending
FROM dim_customers c
LEFT JOIN fact_ticket_sales t ON c.customer_id = t.customer_id
GROUP BY c.member_tier
ORDER BY ticket_spending DESC;

-- ข้อ 6: ประเภทที่นั่งที่ลูกค้า Platinum นิยมซื้อมากที่สุด
SELECT 
    t.seat_type, 
    COUNT(t.ticket_sale_id) AS total_seats_booked, 
    SUM(t.final_price) AS total_spending
FROM fact_ticket_sales t
JOIN dim_customers c ON t.customer_id = c.customer_id
WHERE c.member_tier = 'Platinum'
GROUP BY t.seat_type 
ORDER BY total_seats_booked DESC;

-- ข้อ 7: ยอดซื้อ Concession ของสมาชิกระดับ Gold / Platinum
SELECT 
    c.member_tier, 
    c_sales.item_name, 
    SUM(c_sales.quantity) AS total_qty, 
    SUM(c_sales.total_price) AS total_spend
FROM fact_concession_sales c_sales
JOIN dim_customers c ON c_sales.customer_id = c.customer_id
WHERE c.member_tier IN ('Gold', 'Platinum')
GROUP BY c.member_tier, c_sales.item_name 
ORDER BY total_spend DESC;

-- ข้อ 8: ยอดขายตั๋วตามประเภทสมาชิกในแต่ละไตรมาส
SELECT 
    c.member_tier, 
    s.show_date,
    COUNT(t.ticket_sale_id) AS tickets_sold,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_customers c ON t.customer_id = c.customer_id
JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
GROUP BY c.member_tier, s.show_date 
ORDER BY total_revenue DESC;

-- ข้อ 9: หนังประเภท (Genre) ใดทำรายได้รวมสูงสุด
SELECT 
    m.genre, 
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_id = m.movie_id
GROUP BY m.genre 
ORDER BY total_revenue DESC;

-- ข้อ 10: รายได้รวมแยกตาม Rating หนัง (R, PG-13, PG)
SELECT 
    m.rating, 
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_id = m.movie_id
GROUP BY m.rating 
ORDER BY total_revenue DESC;

-- ข้อ 11: รายได้เฉลี่ยต่อรอบและรายได้รวมแยกตาม Screen Number
SELECT 
    s.screen_number, 
    ROUND(AVG(t.final_price), 2) AS avg_rev_per_ticket, 
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
GROUP BY s.screen_number 
ORDER BY total_revenue DESC;

-- ข้อ 12: ผลกระทบของหนังความยาว > 150 นาที
SELECT 
    CASE 
        WHEN m.duration_minutes > 150 THEN 'Long (>150 mins)' 
        ELSE 'Standard (<=150 mins)' 
    END AS duration_group,
    COUNT(DISTINCT m.movie_id) AS movie_count,
    COUNT(t.ticket_sale_id) AS tickets_sold,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_id = m.movie_id
GROUP BY 1;

-- ข้อ 13: รายได้และสัดส่วน (%) แยกตามประเภทที่นั่ง
SELECT 
    seat_type, 
    SUM(final_price) AS total_revenue,
    ROUND(SUM(final_price) * 100.0 / NULLIF((SELECT SUM(final_price) FROM fact_ticket_sales), 0), 2) AS revenue_share_pct
FROM fact_ticket_sales
GROUP BY seat_type 
ORDER BY total_revenue DESC;

-- ข้อ 14: สินค้า Concession ขายดีที่สุด (Quantity & Total Price)
SELECT 
    item_name, 
    SUM(quantity) AS total_qty, 
    SUM(total_price) AS total_revenue
FROM fact_concession_sales
GROUP BY item_name 
ORDER BY total_revenue DESC;

-- ข้อ 15: ความสัมพันธ์ของการชมภาพยนตร์ช่วงวันหยุด/วันทำงาน กับการซื้อ Combo Set
SELECT 
    s.day_type,
    CASE 
        WHEN c_sales.item_name LIKE '%Combo%' THEN 'Combo Set' 
        ELSE 'Single Item' 
    END AS product_type,
    SUM(c_sales.quantity) AS total_quantity,
    SUM(c_sales.total_price) AS total_revenue
FROM fact_concession_sales c_sales
JOIN dim_showtimes s ON c_sales.showtime_id = s.showtime_id
GROUP BY s.day_type, 2 
ORDER BY s.day_type, total_revenue DESC;