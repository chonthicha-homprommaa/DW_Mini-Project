-- =========================================================
-- CINEMA DW : 15 BUSINESS QUESTIONS
-- Tables:
-- fact_ticket_sales
-- fact_concession_sales
-- dim_movies
-- dim_customers
-- dim_showtimes
-- =========================================================


-- =========================================================
-- ข้อ 1: รายได้จากการขายตั๋วรายเดือน / ไตรมาส
-- =========================================================

-- รายเดือน
SELECT
    DATE_TRUNC('month', show_date) AS month,
    SUM(final_price) AS ticket_revenue
FROM fact_ticket_sales
GROUP BY 1
ORDER BY 1;

-- รายไตรมาส
SELECT
    EXTRACT(YEAR FROM show_date) AS year,
    EXTRACT(QUARTER FROM show_date) AS quarter,
    SUM(final_price) AS ticket_revenue
FROM fact_ticket_sales
GROUP BY 1, 2
ORDER BY 1, 2;


-- =========================================================
-- ข้อ 2: Top 5 หนังทำรายได้สูงสุด แยกตาม Genre
-- =========================================================

WITH RankedMovies AS (
    SELECT
        m.genre,
        m.title,
        SUM(t.final_price) AS total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY m.genre
            ORDER BY SUM(t.final_price) DESC
        ) AS movie_rank
    FROM fact_ticket_sales t
    JOIN dim_movies m
        ON t.movie_id = m.movie_id
    GROUP BY m.genre, m.title
)
SELECT
    genre,
    title,
    total_revenue
FROM RankedMovies
WHERE movie_rank <= 5
ORDER BY genre, movie_rank;


-- =========================================================
-- ข้อ 3: ช่วงเวลาใดของวัน (Time Slot)
-- สร้างรายได้จากการขายตั๋วมากที่สุด
-- =========================================================

SELECT
    CASE
        WHEN EXTRACT(
            HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)
        ) BETWEEN 6 AND 11
            THEN 'Morning'

        WHEN EXTRACT(
            HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)
        ) BETWEEN 12 AND 16
            THEN 'Afternoon'

        ELSE 'Evening'
    END AS time_slot,

    SUM(t.final_price) AS ticket_revenue

FROM fact_ticket_sales t
JOIN dim_showtimes s
    ON t.showtime_id = s.showtime_id

GROUP BY 1
ORDER BY ticket_revenue DESC;


-- =========================================================
-- ข้อ 4: Concession Spending Per Head
-- ยอดซื้อ Concession เฉลี่ยต่อผู้เข้าชม 1 คน
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
-- ข้อ 5: ยอด Spending รวมแยกตาม Member Tier
-- =========================================================

SELECT
    CASE
        WHEN c.member_tier IS NULL
             OR TRIM(c.member_tier) = ''
            THEN 'Non-Member'
        ELSE c.member_tier
    END AS member_tier,

    SUM(t.final_price) AS ticket_spending

FROM dim_customers c
LEFT JOIN fact_ticket_sales t
    ON c.customer_id = t.customer_id

GROUP BY 1
ORDER BY ticket_spending DESC;


-- =========================================================
-- ข้อ 6: ประเภทที่นั่งที่ลูกค้า Platinum
-- นิยมซื้อมากที่สุด
-- =========================================================

SELECT
    t.seat_type,
    COUNT(t.ticket_id) AS total_seats_booked,
    SUM(t.final_price) AS total_spending

FROM fact_ticket_sales t
JOIN dim_customers c
    ON t.customer_id = c.customer_id

WHERE c.member_tier = 'Platinum'

GROUP BY t.seat_type
ORDER BY total_seats_booked DESC;


-- =========================================================
-- ข้อ 7: ยอดซื้อ Concession
-- ของสมาชิก Gold / Platinum
-- =========================================================

SELECT
    c.member_tier,
    cs.item_name,
    SUM(cs.quantity) AS total_qty,
    SUM(cs.total_price) AS total_spend

