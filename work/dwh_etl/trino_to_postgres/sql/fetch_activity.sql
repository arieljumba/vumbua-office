WITH params AS (
    SELECT CAST(CURRENT_DATE - INTERVAL '10' DAY AS DATE) AS cutoff_date
),
-- 1. HARDCODED DATA (Monthly)
manual_data AS (
    SELECT
        CAST(NULL AS VARCHAR) AS cust_id,
        activity_date,
        CAST(0 AS BIGINT) AS txn_count,
        CAST(0 AS DECIMAL(18,2)) AS txn_value,
        active_customers AS is_active,
        CAST('Monthly' AS VARCHAR) AS activity_type
    FROM (
        VALUES
            (DATE '2024-01-31', 17083),
            (DATE '2024-02-29', 16732),
            (DATE '2024-03-31', 17341),
            (DATE '2024-04-30', 17241),
            (DATE '2024-05-31', 16417),
            (DATE '2024-06-30', 16014),
            (DATE '2024-07-31', 16182),
            (DATE '2024-08-31', 17704),
            (DATE '2024-09-30', 17722),
            (DATE '2024-10-31', 18048),
            (DATE '2024-11-30', 17546),
            (DATE '2024-12-31', 16478),
            (DATE '2025-01-31', 16772),
            (DATE '2025-02-28', 17525),
            (DATE '2025-03-31', 18256),
            (DATE '2025-04-30', 18098),
            (DATE '2025-05-31', 18922),
            (DATE '2025-06-30', 18715),
            (DATE '2025-07-31', 19039),
            (DATE '2025-08-31', 18328),
            (DATE '2025-09-30', 18634),
            (DATE '2025-10-31', 19126),
            (DATE '2025-11-30', 18821),
            (DATE '2025-12-31', 18926),
            (DATE '2026-01-31', 18878),
            (DATE '2026-02-28', 18529),
            (DATE '2026-03-31', 19849),
            (DATE '2026-04-30', 19891)
    ) AS t(activity_date, active_customers)
),
-- 2. GET LAST MANUAL DATE
last_manual AS (
    SELECT MAX(activity_date) AS last_manual_date
    FROM manual_data
),
-- 3. HISTORICAL (Monthly AFTER manual ends)
historical AS (
    SELECT
        CAST(vkt.user_account AS VARCHAR) AS cust_id,
        CAST(last_day_of_month(vkt.date_created) AS DATE) AS activity_date,
        COUNT(*) AS txn_count,
        CAST(COALESCE(SUM(vkt.amount),0) AS DECIMAL(18,2)) AS txn_value,
        1 AS is_active,
        CAST('Monthly' AS VARCHAR) AS activity_type
    FROM delta.gold_db.transactions_whizz vkt
    CROSS JOIN params p
    CROSS JOIN last_manual lm
    WHERE CAST(last_day_of_month(vkt.date_created) AS DATE) > lm.last_manual_date
      AND vkt.service_code IN (
            'AIRTIME_OTHER','AIRTIME_SELF','ATO','ATS','MPESA_SEND','MPS',
            'FX_FT_BUY','FXFTBUY','CHCKBKREQ','M2B','MPESA_TO_BANK','EFT',
            'BALANCE_ENQUIRY','FUNDS_TRANSFER','IFT','MB2BPT','MPESA_PAY_TILL',
            'MB2BPB','MPESA_PAY_BILL','MINI_STATEMENT','NYSFTCH','NYS_CR',
            'NYS_CREATE','NYS_TOPUP','NYS_TP','PLNKA2A','PLNKA2C','PLNKA2P',
            'FT_RTGS','RTGS','FX_FT_SELL','FXFTSELL','TGT_CR','TGT_CREATE',
            'TGT_FETCH','TGT_PR_CLS','TGT_PREMATURE_CLOSE','TGT_UN','TGT_UN_CLS',
            'TGT_UNLOCK','TGT_UNLOCK_CLOSE','STATS_TERM_DEPOSIT','TGT_TOPUP',
            'TGT_TP','BILL_PAYMENT','BPS','STDO_CR',
            'MLRP','MLSTAT','PRUSPN','PLNKLKP','MLTOPUP','ML_TOPUP','PCP',
            'STATS_NYUMBA_YANGU','STATS_FX','CHANGE_PIN','FXCREATE','PAYINST',
            'IFT_FCY','FXNEGFTBUY'
      )
    GROUP BY 1,2
),
-- 4. LAST 10 DAYS (Daily AFTER manual ends)
last_10_days AS (
    SELECT
        CAST(vkt.user_account AS VARCHAR) AS cust_id,
        CAST(vkt.date_created AS DATE) AS activity_date,
        COUNT(*) AS txn_count,
        CAST(COALESCE(SUM(vkt.amount),0) AS DECIMAL(18,2)) AS txn_value,
        1 AS is_active,
        CAST('Daily' AS VARCHAR) AS activity_type
    FROM delta.gold_db.transactions_whizz vkt
    CROSS JOIN params p
    CROSS JOIN last_manual lm
    WHERE CAST(vkt.date_created AS DATE) >= p.cutoff_date
      AND CAST(vkt.date_created AS DATE) > lm.last_manual_date
      AND vkt.service_code IN (
            'AIRTIME_OTHER','AIRTIME_SELF','ATO','ATS','MPESA_SEND','MPS',
            'FX_FT_BUY','FXFTBUY','CHCKBKREQ','M2B','MPESA_TO_BANK','EFT',
            'BALANCE_ENQUIRY','FUNDS_TRANSFER','IFT','MB2BPT','MPESA_PAY_TILL',
            'MB2BPB','MPESA_PAY_BILL','MINI_STATEMENT','NYSFTCH','NYS_CR',
            'NYS_CREATE','NYS_TOPUP','NYS_TP','PLNKA2A','PLNKA2C','PLNKA2P',
            'FT_RTGS','RTGS','FX_FT_SELL','FXFTSELL','TGT_CR','TGT_CREATE',
            'TGT_FETCH','TGT_PR_CLS','TGT_PREMATURE_CLOSE','TGT_UN','TGT_UN_CLS',
            'TGT_UNLOCK','TGT_UNLOCK_CLOSE','STATS_TERM_DEPOSIT','TGT_TOPUP',
            'TGT_TP','BILL_PAYMENT','BPS','STDO_CR',
            'MLRP','MLSTAT','PRUSPN','PLNKLKP','MLTOPUP','ML_TOPUP','PCP',
            'STATS_NYUMBA_YANGU','STATS_FX','CHANGE_PIN','FXCREATE','PAYINST',
            'IFT_FCY','FXNEGFTBUY'
      )
    GROUP BY 1,2
)
-- FINAL RESULT
SELECT *
FROM manual_data
UNION ALL
SELECT *
FROM historical
UNION ALL
SELECT *
FROM last_10_days
ORDER BY activity_date, cust_id;