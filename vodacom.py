import psycopg2
import psycopg2.extras

conn = psycopg2.connect(host = "192.168.5.140", database="mobile_money_prod",user="postgres",password="postgres",port= 5432)

def getVodacomTransactions(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT SUM(tr_count) as total_transaction FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s',(from_date, to_date))
    transactions = custom_cursor.fetchone()

    if transactions['total_transaction'] is None:
            voda_transaction_total = 0
    else:
            voda_transaction_total = float(transactions['total_transaction'])
    
    custom_cursor.close()

    return voda_transaction_total

def getVodacomAmount(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT SUM(sum_amount) as total_amount, SUM(sum_fee) as total_fee FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s',(from_date, to_date))
    amounts = custom_cursor.fetchone()

    if amounts['total_amount'] is None:
        total_amount = 0
    else:
        total_amount = float(amounts['total_amount'])
        
    if amounts['total_fee'] is None:
        total_fee = 0
    else:
        total_fee = float(amounts['total_fee'])

    data = dict()
    data['amount'] = total_amount
    data['fee'] = total_fee
    custom_cursor.close()
    return data

def getVodacomCashIn(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT SUM(sum_amount) as total_cash_in FROM vodacom_daily_reports WHERE operation_type = %s AND tdate::int BETWEEN %s AND %s',('IN', from_date, to_date))
    cashin = custom_cursor.fetchone()
    if cashin['total_cash_in'] is None:
        cashin_total = 0
    else:
        cashin_total = float(cashin['total_cash_in'])
    custom_cursor.close()
    return cashin_total

def getVodacomCashOut(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT SUM(sum_amount) as total_cash_out FROM vodacom_daily_reports WHERE operation_type = %s AND tdate::int BETWEEN %s AND %s',('OUT', from_date, to_date))
    cashout = custom_cursor.fetchone()
    if cashout['total_cash_out'] is None:
        cashout_total = 0
    else:
        cashout_total = float(cashout['total_cash_out'])
    custom_cursor.close()
    return cashout_total

def getVodaTransactionWithoutMsisdn(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT transaction_id as transaction_id ,transaction_date as transaction_date,account_msisdn as sender,destination_msisdn as recepient, credited_amount as amount,products_brand as products_brand FROM vodacom_transactions WHERE transaction_date BETWEEN %s AND %s',(from_date, to_date))
    transactions = custom_cursor.fetchall()
    return transactions  

def getVodaTransactionWithMsisdn(msisdn,from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute("SELECT transaction_id as transaction_id ,transaction_date as transaction_date,account_msisdn as sender,destination_msisdn as recepient, credited_amount as amount,products_brand as products_brand FROM vodacom_transactions WHERE (account_msisdn LIKE '%%%s%%' OR destination_msisdn LIKE '%%%s%%') AND (transaction_date BETWEEN %s AND %s)",(msisdn, msisdn,from_date, to_date))
    transactions = custom_cursor.fetchall()
    return transactions

def getAllVodacomTransactionByOperation(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute("SELECT products_brand as operation, SUM(tr_count) as transactions, SUM(sum_amount) as amount, SUM(sum_fee) as fee, operation_type as type,'Vodacom' as operator FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s GROUP BY (products_brand,operation_type)",(from_date, to_date))
    transactions = custom_cursor.fetchall()
    return transactions
    
def getAllVodacomTransactionByType(from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute("SELECT operation_type as type, SUM(tr_count) as transactions, SUM(sum_amount) as amount, SUM(sum_fee) as fee,'Vodacom' as operator  FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s GROUP BY (operation_type)",(from_date, to_date))
    transactions = custom_cursor.fetchall()
    return transactions

def getVodacomTransactionByOperationWithOperation(operation,from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute("SELECT products_brand as operation, SUM(tr_count) as transactions, SUM(sum_amount) as amount, SUM(sum_fee) as fee, operation_type as type,'Vodacom' as operator  FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s AND operation_type = %s GROUP BY (products_brand,operation_type)",(from_date, to_date,operation))
    transactions = custom_cursor.fetchall()
    return transactions  

def getVodacomTransactionByTypeWithOperation(operation,from_date, to_date):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute("SELECT operation_type as type, SUM(tr_count) as transactions, SUM(sum_amount) as amount, SUM(sum_fee) as fee,'Vodacom' as operator FROM vodacom_daily_reports WHERE tdate::int BETWEEN %s AND %s AND operation_type = %s GROUP BY (operation_type)",(from_date, to_date,operation))
    transactions = custom_cursor.fetchall()
    return transactions