FROM fact_concession_sales cs
JOIN dim_customers c
    ON cs.customer_id = c.customer_id

WHERE c.member_tier IN ('Gold', 'Platinum')

GROUP BY
    c.member_tier,
    cs.item_name

ORDER BY total_spend DESC;


-- =========================================================
-- ข้อ 8: ยอดขายตั๋วตามประเภทสมาชิกในแต่ละไตรมาส
-- =========================================================

SELECT
    CASE
        WHEN c.member_tier IS NULL
             OR TRIM(c.member_tier) = ''
            THEN 'Non-Member'
        ELSE c.member_tier
    END AS member_tier,

    EXTRACT(YEAR FROM t.show_date) AS year,
    EXTRACT(QUARTER FROM t.show_date) AS quarter,

    COUNT(t.ticket_id) AS tickets_sold,
    SUM(t.final_price) AS total_revenue

FROM fact_ticket_sales t
JOIN dim_customers c
    ON t.customer_id = c.customer_id

GROUP BY 1, 2, 3

ORDER BY
    year,
    quarter,
    total_revenue DESC;


-- =========================================================
-- ข้อ 9: Genre ใดทำรายได้รวมสูงสุด
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
-- ข้อ 10: รายได้รวมแยกตาม Rating หนัง
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
-- ข้อ 11: ราคาตั๋วเฉลี่ยและรายได้รวม
-- แยกตาม Screen Number
-- =========================================================

SELECT
    s.screen_number,

    ROUND(
        AVG(t.final_price),
        2
    ) AS avg_ticket_price,

    SUM(t.final_price) AS total_revenue

FROM fact_ticket_sales t
JOIN dim_showtimes s
    ON t.showtime_id = s.showtime_id

GROUP BY s.screen_number
ORDER BY total_revenue DESC;


-- =========================================================
-- ข้อ 12: ผลกระทบของหนังที่มีความยาว > 150 นาที
-- =========================================================

SELECT
    CASE
        WHEN m.duration_min > 150
            THEN 'Long (>150 mins)'
        ELSE 'Standard (<=150 mins)'
    END AS duration_group,

    COUNT(DISTINCT m.movie_id) AS movie_count,
    COUNT(t.ticket_id) AS tickets_sold,
    SUM(t.final_price) AS total_revenue

FROM fact_ticket_sales t
JOIN dim_movies m
    ON t.movie_id = m.movie_id

GROUP BY 1
ORDER BY total_revenue DESC;


-- =========================================================
-- ข้อ 13: รายได้และสัดส่วนรายได้ (%)
-- แยกตามประเภทที่นั่ง
-- =========================================================

SELECT
    seat_type,

    SUM(final_price) AS total_revenue,

    ROUND(
        SUM(final_price) * 100.0
        /
        NULLIF(
            (
                SELECT SUM(final_price)
                FROM fact_ticket_sales
            ),
            0
        ),
        2
    ) AS revenue_share_pct

FROM fact_ticket_sales

WHERE seat_type IS NOT NULL

GROUP BY seat_type
ORDER BY total_revenue DESC;


-- =========================================================
-- ข้อ 14: สินค้า Concession ขายดีที่สุด
-- Quantity & Revenue
-- =========================================================

SELECT
    item_name,
    SUM(quantity) AS total_qty,
    SUM(total_price) AS total_revenue

FROM fact_concession_sales

WHERE item_name IS NOT NULL

GROUP BY item_name
ORDER BY total_revenue DESC;


-- =========================================================
-- ข้อ 15: รายได้ Concession แยกตามหมวดหมู่สินค้า
--
-- เปลี่ยนจากคำถามวันหยุด/วันทำงาน
-- เพราะ fact_concession_sales ไม่มี showtime_id
-- จึงไม่ควร JOIN dim_showtimes แบบไม่มี relationship จริง
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

    SUM(quantity) AS total_qty,
    SUM(total_price) AS total_revenue

FROM fact_concession_sales

GROUP BY 1
ORDER BY total_revenue DESC;