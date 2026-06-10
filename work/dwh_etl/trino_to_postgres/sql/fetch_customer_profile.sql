with active_last_90_days as
(	select distinct trim(user_account) as user_account from delta.gold_db.transactions_whizz
	where date_created >= current_date - interval '90' day
	),
active_last_60_days as
(	select distinct trim(user_account) as user_account from delta.gold_db.transactions_whizz
	where date_created >= current_date - interval '60' day
	),
active_last_30_days as
(	select distinct trim(user_account) as user_account from delta.gold_db.transactions_whizz
	where date_created >= current_date - interval '30' day
	),
active_last_7_days as
(	select distinct trim(user_account) as user_account from delta.gold_db.transactions_whizz
	where date_created >= current_date - interval '7' day
	)
SELECT
    ed.customer_name,
    ed.status_ind,
    ed.account_number,
    ed.cust_id,
    ed.cloan_category_description,
    ed.product_desc,
    ed.euro_book_bal,
    ed.account_type,
    ed.opening_date as account_open_date,
    ed.eom_date,
    case
    	when trim(ed.account_number) in (select user_account from active_last_90_days )
    	then 1
    	else 0
    end last_90_days_active,
       case
    	when trim(ed.account_number) in (select user_account from active_last_60_days )
    	then 1
    	else 0
    end last_60_days_active,
      case
    	when trim(ed.account_number) in (select user_account from active_last_30_days )
    	then 1
    	else 0
    end last_30_days_active,
      case
    	when trim(ed.account_number) in (select user_account from active_last_7_days )
    	then 1
    	else 0
    end last_7_days_active,
    case
    	when PRODUCT_DESC in ('VIRTUAL ACCOUNT MOBILE',
    	'NYUMBA YANGU ACCOUNT','TARGET SAVINGS ACCOUNT')
    	then 'Virtual accounts'
    	else 'conventional accounts'
    end as product_categorization,
    dc.primary_mobile_no,
    dc.e_mail,
    dc.customer_id_no,
    cw.date_created as mobile_onboarding_date,
    cw.date_of_reg as mobile_registration_date,
    case
    	when cw.date_created is not null then 1
    	else 0
    end as onboarded_on_mobile,
        case
    	when cw.date_of_reg is not null or cw.date_created is not null then 1
    	else 0
    end as registered_on_mobile
FROM delta.gold_db.eom_deposits ed
LEFT JOIN delta.gold_db.dim_customer dc
    ON dc.customer_id = ed.cust_id
   left join deLta.gold_db.customers_whizz cw
   on trim(cw.document_number) = trim(dc.customer_id_no)
WHERE ed.eom_date = (
      SELECT MAX(eom_date)
      FROM delta.gold_db.eom_deposits)
and ed.opening_date>= timestamp '2016-01-01 00:00:00';
 