-- 1. ยอดขายรวม และ จำนวนตั๋วทั้งหมด (KPIs)
SELECT 
    SUM(final_price) AS total_revenue,
    COUNT(ticket_id) AS total_tickets_sold,
    COUNT(DISTINCT ticket_id) AS total_transactions
FROM main.fact_ticket;

-- 2. ยอดขายแยกตามรายชื่อภาพยนตร์ (Revenue by Product Name)
SELECT 
    m.title AS product_name,
    SUM(f.final_price) AS total_revenue,
    COUNT(f.ticket_id) AS tickets_sold
FROM main.fact_ticket f
LEFT JOIN main.dim_movie m ON f.movie_id = m.movie_id
GROUP BY m.title
ORDER BY total_revenue DESC;