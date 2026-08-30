{{ config(
    materialized = 'table'
) }}

with concession as (
    select
        customer_id,
        sale_date,
        total_price as amount,
        'concession' as sales_type
    from {{ ref('fact_concession_sales') }}
),

tickets as (
    select
        customer_id,
        show_date as sale_date,
        final_price as amount,
        'ticket' as sales_type
    from {{ ref('fact_ticket_sales') }}
),

all_sales as (
    select * from concession
    union all
    select * from tickets
)

select
    customer_id,
    sale_date,
    amount,
    sales_type,
    current_localtimestamp() as insertion_timestamp
from all_sales