15 Business Questions)
-- 1. มุมมองด้านรายได้และการขาย (Revenue & Sales Analysis)
-- ------------------------------------------------------------
-- Q1: รายได้รวมจากการขายตั๋วและสินค้า Concession แยกตามเดือน/ไตรมาส
SELECT 
    d.year,
    d.quarter,
    d.month_name,
    SUM(t.total_price) AS ticket_revenue,
    SUM(c.total_price) AS concession_revenue,
    (SUM(t.total_price) + SUM(c.total_price)) AS total_revenue
FROM dim_date d
LEFT JOIN fact_ticket_sales t ON d.date_key = t.date_key
LEFT JOIN fact_concession_sales c ON d.date_key = c.date_key
GROUP BY d.year, d.quarter, d.month, d.month_name
ORDER BY d.year, d.month;

-- Q2: 5 อันดับ หนังทำเงินสูงสุด (Box Office) ในแต่ละประเภทหนัง (Genre)
WITH RankedMovies AS (
    SELECT 
        m.genre,
        m.title,
        SUM(t.total_price) AS total_gross_revenue,
        ROW_NUMBER() OVER (PARTITION BY m.genre ORDER BY SUM(t.total_price) DESC) AS rank
    FROM fact_ticket_sales t
    JOIN dim_movies m ON t.movie_key = m.movie_key
    GROUP BY m.genre, m.title
)
SELECT genre, title, total_gross_revenue
FROM RankedMovies
WHERE rank <= 5
ORDER BY genre, rank;

-- Q3: ช่วงเวลาขายตั๋วดีที่สุดของวัน (Time Slot: เช้า, บ่าย, เย็น, ดึก)
SELECT 
    s.time_slot, -- Morning, Afternoon, Evening, Late Night
    SUM(t.total_price) AS ticket_revenue,
    COUNT(t.ticket_id) AS total_tickets_sold
FROM fact_ticket_sales t
JOIN dim_showtimes s ON t.showtime_key = s.showtime_key
GROUP BY s.time_slot
ORDER BY ticket_revenue DESC;

-- Q4: ยอดขาย Concession เฉลี่ยต่อผู้เข้าชม 1 คน (Concession Spend Per Head)
SELECT 
    SUM(c.total_price) AS total_concession_revenue,
    COUNT(DISTINCT t.customer_key) AS total_attendees,
    ROUND(SUM(c.total_price) / COUNT(DISTINCT t.customer_key), 2) AS spend_per_head
FROM fact_ticket_sales t
FULL OUTER JOIN fact_concession_sales c ON t.customer_key = c.customer_key;


-- ------------------------------------------------------------
-- 2. มุมมองด้านลูกค้าและสมาชิก (Customer & Membership Analysis)
-- ------------------------------------------------------------

-- Q5: ยอด spending รวมของสมาชิกแต่ละระดับ (Silver, Gold, Platinum)
SELECT 
    c.member_tier,
    SUM(t.total_price) AS ticket_spending,
    SUM(cs.total_price) AS concession_spending,
    (SUM(t.total_price) + SUM(cs.total_price)) AS total_spending
FROM dim_customers c
LEFT JOIN fact_ticket_sales t ON c.customer_key = t.customer_key
LEFT JOIN fact_concession_sales cs ON c.customer_key = cs.customer_key
GROUP BY c.member_tier
ORDER BY total_spending DESC;

