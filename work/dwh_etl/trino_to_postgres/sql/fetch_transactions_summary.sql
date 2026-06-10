with mobile_transactions as
(
select
	cast(tw.date_created as date) as transaction_date,
	case
		when tw.amount <= 1000000 then tw.amount
		else 0
	end as transaction_amount,
	case
		when channel = 1 then 'Android'
		when channel = 2 then 'iOS'
		when channel = 8 then 'Whatsap'
		when channel = 9 then 'Portal'
		else 'other'
	end as transaction_channel,
	case
		when tw.service_code in ('AIRTIME_OTHER' , 'AIRTIME_SELF', 'ATO', 'ATS') then 'Airtime Purchase'
		when tw.service_code in ('MPESA_SEND' , 'MPS') then 'B2C'
		when tw.service_code in ('FX_FT_BUY' , 'FXFTBUY') then 'Buy FX'
		when tw.service_code in ('CHCKBKREQ') then 'Cheque Book Request'
		when tw.service_code in ('M2B' , 'MPESA_TO_BANK') then 'Direct Deposits'
		when tw.service_code in ('EFT') then 'EFT Transfers'
		--  WHEN tw.service_code IN ('BALANCE_ENQUIRY') THEN 'General Balance Enquiry'
		when tw.service_code in ('FUNDS_TRANSFER' , 'IFT') then 'Internal Funds Transfer'
		when tw.service_code in ('MB2BPT' , 'MPESA_PAY_TILL') then 'Merchant Payments: BuyGoods'
		when tw.service_code in ('MB2BPB' , 'MPESA_PAY_BILL') then 'Merchant Payments: Paybill'
		when tw.service_code in ('MINI_STATEMENT') then 'Mini Statement Fetch'
		when tw.service_code in ('NYSFTCH') then 'Nyumba Yangu Account Fetch'
		when tw.service_code in ('NYS_CR' , 'NYS_CREATE') then 'Nyumba Yangu Create'
		when tw.service_code in ('NYS_TOPUP' , 'NYS_TP') then 'Nyumba Yangu Top Up'
		when tw.service_code in ('PLNKA2A' , 'PLNKA2C', 'PLNKA2P') then 'Pesalink'
		when tw.service_code in ('FT_RTGS' , 'RTGS') then 'RTGS Transfers'
		when tw.service_code in ('FX_FT_SELL' , 'FXFTSELL') then 'Sell FX'
		when tw.service_code in ('TGT_CR' , 'TGT_CREATE') then 'Target Save account creation'
		when tw.service_code in ('TGT_FETCH') then 'Target Save Account Fetch'
		when tw.service_code in ('TGT_PR_CLS' , 'TGT_PREMATURE_CLOSE', 'TGT_UN', 'TGT_UN_CLS', 'TGT_UNLOCK', 'TGT_UNLOCK_CLOSE') then 'Target Save Redemption'
		when tw.service_code in ('STATS_TERM_DEPOSIT') then 'Target Save Statement Fetch'
		when tw.service_code in ('TGT_TOPUP' , 'TGT_TP') then 'Target Save Topup'
		when tw.service_code in ('BILL_PAYMENT' , 'BPS') then 'Utility Bill Payment'
		when tw.service_code in ('BALANCE_ENQUIRY') then 'Balance Enquiry'
		when tw.service_code = 'STDO_CR'
		and tw.extra3 like '%*0'
                then 'Nyumba Yangu STO setup'
		when tw.service_code = 'STDO_CR'
		and tw.extra3 like '%*1' then 'Target Save STO setup'
		else 'Others'
	end as transaction_type,
	case
		/* ---------------------- SUCCESS ---------------------- */
		when tw.active = 1 then 'Successful'
		when tw.active = 6
		and lower(tw.cbs_response_extra5) like '%success%'
    then 'Successful'
		when lower(tw.status_message) like '%success%'
		and tw.active > 104 then 'Successful'
		when lower(tw.status_message) like '%success%'
		and tw.active > 104 then 'Successful'
		when tw.active = 5 then 'Successful'
    /* ---------------------- FAILED (nested CASE) ---------- */
		else
        case
			/* -------- CUSTOMER ERRORS -------- */
			when lower(tw.status_message) like '%insufficient bal%'
			or lower(tw.status_message) like '%balance%'
			or lower(tw.status_message) like '%sufficient funds%'
            then 'Customer: Insufficient Balance'
			when lower(tw.status_message) like '%password%'
			or lower(tw.status_message) like '%pin%'
			or lower(tw.status_message) like '%username%'
			or lower(tw.status_message) like '%credential%'
			or lower(tw.status_message) like '%user_status_on_otp_self_reset%'
			or lower(tw.status_message) like '%status_user_on_otp%'
			or lower(tw.status_message) like '%status_user_pin_status_blocked%'
			or lower(tw.status_message) like '%changed%sim%card%'
            then 'Customer: Incorrect PIN/Credentials'
			when lower(tw.status_message) like '%changed%sim%card%'
            then 'Customer: SIM Reset'
			when lower(tw.status_message) like '%allowed minimum%'
			or lower(tw.status_message) like '%allowed max%'
			or lower(tw.status_message) like '%limit%'
			or lower(tw.status_message) like '%input amount%'
            then 'Customer: Transaction Limits'
			when lower(tw.status_message) like '%contains more than%'
			or lower(tw.status_message) like '%dealer_rate%'
			or lower(tw.status_message) like '%initiator information%'
			or lower(tw.status_message) like '%cents should have%'
			or lower(tw.status_message) like '%cannot be more than%'
			or lower(tw.status_message) like '%are_less_than_declared%'
			or lower(tw.status_message) like '%invalid value(s) supplied in the request%'
			or lower(tw.status_message) like '%invalid%organization%'
			or lower(tw.status_message) like '%account%reference%invalid%'
			or lower(tw.status_message) like '%recipient%invalid%'
			or lower(tw.status_message) like '%mobile%number%invalid%'
			or lower(tw.status_message) like '%two%currencies%'
			or lower(tw.status_message) like '%amount_on_which_the_tax%'
			or lower(tw.status_message) like '%request%cancelled%by%user%'
			or lower(tw.status_message) like '%no%response%from%user%'
			or lower(tw.status_message) like '%transaction%cannot%executed%selected%product%'
			or lower(tw.status_message) like '%transaction%cancelled%'
			or lower(tw.status_message) like '%account%not%found%'
			or lower(tw.status_message) like '%service%cannot%process%transactions%specified%customer%type%'
			or lower(tw.status_message) like '%transaction%validation%recipient%failed%'
            then 'Customer: Input Issues'
			when lower(tw.status_message) like '%not activated for pesalink service%'
            then 'Customer: Account not activated for pesalink'
			when lower(tw.status_message) like '%profile has been blocked%'
			or lower(tw.status_message) like '%reactivate your app%'
            then 'Customer: Account blocked/not activated'
            /* -------- PEER COMM ERRORS -------- */
			when lower(tw.status_message) like '%prft024%'
			or lower(tw.status_message) like '%prft026%'
			or lower(tw.status_message) like '%prft044%'
			or lower(tw.status_message) like '%prft051%'
			or lower(tw.status_message) like '%tcpipconnection::readdata%'
			or lower(tw.status_message) like '%tcpipconnection::writedata%'
			or lower(tw.status_message) like '%socketexception%'
			or lower(tw.status_message) like '%forcibly closed by the remote host%'
			or lower(tw.status_message) like '%jsonobject[t2102v_standingordersmanagementresponse%'
			or lower(tw.status_message) like '%cfbdynamicmessage::parseforcommerror%'
			or lower(tw.status_message) like '%cfbdynamicmessage::parseforservererror%'
			or lower(tw.status_message) like '%tirm030e%'
			or lower(tw.status_message) like '%application failed - updates have been backed out%'
			or lower(tw.status_message) like '%ift exception%'
			or lower(tw.status_message) like '%technical http operation failed%'
			or lower(tw.status_message) like '%statuscode: 400%'
			or lower(tw.status_message) like '%evaluated to null or missing%'
            then 'Profits: Peer Communication errors'
            /* -------- SMS GATEWAY -------- */
			when lower(tw.status_message) like '%error occurred during processing of your request%'
            then 'SMS Gateway Errors'
            /* -------- SAFARICOM CALLBACK -------- */
			when lower(tw.status_message) like '%error occurred while sending push request%'
			or lower(tw.status_message) like '%downstream%'
			or lower(tw.status_message) like '%error code 9001%'
			or lower(tw.status_message) like '%error code 9003%'
			or lower(tw.status_message) like '%error code 9004%'
			or lower(tw.status_message) like '%sorry customer, we could not process your request at the moment%'
			or lower(tw.status_message) like '%m-pesa is undergoing scheduled maintenance%'
			or lower(tw.status_message) like '%error code 9006%'
            then 'Safaricom Callback Errors'
            /* -------- PROFITS EOD -------- */
			when lower(tw.status_message) like '%production%date%not%found%'
			or lower(tw.status_message) like '%profits%reference_sent%'
			or lower(tw.status_message) like '%profits%unique_key%'
            then 'Profits: Errors during EOD'
            /* -------- PROFITS DB -------- */
			when lower(tw.status_message) like '%prft013%'
            then 'Profits: Database Connection'
            /* -------- PROFITS OTHER ERRORS -------- */
			when lower(tw.status_message) like '%p%j%t%'
			or lower(tw.status_message) like '%customer%category%language%'
			or lower(tw.status_message) like '%invalid%transaction%deposit%'
			or lower(tw.status_message) like '%deposit_type%'
			or lower(tw.status_message) like '%error%from%core%'
			or lower(tw.status_message) like '%value%date%working%day%'
			or lower(tw.status_message) like '%value%date%smaller%'
			or lower(tw.status_message) like '%prft048%'
			or lower(tw.status_message) like '%transaction_date_is_changed%'
			or lower(tw.status_message) like '%debit_account_not_found%'
			or lower(tw.status_message) like '%credit_account_not_found%'
            then 'Profits: Other Errors'
            /* -------- PROFITS ESB ERRORS -------- */
			when lower(tw.status_message) like '%standing%order%'
            then 'Profits: ESB Errors'
            /* -------- NETWORK / TIMEOUT -------- */
			when lower(tw.status_message) like '%java%net%'
			or lower(tw.status_message) like '%timeout%'
			or lower(tw.status_message) like '%similar%transaction%'
            then 'Profits: Network Timeout'
			when lower(tw.status_message) like '%http%operation%ipsl%' then 'Pesalink: IPSL Timeout Errors'
			when lower(tw.status_message) like '%customer%registration%failed%jsonobject%text%must%begin%'
            then 'Pesalink: Registration Errors'
			when lower(tw.status_message) like '%decode%soap%request%' then 'Pesalink: Transaction Errors'
			when lower(tw.status_message) like '%token%time%'
            then 'Kocela: Validation Errors'
			when lower(tw.status_message) like '%service%currently%unavailable%'
            then 'TES Errors'
            /* -------- ACCOUNT STATE ERRORS -------- */
			when lower(tw.status_message) like '%account%is%blocked%'
			or lower(tw.status_message) like '%account%is%closed%'
			or lower(tw.status_message) like '%account%not%active%'
			or lower(tw.status_message) like '%account%number%tied%user%'
			or lower(tw.status_message) like '%account%verification%failed%'
			or lower(tw.status_message) like '%account%is%idle%'
			or lower(tw.status_message) like '%account%is%dormant%'
            then 'Account blocked,dormant,closed'
            /* -------- WHIZZ LOAN ERRORS -------- */
			when lower(tw.status_message) like '%maxed%loan%topup%tenors%'
			or lower(tw.status_message) like '%no%running%loans%'
            then 'Customer: Whizz loan errors'
			when lower(tw.status_message) like '%not%registered%mobile%banking%' then 'Not Registered'
			when lower(tw.status_message) like '%your%request%being%processed%wait%confirmation%message%' then 'Other: Undefined'
			when lower(tw.status_message) like '%request%validation%fail%' then 'Other Errors'
			when lower(tw.status_message) like '%request%processed%shortly%confirmation%sms%'
			and lower(tw.cbs_response_extra5) like '%success%' then 'Successful'
            /* -------- OTHER ERRORS -------- */
			when lower(tw.status_message) like '%invalid_data%' then 'Other: Target save redemption error'
			when lower(tw.status_message) like '%not_existant_bank%' then 'Pesalink: Invalid bank'
			when lower(tw.status_message) like '%transaction declined due to account restrictions%' then 'Other: Paybill not enabled for B2B'
			when lower(tw.status_message) like '%the debitparty is in an invalid state%' then 'Other: Deposit to dormant/closed account'
			when lower(tw.status_message) like '%bank has not been configured yet.%' then 'Pesalink: Invalid bank'
			when lower(tw.status_message) like '%bank list request failed%' then 'Other: ESB Downtime'
			when lower(tw.status_message) like '%payment cannot be processed due to the recipient%current status%' then 'Other: Invalid recipient phone/account number'
			when lower(tw.status_message) like '%receiver party information is invalid%' then 'Other: Invalid recipient phone/account number'
			when lower(tw.status_message) like '%You are not registered for mobile banking.%' then 'Other: Recipient Not Registered'
            /* -------- DEFAULT -------- */
			else 'Other'
		end
	end as transaction_status
from
	delta.gold_db.transactions_whizz tw
where cast(tw.date_created as date) >= timestamp '2024-01-01 00:00:00'
)
select 
transaction_date, 
transaction_type,
transaction_status,
transaction_channel,
sum(transaction_amount) as transaction_amount, 
count(transaction_amount) as transaction_count
from mobile_transactions
group by transaction_date, transaction_type,
transaction_status,transaction_channel
;