-- =========================================================
-- CINEMA DW : 15 BUSINESS QUESTIONS
-- =========================================================


-- =========================================================
-- Q1: รายได้รวมจากการขายตั๋วภาพยนตร์ทั้งหมด
-- =========================================================

SELECT
    SUM(final_price) AS total_ticket_revenue
FROM fact_ticket_sales;


-- =========================================================
-- Q2: ช่วงเวลาใดของวันที่สร้างรายได้จากการขายตั๋วมากที่สุด
-- =========================================================

SELECT
    CASE
        WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP))
            BETWEEN 6 AND 11 THEN 'Morning'
        WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP))
            BETWEEN 12 AND 16 THEN 'Afternoon'
        WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP))
            BETWEEN 17 AND 23 THEN 'Evening'
        ELSE 'Unknown'
    END AS time_slot,
    SUM(t.final_price) AS ticket_revenue
FROM fact_ticket_sales t
JOIN dim_showtimes s
    ON t.showtime_id = s.showtime_id
GROUP BY 1
ORDER BY ticket_revenue DESC;


-- =========================================================
-- Q3: ยอดซื้อ Concession เฉลี่ยต่อผู้เข้าชม 1 คน
-- =========================================================

SELECT
    (SELECT COALESCE(SUM(total_price), 0)
     FROM fact_concession_sales) AS total_concession_revenue,

    (SELECT COUNT(ticket_id)
     FROM fact_ticket_sales) AS total_tickets,

    ROUND(
        (SELECT COALESCE(SUM(total_price), 0)
         FROM fact_concession_sales)
        /
        NULLIF(
            (SELECT COUNT(ticket_id)
             FROM fact_ticket_sales),
            0
        ),
        2
    ) AS spend_per_head;


-- =========================================================
-- Q4: สัดส่วนรายได้ระหว่าง Ticket และ Concession
-- =========================================================

WITH revenues AS (
    SELECT
        'Ticket Revenue' AS revenue_type,
        SUM(final_price) AS revenue
    FROM fact_ticket_sales

    UNION ALL

    SELECT
        'Concession Revenue' AS revenue_type,
        SUM(total_price) AS revenue
    FROM fact_concession_sales
)
SELECT
    revenue_type,
    revenue,
    ROUND(
        revenue * 100.0 /
        NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS revenue_percentage
FROM revenues
ORDER BY revenue DESC;


-- =========================================================
-- Q5: ราคาตั๋วเฉลี่ยต่อใบ
-- =========================================================

SELECT
    ROUND(AVG(final_price), 2) AS average_ticket_price
FROM fact_ticket_sales;


-- =========================================================
-- Q6: Top 5 ภาพยนตร์ที่ทำรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    m.title,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m
    ON t.movie_id = m.movie_id
GROUP BY m.title
ORDER BY total_revenue DESC
LIMIT 5;


-- =========================================================
-- Q7: Genre ใดทำรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    m.genre,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m
    ON t.movie_id = m.movie_id
GROUP BY m.genre
ORDER BY total_revenue DESC;


-- =========================================================
-- Q8: Rating ใดทำรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    m.rating,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_movies m
    ON t.movie_id = m.movie_id
GROUP BY m.rating
ORDER BY total_revenue DESC;


-- =========================================================
-- Q9: Screen Number ใดทำรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    s.screen_number,
    SUM(t.final_price) AS total_revenue
FROM fact_ticket_sales t
JOIN dim_showtimes s
    ON t.showtime_id = s.showtime_id
GROUP BY s.screen_number
ORDER BY total_revenue DESC;


-- =========================================================
-- Q10: ยอด Spending รวมแยกตาม Member Tier
-- =========================================================

SELECT
    CASE
        WHEN c.member_tier IS NULL
             OR TRIM(c.member_tier) = ''
            THEN 'Non-Member'
        ELSE c.member_tier
    END AS member_tier,
    SUM(t.final_price) AS total_spending
FROM fact_ticket_sales t
LEFT JOIN dim_customers c
    ON t.customer_id = c.customer_id
GROUP BY 1
ORDER BY total_spending DESC;


-- =========================================================
-- Q11: จำนวนตั๋วแยกตาม Member Tier
-- =========================================================

SELECT
    CASE
        WHEN c.member_tier IS NULL
             OR TRIM(c.member_tier) = ''
            THEN 'Non-Member'
        ELSE c.member_tier
    END AS member_tier,
    COUNT(t.ticket_id) AS total_tickets
FROM fact_ticket_sales t
LEFT JOIN dim_customers c
    ON t.customer_id = c.customer_id
GROUP BY 1
ORDER BY total_tickets DESC;


-- =========================================================
-- Q12: ประเภทที่นั่งที่ลูกค้า Platinum นิยมมากที่สุด
-- =========================================================

SELECT
    t.seat_type,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(t.final_price) AS total_spending
FROM fact_ticket_sales t
JOIN dim_customers c
    ON t.customer_id = c.customer_id
WHERE c.member_tier = 'Platinum'
GROUP BY t.seat_type
ORDER BY total_tickets DESC;


-- =========================================================
-- Q13: ประเภทที่นั่งใดสร้างรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    seat_type,
    SUM(final_price) AS total_revenue,
    ROUND(
        SUM(final_price) * 100.0 /
        NULLIF(
            (SELECT SUM(final_price)
             FROM fact_ticket_sales),
            0
        ),
        2
    ) AS revenue_share_pct
FROM fact_ticket_sales
WHERE seat_type IS NOT NULL
GROUP BY seat_type
ORDER BY total_revenue DESC;


-- =========================================================
-- Q14: สินค้า Concession ที่สมาชิก Gold และ Platinum
-- นิยมซื้อมากที่สุด
-- =========================================================

SELECT
    cs.item_name,
    SUM(cs.quantity) AS total_quantity,
    SUM(cs.total_price) AS total_spending
FROM fact_concession_sales cs
JOIN dim_customers c
    ON cs.customer_id = c.customer_id
WHERE c.member_tier IN ('Gold', 'Platinum')
GROUP BY cs.item_name
ORDER BY total_quantity DESC;


-- =========================================================
-- Q15: หมวดหมู่สินค้า Concession ใดทำรายได้รวมสูงที่สุด
-- =========================================================

SELECT
    CASE
        WHEN LOWER(item_name) LIKE '%combo%'
            THEN 'Combo Set'
        WHEN LOWER(item_name) LIKE '%popcorn%'
            THEN 'Popcorn'
        WHEN LOWER(item_name) LIKE '%soda%'
             OR LOWER(item_name) LIKE '%water%'
            THEN 'Beverage'
        ELSE 'Other'
    END AS category,
    SUM(quantity) AS total_quantity,
    SUM(total_price) AS total_revenue
FROM fact_concession_sales
WHERE item_name IS NOT NULL
GROUP BY 1
ORDER BY total_revenue DESC;