-- Q6: ประเภทที่นั่งยอดนิยมของลูกค้าระดับ Platinum (Normal, Honeymoon, VIP)
SELECT 
    t.seat_type,
    COUNT(t.ticket_id) AS total_seats_booked,
    SUM(t.total_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_customers c ON t.customer_key = c.customer_key
WHERE c.member_tier = 'Platinum'
GROUP BY t.seat_type
ORDER BY total_seats_booked DESC;

-- Q7: สมาชิกกลุ่มใดที่ซื้อสินค้า Concession มากที่สุด และสินค้ายอดนิยมของกลุ่ม Gold/Platinum
SELECT 
    c.member_tier,
    cs.item_category,
    cs.item_name,
    SUM(cs.quantity) AS total_quantity_bought,
    SUM(cs.total_price) AS total_amount_spent
FROM fact_concession_sales cs
JOIN dim_customers c ON cs.customer_key = c.customer_key
WHERE c.member_tier IN ('Gold', 'Platinum')
GROUP BY c.member_tier, cs.item_category, cs.item_name
ORDER BY c.member_tier, total_amount_spent DESC;

-- Q8: ยอดขายตั๋วจำแนกตามประเภทสมาชิกในแต่ละไตรมาส (Customer Loyalty)
SELECT 
    d.year,
    d.quarter,
    c.member_tier,
    SUM(t.total_price) AS quarterly_ticket_sales
FROM fact_ticket_sales t
JOIN dim_customers c ON t.customer_key = c.customer_key
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY d.year, d.quarter, c.member_tier
ORDER BY d.year, d.quarter, c.member_tier;


-- ------------------------------------------------------------
-- 3. มุมมองด้านภาพยนตร์และการฉาย (Movie & Showtimes Performance Analysis)
-- ------------------------------------------------------------

-- Q9: ประเภทหนัง (Genre) ที่ทำรายได้รวมสูงที่สุด
SELECT 
    m.genre,
    SUM(t.total_price) AS total_revenue,
    COUNT(t.ticket_id) AS total_tickets_sold
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_key = m.movie_key
GROUP BY m.genre
ORDER BY total_revenue DESC;

-- Q10: เรตติ้งภาพยนตร์ (Rating: R, PG-13, PG) ที่ทำรายได้สูงสุด
SELECT 
    m.rating,
    SUM(t.total_price) AS total_revenue,
    AVG(t.total_price) AS avg_ticket_price
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_key = m.movie_key
GROUP BY m.rating
ORDER BY total_revenue DESC;

-- Q11: โรงฉายหมายเลขใด (Screen Number) มีรายได้เฉลี่ยต่อรอบสูงสุด
SELECT 
    s.screen_number,
    COUNT(DISTINCT s.showtime_id) AS total_showtimes,
    SUM(t.total_price) AS total_revenue,
    ROUND(SUM(t.total_price) / COUNT(DISTINCT s.showtime_id), 2) AS avg_revenue_per_showtime
FROM fact_ticket_sales t
JOIN dim_showtimes s ON t.showtime_key = s.showtime_key
GROUP BY s.screen_number
ORDER BY avg_revenue_per_showtime DESC;

-- Q12: ผลกระทบของหนังที่ยาวเกิน 150 นาที ต่อรอบฉายและรายได้
SELECT 
    CASE WHEN m.duration_minutes > 150 THEN 'Long (>150 mins)' ELSE 'Standard (<=150 mins)' END AS movie_length_category,
    COUNT(DISTINCT m.movie_key) AS total_movies,
    COUNT(DISTINCT s.showtime_id) AS total_showtimes,
    SUM(t.total_price) AS total_revenue,
    ROUND(SUM(t.total_price) / COUNT(DISTINCT m.movie_key), 2) AS avg_revenue_per_movie
FROM fact_ticket_sales t
JOIN dim_movies m ON t.movie_key = m.movie_key
JOIN dim_showtimes s ON t.showtime_key = s.showtime_key
GROUP BY CASE WHEN m.duration_minutes > 150 THEN 'Long (>150 mins)' ELSE 'Standard (<=150 mins)' END;


-- ------------------------------------------------------------
-- 4. มุมมองด้านที่นั่งและพฤติกรรมการบริโภค (Seat & Concession Trend Analysis)
-- ------------------------------------------------------------

-- Q13: รายได้และสัดส่วนเปอร์เซ็นต์ของที่นั่งแต่ละประเภท (Normal, Honeymoon, VIP)
SELECT 
    t.seat_type,
    SUM(t.total_price) AS total_seat_revenue,
    ROUND(SUM(t.total_price) * 100.0 / SUM(SUM(t.total_price)) OVER(), 2) AS revenue_percentage
FROM fact_ticket_sales t
GROUP BY t.seat_type
ORDER BY total_seat_revenue DESC;

-- Q14: สินค้า Concession ขายดีที่สุดเชิงปริมาณและเชิงรายได้
SELECT 
    cs.item_name,
    cs.item_category,
    SUM(cs.quantity) AS total_quantity_sold,
    SUM(cs.total_price) AS total_concession_revenue
FROM fact_concession_sales cs
GROUP BY cs.item_name, cs.item_category
ORDER BY total_concession_revenue DESC;

-- Q15: ความสัมพันธ์ของการซื้อ Combo Set ในวันหยุด vs วันทำงาน
SELECT 
    d.is_weekend, -- TRUE (วันหยุด), FALSE (วันทำงาน)
    SUM(CASE WHEN cs.item_category = 'Combo Set' THEN cs.quantity ELSE 0 END) AS combo_sets_sold,
    SUM(cs.total_price) AS total_concession_revenue
FROM fact_concession_sales cs
JOIN dim_date d ON cs.date_key = d.date_key
GROUP BY d.is_weekend;