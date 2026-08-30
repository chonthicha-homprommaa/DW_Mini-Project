with source as (
    select
        customer_id,
        first_name,
        last_name,
        email,
        member_tier,
        ingestion_timestamp as insertion_timestamp
    from {{ ref('stg_customers') }}
),

unique_source as (
    select
        *,
        row_number() over(partition by customer_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1