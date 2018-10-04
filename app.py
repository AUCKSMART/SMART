import psycopg2
import psycopg2.extras
import csv
import os
from flask import Flask, render_template, flash, redirect, request, url_for,session, logging,json,send_file,jsonify
import datetime
from process import millify, stripper
from datetime import timedelta,tzinfo
from wtforms import Form, StringField, PasswordField, validators,SelectField
from passlib.hash import sha256_crypt
from functools import wraps
from vodacom import getVodacomTransactions, getVodacomAmount, getVodacomCashIn, getVodacomCashOut,getVodaTransactionWithoutMsisdn,getVodaTransactionWithMsisdn
from vodacom import getAllVodacomTransactionByType,getAllVodacomTransactionByOperation, getVodacomTransactionByOperationWithOperation,getVodacomTransactionByTypeWithOperation
from airtel import getAirtelTransaction, getAirtelAmount, getAirtelCashIn,getAirtelCashOut,getAirtelTransactionsWithoutMsisdn,getAirtelTransactionsWithMsisdn,getAirtelLookup
from airtel import getAllAirtelTransactionByOperation,getAllAirtelTransactionByType,getAirtelTransactionByOperationWithOperation,getAirtelTransactionByTypeWithOperation
from tigo import getTigoTransactions,getTigoAmount,getTigoCashIn,getTigoCashOut,getAllTigoTransactionByOperation,getAllTigoTransactionByType
from tigo import getTigoTransactionByOperationWithOperation,getTigoTransactionByTypeWithOperation,getTigoTransactionsWithMsisdn,getTigoTransactionsWithoutMsisdn
from viettel import getViettelTransaction, getViettelAmount,getViettelCashIn,getViettelCashOut,getAllHalotelTransactionByOperation,getAllHalotelTransactionByType
from viettel import getHalotelTransactionByTypeWithOperation,getHalotelTransactionByOperationWithOperation,getHalotelTransactionsWithMsisdn,getHalotelTransactionsWithoutMsisdn
from zantel import getZantelTransactions,getZantelAmount,getZantelCashIn,getZantelCashOut,getAllZantelTransactionByOperation,getAllZantelTransactionByType
from zantel import getZantelTransactionByOperationWithOperation,getZantelTransactionByTypeWithOperation,getZantelTransactionWithMsisdn,getZantelTransactionWithoutMsisdn
from ttcl import getTTCLTransactions,getTTCLAmount,getTTCLCashIn,getTTCLCashOut,getAllTTCLTransactionByType,getAllTTCLTransactionByOperation
from ttcl import getTTCLTransactionByOperationWithOperation,getTTCLTransactionByTypeWithOperation,getTTCLTransactionsWithMsisdn,getTTCLTransactionsWithoutMsisdn

conn = psycopg2.connect(host = "192.168.5.140", database="mobile_money_prod",user="postgres",password="postgres")

#Creating File For Export
op_filename = 'Operation_Transactions.csv'
type_filename = 'Type_Transactions.csv'
transactions_file = 'Transactions.csv'
operation_file = 'Operations_types.csv'
op_transactions = dict()
type_transaction = dict()



app = Flask('__name__')
@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        login_cursor.execute('SELECT * FROM login WHERE username = %s',[username])
        if login_cursor.rowcount > 0:
            log_data = login_cursor.fetchone()
            stored_password = log_data['password']
            if sha256_crypt.verify(password,stored_password):
                staff_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                staff_cursor.execute('SELECT username,firstname,othernames,surname,level,status FROM staffs WHERE username = %s',[username])
                staffs = staff_cursor.fetchone()
                if staffs['status'] == 'Blocked':
                    flash('Your account appears to be blocked, check with the administrator','info')
                    return redirect(url_for('index'))
                else:
                    session['logged_in'] = True
                    session['username'] = staffs['username']
                    session['firstname'] = staffs['firstname']
                    session['surname'] = staffs['surname']
                    session['level'] = staffs['level']

                    return redirect(url_for('home'))
            else:
                flash('Incorrect username of password','danger')
                return redirect(url_for('index'))
        else:
            flash('It appears you do not have an account in this system yet','danger')
            return redirect(url_for('index'))
    return render_template('index.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login here!!','danger')
            return redirect(url_for('index'))
    return wrap

#Logout route

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You have successfully logged out!!','success')
    return redirect(url_for('index'))

@app.route('/home', methods = ['GET','POST'])
@is_logged_in
def home():
    if request.method == 'POST':
        #Get Form Value
        from_datetime = request.form['from_date']
        to_datetime = request.form['to_date']

        #Formating Dates
        user_from_date = stripper(str(from_datetime))
        user_to_date = stripper(str(to_datetime))

        #Summing Up Data from different Operators
        #Vodacom
        voda_transaction_total = getVodacomTransactions(user_from_date, user_to_date)
        voda_package = getVodacomAmount(user_from_date, user_to_date)
        voda_total_amount = float(voda_package['amount'])
        voda_total_fee = float(voda_package['fee'])
        vodacom_total_cashin = getVodacomCashIn(user_from_date, user_to_date)
        vodacom_cashin = millify(vodacom_total_cashin)
        vodacom_total_cashout = getVodacomCashOut(user_from_date, user_to_date)
        vodacom_cashout = millify(vodacom_total_cashout)
        vodacom_trans_single = millify(voda_transaction_total)
        vodacom_amount_single = millify(voda_total_amount)
        voda_fee_single = millify(voda_total_fee)
        #Airtel
        airtel_transactions = getAirtelTransaction(user_from_date, user_to_date)
        airtel_amounts = getAirtelAmount(user_from_date, user_to_date)
        airtel_total_amount = float(airtel_amounts['amount'])
        airtel_total_fees = float(airtel_amounts['fee'])
        airtel_total_cashin = getAirtelCashIn(user_from_date, user_to_date)
        airtel_cashin = millify(airtel_total_cashin)
        airtel_total_cashout = getAirtelCashOut(user_from_date, user_to_date)
        airtel_cashout = millify(airtel_total_cashout)
        airtel_transactions_single = millify(airtel_transactions)
        airtel_amount_single = millify(airtel_total_amount)
        airtel_fee_single = millify(airtel_total_fees)
        #Tigo
        tigo_transactions = getTigoTransactions(user_from_date, user_to_date)
        tigo_amounts = getTigoAmount(user_from_date, user_to_date)
        tigo_total_amount = float(tigo_amounts['amount'])
        tigo_total_fee = float(tigo_amounts['fee'])
        tigo_total_cashin = getTigoCashIn(user_from_date, user_to_date)
        tigo_cashin = millify(tigo_total_cashin)
        tigo_total_cashout = getTigoCashOut(user_from_date, user_to_date)
        tigo_cashout = millify(tigo_total_cashout)
        tigo_trans_single = millify(tigo_transactions)
        tigo_amount_single = millify(tigo_total_amount)
        tigo_fee_single = millify(tigo_total_fee)
        #Viettel
        viettel_transactions = getViettelTransaction(user_from_date, user_to_date)
        viettel_amounts = getViettelAmount(user_from_date, user_to_date)
        viettel_total_amount = float(viettel_amounts['amount'])
        viettel_total_fee = float(viettel_amounts['fee'])
        viettel_total_cashin = getViettelCashIn(user_from_date, user_to_date)
        viettel_cashin = millify(viettel_total_cashin)
        viettel_total_cashout = getViettelCashOut(user_from_date, user_to_date)
        viettel_cashout = millify(viettel_total_cashout)
        viettel_trans_single = millify(viettel_transactions)
        viettel_amount_single = millify(viettel_total_amount)
        viettel_fee_single = millify(viettel_total_fee)
        #Zantel
        zantel_transactions = getZantelTransactions(user_from_date, user_to_date)
        zantel_amounts = getZantelAmount(user_from_date, user_to_date)
        zantel_total_amount = float(zantel_amounts['amount'])
        zantel_total_fee = float(zantel_amounts['fee'])
        zantel_total_cashin = getZantelCashIn(user_from_date, user_to_date)
        zantel_cashin = millify(zantel_total_cashin)
        zantel_total_cashout = getZantelCashOut(user_from_date, user_to_date)
        zantel_cashout = millify(zantel_total_cashout)
        zantel_trans_single = millify(zantel_transactions)
        zantel_amount_single = millify(zantel_total_amount)
        zantel_fee_single = millify(zantel_total_fee)
        #TTCL
        ttcl_transactions = getTTCLTransactions(user_from_date, user_to_date)
        ttcl_amounts = getTTCLAmount(user_from_date, user_to_date)
        ttcl_total_amount = float(ttcl_amounts['amount'])
        ttcl_total_fee = float(ttcl_amounts['fee'])
        ttcl_total_cashin = getTTCLCashIn(user_from_date, user_to_date)
        ttcl_cashin = millify(ttcl_total_cashin)
        ttcl_total_cashout = getTTCLCashOut(user_from_date, user_to_date)
        ttcl_cashout = millify(ttcl_total_cashout)
        ttcl_trans_single = millify(ttcl_transactions)
        ttcl_amount_single = millify(ttcl_total_amount)
        ttcl_fee_single = millify(ttcl_total_fee)
        #Summing Up Data
        #Total Transaction
        total_transaction_all_temp = voda_transaction_total + airtel_transactions + tigo_transactions + viettel_transactions + zantel_transactions + ttcl_transactions
        total_transaction_all = millify(total_transaction_all_temp)
        #Transactions Percentage
        if airtel_transactions == 0:
            airtel_transaction_percent = 0
        else:
            airtel_transaction_percent = '{:0.1F}'.format(((airtel_transactions/total_transaction_all_temp)*100))
        if voda_transaction_total == 0:
            voda_trans_percent = 0
        else:
            voda_trans_percent = '{:0.1F}'.format(((voda_transaction_total/total_transaction_all_temp)*100))
        if tigo_transactions == 0:
            tigo_trans_percent = 0
        else:
            tigo_trans_percent = '{:0.1F}'.format(((tigo_transactions/total_transaction_all_temp)*100))
        if viettel_transactions == 0:
            viettel_trans_percent = 0
        else:
            viettel_trans_percent = '{:0.1F}'.format(((viettel_transactions/total_transaction_all_temp)*100))
        if zantel_transactions == 0:
            zantel_trans_percent = 0
        else:
            zantel_trans_percent = '{:0.1F}'.format(((zantel_transactions/total_transaction_all_temp)*100))
        if ttcl_transactions == 0:
            ttcl_trans_percent = 0
        else:
            ttcl_trans_percent = '{:0.1F}'.format(((ttcl_transactions/total_transaction_all_temp)*100))

        operators_transactions = [
                {
                    'operator':'Airtel',
                    'transactions':airtel_transactions_single,
                    'percentage':airtel_transaction_percent
                },
                {
                    'operator':'Vodacom',
                    'transactions':vodacom_trans_single,
                    'percentage':voda_trans_percent
                },
                {
                    'operator':'Tigo',
                    'transactions':tigo_trans_single,
                    'percentage':tigo_trans_percent
                },
                {
                    'operator':'Viettel',
                    'transactions':viettel_trans_single,
                    'percentage':viettel_trans_percent
                },
                {
                    'operator':'Zantel',
                    'transactions':zantel_trans_single,
                    'percentage':zantel_trans_percent
                },
                {
                    'operator':'TTCL',
                    'transactions':ttcl_trans_single,
                    'percentage':ttcl_trans_percent
                }
            ]
        #Total Amount
        total_amount_all_temp = voda_total_amount + airtel_total_amount + tigo_total_amount + viettel_total_amount + zantel_total_amount + ttcl_total_amount
        total_amount_all = millify(total_amount_all_temp)
        #Amount Percentage
        if airtel_total_amount == 0:
            airtel_amount_percent = 0
        else:
            airtel_amount_percent = '{:0.1F}'.format(((airtel_total_amount/total_amount_all_temp)*100))
        if voda_total_amount == 0:
            voda_amount_percent = 0
        else:
            voda_amount_percent = '{:0.1F}'.format(((voda_total_amount/total_amount_all_temp)*100))
        if tigo_total_amount == 0:
            tigo_amount_percent = 0
        else:
            tigo_amount_percent = '{:0.1F}'.format(((tigo_total_amount/total_amount_all_temp)*100))
        if viettel_total_amount == 0:
            viettel_amount_percent = 0
        else:
            viettel_amount_percent = '{:0.1F}'.format(((viettel_total_amount/total_amount_all_temp)*100))
        if zantel_total_amount == 0:
            zantel_amount_percent = 0
        else:
            zantel_amount_percent = '{:0.1F}'.format(((zantel_total_amount/total_amount_all_temp)*100))
        if ttcl_total_amount == 0:
            ttcl_amount_percent = 0
        else:
            ttcl_amount_percent = '{:0.1F}'.format(((ttcl_total_amount/total_amount_all_temp)*100))
         
        operators_amount = [
                {
                    'operator':'Airtel',
                    'amount':airtel_amount_single,
                    'percentage':airtel_amount_percent
                },
                {
                    'operator':'Vodacom',
                    'amount':vodacom_amount_single,
                    'percentage':voda_amount_percent
                },
                {
                    'operator':'Tigo',
                    'amount':tigo_amount_single,
                    'percentage':tigo_amount_percent
                },
                {
                    'operator':'Viettel',
                    'amount':viettel_amount_single,
                    'percentage':viettel_amount_percent
                },
                {
                    'operator':'Zantel',
                    'amount':zantel_amount_single,
                    'percentage':zantel_amount_percent
                },
                {
                    'operator':'TTCL',
                    'amount':ttcl_amount_single,
                    'percentage':ttcl_amount_percent
                }
            ]
        #Total Fees
        total_fees_all_temp = voda_total_fee + airtel_total_fees + tigo_total_fee + viettel_total_fee + zantel_total_fee + ttcl_total_fee
        total_fees_all = millify(total_fees_all_temp)
        #Fees Percentage
        if airtel_total_fees == 0:
            airtel_fee_percent = 0
        else:
            airtel_fee_percent = '{:0.1F}'.format(((airtel_total_fees/total_fees_all_temp)*100))
        if voda_total_fee == 0:
            voda_fee_percent = 0
        else:
            voda_fee_percent = '{:0.1F}'.format(((voda_total_fee/total_fees_all_temp)*100))
        if tigo_total_fee == 0:
            tigo_fee_percent = 0
        else:
            tigo_fee_percent = '{:0.1F}'.format(((tigo_total_fee/total_fees_all_temp)*100))
        if viettel_total_fee == 0:
            viettel_fee_percent = 0
        else:
            viettel_fee_percent = '{:0.1F}'.format(((viettel_total_fee/total_fees_all_temp)*100))
        if zantel_total_fee == 0:
            zantel_fee_percent = 0
        else:
            zantel_fee_percent = '{:0.1F}'.format(((zantel_total_fee/total_fees_all_temp)*100))
        if ttcl_total_fee == 0:
            ttcl_fee_percent = 0
        else:
            ttcl_fee_percent = '{:0.1F}'.format(((ttcl_total_fee/total_fees_all_temp)*100))
        operators_fee = [
                {
                    'operator':'Airtel',
                    'fee':airtel_fee_single,
                    'percentage':airtel_fee_percent
                },{
                    'operator':'Vodacom',
                    'fee':voda_fee_single,
                    'percentage':voda_fee_percent
                },
                {
                    'operator':'Tigo',
                    'fee':tigo_fee_single,
                    'percentage':tigo_fee_percent
                },
                {
                    'operator':'Viettel',
                    'fee':viettel_fee_single,
                    'percentage':viettel_fee_percent
                },
                {
                    'operator':'Zantel',
                    'fee':zantel_fee_single,
                    'percentage':zantel_fee_percent
                },
                {
                    'operator':'TTCL',
                    'fee':ttcl_fee_single,
                    'percentage':ttcl_fee_percent
                }
            ]
        #Total Cash In
        total_cashin_temp = vodacom_total_cashin + airtel_total_cashin + tigo_total_cashin + viettel_total_cashin + zantel_total_cashin + ttcl_total_cashin
        total_cashin = millify(total_cashin_temp)
        #Total Cash Out
        total_cashout_temp = vodacom_total_cashout + airtel_total_cashout + tigo_total_cashout + viettel_total_cashout + zantel_total_cashout + ttcl_total_cashout
        total_cashout = millify(total_cashout_temp)
        
        return render_template('home.html', total_transaction_all = total_transaction_all, total_amount_all=total_amount_all, total_fees_all=total_fees_all,total_cashin=total_cashin,total_cashout=total_cashout,vodacom_cashin=vodacom_cashin,vodacom_cashout=vodacom_cashout,airtel_cashin=airtel_cashin,airtel_cashout=airtel_cashout,tigo_cashin=tigo_cashin,tigo_cashout=tigo_cashout,viettel_cashin=viettel_cashin,viettel_cashout=viettel_cashout,zantel_cashin=zantel_cashin,zantel_cashout=zantel_cashout,ttcl_cashin=ttcl_cashin, ttcl_cashout=ttcl_cashout, operators_transactions=operators_transactions,operators_amount=operators_amount,operators_fee=operators_fee)
    
    else:
        cur_date = datetime.datetime.now()
        prev_date = cur_date - datetime.timedelta(days = 1)
        today_date_raw = cur_date.strftime("%Y-%m-%d")
        yesterday_date_raw = prev_date.strftime("%Y-%m-%d")
        request.form.from_date = yesterday_date_raw
        request.form.to_date = today_date_raw
        #General Date Formatting
        
        yesterday_date = stripper(str(yesterday_date_raw))
        today_date = stripper(str(today_date_raw))

        #Summing Up Data from different Operators
        #Vodacom
        voda_transaction_total = getVodacomTransactions(yesterday_date, today_date)
        voda_amounts = getVodacomAmount(yesterday_date, today_date)
        voda_total_amount = float(voda_amounts['amount'])
        voda_total_fee = float(voda_amounts['fee'])
        vodacom_total_cashin = getVodacomCashIn(yesterday_date, today_date)
        vodacom_cashin = millify(vodacom_total_cashin)
        vodacom_total_cashout = getVodacomCashOut(yesterday_date, today_date)
        vodacom_cashout = millify(vodacom_total_cashout)
        vodacom_trans_single = millify(voda_transaction_total)
        vodacom_amount_single = millify(voda_total_amount)
        voda_fee_single = millify(voda_total_amount)
        #Airtel
        airtel_transactions = getAirtelTransaction(yesterday_date, today_date)
        airtel_amounts = getAirtelAmount(yesterday_date, today_date)
        airtel_total_amount = float(airtel_amounts['amount'])
        airtel_total_fees = float(airtel_amounts['fee'])
        airtel_total_cashin = getAirtelCashIn(yesterday_date, today_date)
        airtel_cashin = millify(airtel_total_cashin)
        airtel_total_cashout = getAirtelCashOut(yesterday_date, today_date)
        airtel_cashout = millify(airtel_total_cashout)
        airtel_transactions_single = millify(airtel_transactions)
        airtel_amount_single = millify(airtel_total_amount)
        airtel_fee_single = millify(airtel_total_fees)
        #Tigo
        tigo_transactions = getTigoTransactions(yesterday_date, today_date)
        tigo_amounts = getTigoAmount(yesterday_date, today_date)
        tigo_total_amount = float(tigo_amounts['amount'])
        tigo_total_fee = float(tigo_amounts['fee'])
        tigo_total_cashin = getTigoCashIn(yesterday_date, today_date)
        tigo_cashin = millify(tigo_total_cashin)
        tigo_total_cashout = getTigoCashOut(yesterday_date, today_date)
        tigo_cashout = millify(tigo_total_cashout)
        tigo_trans_single = millify(tigo_transactions)
        tigo_amount_single = millify(tigo_total_amount)
        tigo_fee_single = millify(tigo_total_fee)
        #Viettel
        viettel_transactions = getViettelTransaction(yesterday_date, today_date)
        viettel_amounts = getViettelAmount(yesterday_date, today_date)
        viettel_total_amount = float(viettel_amounts['amount'])
        viettel_total_fee = float(viettel_amounts['fee'])
        viettel_total_cashin = getViettelCashIn(yesterday_date, today_date)
        viettel_cashin = millify(viettel_total_cashin)
        viettel_total_cashout = getViettelCashOut(yesterday_date, today_date)
        viettel_cashout = millify(viettel_total_cashout)
        viettel_trans_single = millify(viettel_transactions)
        viettel_amount_single = millify(viettel_total_amount)
        viettel_fee_single = millify(viettel_total_fee)
        #Zantel
        zantel_transactions = getZantelTransactions(yesterday_date, today_date)
        zantel_amounts = getZantelAmount(yesterday_date, today_date)
        zantel_total_amount = float(zantel_amounts['amount'])
        zantel_total_fee = float(zantel_amounts['fee'])
        zantel_total_cashin = getZantelCashIn(yesterday_date, today_date)
        zantel_cashin = millify(zantel_total_cashin)
        zantel_total_cashout = getZantelCashOut(yesterday_date, today_date)
        zantel_cashout = millify(zantel_total_cashout)
        zantel_trans_single = millify(zantel_transactions)
        zantel_amount_single = millify(zantel_total_amount)
        zantel_fee_single = millify(zantel_total_fee)
        #TTCL
        ttcl_transactions = getTTCLTransactions(yesterday_date, today_date)
        ttcl_amounts = getTTCLAmount(yesterday_date, today_date)
        ttcl_total_amount = float(ttcl_amounts['amount'])
        ttcl_total_fee = float(ttcl_amounts['fee'])
        ttcl_total_cashin = getTTCLCashIn(yesterday_date, today_date)
        ttcl_cashin = millify(ttcl_total_cashin)
        ttcl_total_cashout = getTTCLCashOut(yesterday_date, today_date)
        ttcl_cashout = millify(ttcl_total_cashout)
        ttcl_trans_single = millify(ttcl_transactions)
        ttcl_amount_single = millify(ttcl_total_amount)
        ttcl_fee_single = millify(ttcl_total_fee)
        #Summing Up Data
        #Total Transaction
        total_transaction_all_temp = voda_transaction_total + airtel_transactions + tigo_transactions + viettel_transactions + zantel_transactions + ttcl_transactions
        total_transaction_all = millify(total_transaction_all_temp)
        #Transactions Percentage
        if airtel_transactions == 0:
            airtel_transaction_percent = 0
        else:
            airtel_transaction_percent = '{:0.1F}'.format(((airtel_transactions/total_transaction_all_temp)*100))
        if voda_transaction_total == 0:
            voda_trans_percent = 0
        else:
            voda_trans_percent = '{:0.1F}'.format(((voda_transaction_total/total_transaction_all_temp)*100))
        if tigo_transactions == 0:
            tigo_trans_percent = 0
        else:
            tigo_trans_percent = '{:0.1F}'.format(((tigo_transactions/total_transaction_all_temp)*100))
        if viettel_transactions == 0:
            viettel_trans_percent = 0
        else:
            viettel_trans_percent = '{:0.1F}'.format(((viettel_transactions/total_transaction_all_temp)*100))
        if zantel_transactions == 0:
            zantel_trans_percent = 0
        else:
            zantel_trans_percent = '{:0.1F}'.format(((zantel_transactions/total_transaction_all_temp)*100))
        if ttcl_transactions == 0:
            ttcl_trans_percent = 0
        else:
            ttcl_trans_percent = '{:0.1F}'.format(((ttcl_transactions/total_transaction_all_temp)*100))

        operators_transactions = [
                {
                    'operator':'Airtel',
                    'transactions':airtel_transactions_single,
                    'percentage':airtel_transaction_percent
                },
                {
                    'operator':'Vodacom',
                    'transactions':vodacom_trans_single,
                    'percentage':voda_trans_percent
                },
                {
                    'operator':'Tigo',
                    'transactions':tigo_trans_single,
                    'percentage':tigo_trans_percent
                },
                {
                    'operator':'Viettel',
                    'transactions':viettel_trans_single,
                    'percentage':viettel_trans_percent
                },
                {
                    'operator':'Zantel',
                    'transactions':zantel_trans_single,
                    'percentage':zantel_trans_percent
                },
                {
                    'operator':'TTCL',
                    'transactions':ttcl_trans_single,
                    'percentage':ttcl_trans_percent
                }
            ]
        #Total Amount
        total_amount_all_temp = voda_total_amount + airtel_total_amount + tigo_total_amount + viettel_total_amount + zantel_total_amount + ttcl_total_amount
        total_amount_all = millify(total_amount_all_temp)
        #Amount Percentage
        if airtel_total_amount == 0:
            airtel_amount_percent = 0
        else:
            airtel_amount_percent = '{:0.1F}'.format(((airtel_total_amount/total_amount_all_temp)*100))
        if voda_total_amount == 0:
            voda_amount_percent = 0
        else:
            voda_amount_percent = '{:0.1F}'.format(((voda_total_amount/total_amount_all_temp)*100))
        if tigo_total_amount == 0:
            tigo_amount_percent = 0
        else:
            tigo_amount_percent = '{:0.1F}'.format(((tigo_total_amount/total_amount_all_temp)*100))
        if viettel_total_amount == 0:
            viettel_amount_percent = 0
        else:
            viettel_amount_percent = '{:0.1F}'.format(((viettel_total_amount/total_amount_all_temp)*100))
        if zantel_total_amount == 0:
            zantel_amount_percent = 0
        else:
            zantel_amount_percent = '{:0.1F}'.format(((zantel_total_amount/total_amount_all_temp)*100))
        if ttcl_total_amount == 0:
            ttcl_amount_percent = 0
        else:
            ttcl_amount_percent = '{:0.1F}'.format(((ttcl_total_amount/total_amount_all_temp)*100))
         
        operators_amount = [
                {
                    'operator':'Airtel',
                    'amount':airtel_amount_single,
                    'percentage':airtel_amount_percent
                },
                {
                    'operator':'Vodacom',
                    'amount':vodacom_amount_single,
                    'percentage':voda_amount_percent
                },
                {
                    'operator':'Tigo',
                    'amount':tigo_amount_single,
                    'percentage':tigo_amount_percent
                },
                {
                    'operator':'Viettel',
                    'amount':viettel_amount_single,
                    'percentage':viettel_amount_percent
                },
                {
                    'operator':'Zantel',
                    'amount':zantel_amount_single,
                    'percentage':zantel_amount_percent
                },
                {
                    'operator':'TTCL',
                    'amount':ttcl_amount_single,
                    'percentage':ttcl_amount_percent
                }
            ]
        #Total Fees
        total_fees_all_temp = voda_total_fee + airtel_total_fees + tigo_total_fee + viettel_total_fee + zantel_total_fee + ttcl_total_fee
        total_fees_all = millify(total_fees_all_temp)
        #Fees Percentage
        if airtel_total_fees == 0:
            airtel_fee_percent = 0
        else:
            airtel_fee_percent = '{:0.1F}'.format(((airtel_total_fees/total_fees_all_temp)*100))
        if voda_total_fee == 0:
            voda_fee_percent = 0
        else:
            voda_fee_percent = '{:0.1F}'.format(((voda_total_fee/total_fees_all_temp)*100))
        if tigo_total_fee == 0:
            tigo_fee_percent = 0
        else:
            tigo_fee_percent = '{:0.1F}'.format(((tigo_total_fee/total_fees_all_temp)*100))
        if viettel_total_fee == 0:
            viettel_fee_percent = 0
        else:
            viettel_fee_percent = '{:0.1F}'.format(((viettel_total_fee/total_fees_all_temp)*100))
        if zantel_total_fee == 0:
            zantel_fee_percent = 0
        else:
            zantel_fee_percent = '{:0.1F}'.format(((zantel_total_fee/total_fees_all_temp)*100))
        if ttcl_total_fee == 0:
            ttcl_fee_percent = 0
        else:
            ttcl_fee_percent = '{:0.1F}'.format(((ttcl_total_fee/total_fees_all_temp)*100))
        operators_fee = [
                {
                    'operator':'Airtel',
                    'fee':airtel_fee_single,
                    'percentage':airtel_fee_percent
                },{
                    'operator':'Vodacom',
                    'fee':voda_fee_single,
                    'percentage':voda_fee_percent
                },
                {
                    'operator':'Tigo',
                    'fee':tigo_fee_single,
                    'percentage':tigo_fee_percent
                },
                {
                    'operator':'Viettel',
                    'fee':viettel_fee_single,
                    'percentage':viettel_fee_percent
                },
                {
                    'operator':'Zantel',
                    'fee':zantel_fee_single,
                    'percentage':zantel_fee_percent
                },
                {
                    'operator':'TTCL',
                    'fee':ttcl_fee_single,
                    'percentage':ttcl_fee_percent
                }
            ]
        #Total Cash In
        total_cashin_temp = vodacom_total_cashin + airtel_total_cashin + tigo_total_cashin + viettel_total_cashin + zantel_total_cashin + ttcl_total_cashin
        total_cashin = millify(total_cashin_temp)
        #Total Cash Out
        total_cashout_temp = vodacom_total_cashout + airtel_total_cashout + tigo_total_cashout + viettel_total_cashout + zantel_total_cashout + ttcl_total_cashout
        total_cashout = millify(total_cashout_temp)
        

        return render_template('home.html', total_transaction_all = total_transaction_all, total_amount_all=total_amount_all, total_fees_all=total_fees_all,total_cashin=total_cashin,total_cashout=total_cashout,vodacom_cashin=vodacom_cashin,vodacom_cashout=vodacom_cashout,airtel_cashin=airtel_cashin,airtel_cashout=airtel_cashout,tigo_cashin=tigo_cashin,tigo_cashout=tigo_cashout,viettel_cashin=viettel_cashin,viettel_cashout=viettel_cashout,zantel_cashin=zantel_cashin,zantel_cashout=zantel_cashout,ttcl_cashin=ttcl_cashin, ttcl_cashout=ttcl_cashout, operators_transactions=operators_transactions,operators_amount=operators_amount,operators_fee=operators_fee)


#Register Route

@app.route('/register',methods = ['GET','POST'])
@is_logged_in
def register():
    if request.method == "POST":
        staff_id = request.form['staff_id']
        firstname = request.form['firstname']
        othername = request.form['othername']
        surname = request.form['surname']
        phone = request.form['phone']
        email = request.form['email']
        gender = request.form['gender']
        position = request.form['position']
        organization = request.form['organization']
        password = sha256_crypt.encrypt(str(surname.upper()))

        #Create Cursor

        staffs_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        login_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        staffs_cursor.execute('INSERT INTO staffs(username,firstname,othernames,surname,sex,phone,email,level,organization) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',(staff_id,firstname,othername,surname,gender,phone,email,position,organization))
        login_cursor.execute('INSERT INTO login(username,password) VALUES(%s,%s)',(staff_id,password))
        conn.commit()
        staffs_cursor.close()
        login_cursor.close()
        flash('You have registered a new staff','success')
        return redirect(url_for('register'))
    return render_template('register.html')

#Route for Staffs Page
@app.route('/staffs',methods = ['POST','GET'])
#@is_logged_in
def staffs():
    if request.method == 'POST':
        category = request.form['search_category']
        keyword = request.form['keyword']
        if category != "" and keyword != "":
            staff_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            staff_cursor.execute('SELECT * FROM staffs WHERE %s = %s',(category,keyword))
            staffs = staff_cursor.fetchall()
            if len(staffs) > 0:
                return render_template('staffs.html',staffs=staffs)
            else:
                msg = 'There are no staffs registered in the system with those particulars!'
                return render_template('staffs.html', msg = msg)
        else:
            msg = 'Fill in the search fields first!'
            return render_template('staffs.html', msg = msg)
    else:
        staff_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        staff_cursor.execute('SELECT * FROM staffs')
        staffs = staff_cursor.fetchall()
        if staff_cursor.rowcount > 0:
            return render_template('staffs.html',staffs=staffs)
        else:
            msg = 'There are no staffs registered in the system yet!'
            return render_template('staffs.html', msg = msg)

    staff_cursor.close()

#EDIT STAFFS
@app.route('/edit_staff/<string:staff_id>/',methods = ['POST','GET'])
@is_logged_in
def edit_staff(staff_id):
    custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    custom_cursor.execute('SELECT * FROM staffs WHERE username = %s',[staff_id])
    staff = custom_cursor.fetchone()
    request.form.staff_id = staff['username']
    request.form.firstname = staff['firstname']
    request.form.othername = staff['othernames']
    request.form.surname = staff['surname']
    request.form.phone = staff['phone']
    request.form.email = staff['email']
    request.form.gender = staff['sex']
    request.form.position = staff['level']
    request.form.organization = staff['organization']
    request.form.status = staff['status']
    custom_cursor.close()

    if request.method == 'POST':
        username = request.form['staff_id']
        firstname = request.form['firstname']
        othername = request.form['othername']
        surname = request.form['surname']
        phone = request.form['phone']
        email = request.form['email']
        gender = request.form['gender']
        position = request.form['position']
        organization = request.form['organization']
        status = request.form['status']

        custom_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        custom_cursor.execute("UPDATE staffs SET username = %s,firstname = %s, othernames = %s, surname = %s, sex = %s,phone = %s,email = %s, level = %s,status = %s,organization = %s WHERE username = %s",(username,firstname,othername,surname,gender,phone,email,position,status,organization,staff_id))
        conn.commit()
        custom_cursor.close()

        flash('User details updated','success')
        return render_template('edit_staff.html')

    return render_template('edit_staff.html')

transactions = dict()
#Route for Transactions
@app.route('/transactions',methods = ['POST','GET'])
@is_logged_in
def find_transactions():
    if request.method == 'POST':
        operator = request.form['operator']
        msisdn = request.form['msisdn']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        from_date_modified = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        to_date_modified = datetime.datetime.strptime(to_date, "%Y-%m-%d")
        from_date_long = from_date_modified.strftime("%Y-%m-%d %H:%M:%S")
        to_date_long = to_date_modified.strftime("%Y-%m-%d %H:%M:%S")
        user_from_date = stripper(str(from_date_long))
        user_to_date = stripper(str(to_date_long))
        global transactions
        transactions.clear()
        if operator == "Vodacom":
            if msisdn == "":
                transactions = getVodaTransactionWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Vodacom have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getVodaTransactionWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Vodacom have no record of transactions made in such duration by the phone number provided!'
                    return render_template('transactions.html',msg=msg)
        elif operator == "Airtel":
            if msisdn == "":
                transactions = getAirtelTransactionsWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Airtel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getAirtelTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Airtel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)

        elif operator == "Tigo":
            if msisdn == "":
                transactions = getTigoTransactionsWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Tigo have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getTigoTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Tigo have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)

        elif operator == "Viettel":
            if msisdn == "":
                transactions = getHalotelTransactionsWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Halotel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getHalotelTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Halotel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
        
        elif operator == "Zantel":
            if msisdn == "":
                transactions = getZantelTransactionWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Zantel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getZantelTransactionWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears Zantel have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)

        elif operator == "TTCL":
            if msisdn == "":
                transactions = getTTCLTransactionsWithoutMsisdn(user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears TTCL have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                transactions = getTTCLTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears TTCL have no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
        
        elif operator == "All" or operator == "":
            if msisdn == "":
                ttcl_transaction = getTTCLTransactionsWithoutMsisdn(user_from_date,user_to_date)
                zantel_transactions = getZantelTransactionWithoutMsisdn(user_from_date,user_to_date)
                halotel_transactions = getHalotelTransactionsWithoutMsisdn(user_from_date,user_to_date)
                tigo_transactions = getTigoTransactionsWithoutMsisdn(user_from_date,user_to_date)
                airtel_transactions = getAirtelTransactionsWithoutMsisdn(user_from_date,user_to_date)
                vodacom_transactions = getVodaTransactionWithoutMsisdn(user_from_date,user_to_date)

                transactions = ttcl_transaction + zantel_transactions + halotel_transactions + tigo_transactions + airtel_transactions + vodacom_transactions
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears there are no transactions made in such duration!'
                    return render_template('transactions.html',msg=msg)
            else:
                msisdn = int(msisdn)
                ttcl_transactions = getTTCLTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                zantel_transactions = getZantelTransactionWithMsisdn(msisdn,user_from_date,user_to_date)
                halotel_transactions = getHalotelTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                tigo_transactions = getTigoTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                airtel_transactions = getAirtelTransactionsWithMsisdn(msisdn,user_from_date,user_to_date)
                vodacom_transactions = getVodaTransactionWithMsisdn(msisdn,user_from_date,user_to_date)

                transactions = ttcl_transactions + zantel_transactions + halotel_transactions + tigo_transactions + airtel_transactions + vodacom_transactions
                if len(transactions) > 0:
                    transaction_count = len(transactions)
                    return render_template('transactions.html',transactions=transactions,transaction_count=transaction_count,millify=millify,transactions_file=transactions_file)
                else:
                    msg = 'It appears there are no transactions made in such duration by that number!'
                    return render_template('transactions.html',msg=msg)

    else:
        return render_template('transactions.html')

#Route For Reports
@app.route('/reports', methods = ['POST','GET'])
@is_logged_in
def reports():
    if request.method == 'POST':
        load_from_date = request.form['from_date']
        load_to_date = request.form['to_date']
        operator = request.form['operator']
        operation_type = request.form['type']
        operation = request.form['operation']

        #Format Dates
        from_date = stripper(str(load_from_date))
        today_date = stripper(str(load_to_date))
        if operator == 'Viettel':
            if operation_type == "All" or operation == "":
                viettel_type = getAllHalotelTransactionByType(from_date,today_date)
                viettel_operation = getAllHalotelTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = viettel_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = viettel_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                viettel_type_with_op = getHalotelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                viettel_operation_with_op = getHalotelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = viettel_type_with_op
                op_transactions = viettel_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
        elif operator == 'Tigo':
            if operation_type == "All" or operation == "":
                tigo_type = getAllTigoTransactionByType(from_date,today_date)
                tigo_operation = getAllTigoTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = tigo_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = tigo_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                tigo_type_with_op = getTigoTransactionByTypeWithOperation(operation_type,from_date,today_date)
                tigo_operation_with_op = getTigoTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = tigo_type_with_op
                op_transactions = tigo_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)

        elif operator == 'Airtel':
            if operation_type == "All" or operation == "":
                airtel_type = getAllAirtelTransactionByType(from_date,today_date)
                airtel_operation = getAllAirtelTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = airtel_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = airtel_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                airtel_type_with_op = getAirtelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                airtel_operation_with_op = getAirtelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = airtel_type_with_op
                op_transactions = airtel_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)

        elif operator == 'Vodacom':
            if operation_type == "All" or operation == "":
                vodacom_type = getAllVodacomTransactionByType(from_date,today_date)
                vodacom_operation = getAllVodacomTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = vodacom_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = vodacom_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                vodacom_type_with_op = getVodacomTransactionByTypeWithOperation(operation_type,from_date,today_date)
                vodacom_operation_with_op = getVodacomTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = vodacom_type_with_op
                op_transactions = vodacom_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)

        elif operator == 'Zantel':
            if operation_type == "All" or operation == "":
                zantel_type = getAllZantelTransactionByType(from_date,today_date)
                zantel_operation = getAllZantelTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = zantel_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = zantel_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                zantel_type_with_op = getZantelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                zantel_operation_with_op = getZantelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = zantel_type_with_op
                op_transactions = zantel_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)

        elif operator == 'TTCL':
            if operation_type == "All" or operation == "":
                ttcl_type = getAllTTCLTransactionByType(from_date,today_date)
                ttcl_operation = getAllTTCLTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = ttcl_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = ttcl_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                ttcl_type_with_op = getTTCLTransactionByTypeWithOperation(operation_type,from_date,today_date)
                ttcl_operation_with_op = getTTCLTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = ttcl_type_with_op
                op_transactions = ttcl_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)

        elif operator == 'All' or operator == "":
            if operation_type == "All" or operation == "":
                ttcl_type = getAllTTCLTransactionByType(from_date,today_date)
                ttcl_operation = getAllTTCLTransactionByOperation(from_date,today_date)
                zantel_type = getAllZantelTransactionByType(from_date,today_date)
                zantel_operation = getAllZantelTransactionByOperation(from_date,today_date)
                vodacom_type = getAllVodacomTransactionByType(from_date,today_date)
                vodacom_operation = getAllVodacomTransactionByOperation(from_date,today_date)
                airtel_type = getAllAirtelTransactionByType(from_date,today_date)
                airtel_operation = getAllAirtelTransactionByOperation(from_date,today_date)
                tigo_type = getAllTigoTransactionByType(from_date,today_date)
                tigo_operation = getAllTigoTransactionByOperation(from_date,today_date)
                viettel_type = getAllHalotelTransactionByType(from_date,today_date)
                viettel_operation = getAllHalotelTransactionByOperation(from_date,today_date)
                #global op_transactions
                global op_transactions
                op_transactions.clear()
                op_transactions = ttcl_operation + zantel_operation + vodacom_operation + airtel_operation + tigo_operation + viettel_operation
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                type_transaction = ttcl_type + zantel_type + vodacom_type + airtel_type + tigo_type + viettel_type
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
            else:
                ttcl_type_with_op = getTTCLTransactionByTypeWithOperation(operation_type,from_date,today_date)
                ttcl_operation_with_op = getTTCLTransactionByOperationWithOperation(operation_type,from_date,today_date)
                zantel_type_with_op = getZantelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                zantel_operation_with_op = getZantelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                vodacom_type_with_op = getVodacomTransactionByTypeWithOperation(operation_type,from_date,today_date)
                vodacom_operation_with_op = getVodacomTransactionByOperationWithOperation(operation_type,from_date,today_date)
                airtel_type_with_op = getAirtelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                airtel_operation_with_op = getAirtelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                tigo_type_with_op = getTigoTransactionByTypeWithOperation(operation_type,from_date,today_date)
                tigo_operation_with_op = getTigoTransactionByOperationWithOperation(operation_type,from_date,today_date)
                viettel_type_with_op = getHalotelTransactionByTypeWithOperation(operation_type,from_date,today_date)
                viettel_operation_with_op = getHalotelTransactionByOperationWithOperation(operation_type,from_date,today_date)
                #global type_transaction
                global type_transaction
                type_transaction.clear()
                global op_transactions
                op_transactions.clear()
                type_transaction = ttcl_type_with_op + zantel_type_with_op + vodacom_type_with_op + airtel_type_with_op + tigo_type_with_op + viettel_type_with_op
                op_transactions = ttcl_operation_with_op + zantel_operation_with_op + vodacom_operation_with_op + airtel_operation_with_op + tigo_operation_with_op + viettel_operation_with_op
                op_count = len(op_transactions)
                type_count = len(type_transaction)
                total_row = dict()
                total_row['operation'] = op_count
                total_row['type'] = type_count
                return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
    else:
        cur_date = datetime.datetime.now()
        prev_date = cur_date - datetime.timedelta(days = 7)
        today_date_raw = cur_date.strftime("%Y-%m-%d")
        last_week_date_raw = prev_date.strftime("%Y-%m-%d")

        #General Date Formatting
        
        last_week_date = stripper(str(last_week_date_raw))
        today_date = stripper(str(today_date_raw))
        request.form.from_date = last_week_date_raw
        request.form.to_date = today_date_raw
        #Transactin By Operation
        viettel_operation = getAllHalotelTransactionByOperation(last_week_date,today_date)
        tigo_operation = getAllTigoTransactionByOperation(last_week_date,today_date)
        vodacom_operation = getAllVodacomTransactionByOperation(last_week_date,today_date)
        zantel_operation = getAllZantelTransactionByOperation(last_week_date,today_date)
        airtel_operation = getAllAirtelTransactionByOperation(last_week_date,today_date)

        global op_transactions
        op_transactions.clear()
        op_transactions = viettel_operation + tigo_operation + vodacom_operation + zantel_operation + airtel_operation

        #Transaction By Type
        viettel_type = getAllHalotelTransactionByType(last_week_date,today_date)
        tigo_type = getAllTigoTransactionByType(last_week_date,today_date)
        vodacom_type = getAllVodacomTransactionByType(last_week_date,today_date)
        zantel_type = getAllZantelTransactionByType(last_week_date,today_date)
        airtel_type = getAllAirtelTransactionByType(last_week_date,today_date)

        global type_transaction
        type_transaction.clear()
        type_transaction = viettel_type + tigo_type + vodacom_type + zantel_type + airtel_type

        #Row Count
        op_count = len(op_transactions)
        type_count = len(type_transaction)
        total_row = dict()
        total_row['operation'] = op_count
        total_row['type'] = type_count

        return render_template('reports.html',op_transactions=op_transactions,type_transaction=type_transaction,total_row=total_row,millify=millify,op_filename=op_filename,type_filename=type_filename)
    
#Download CSV Report For Transaction By Operation
@app.route('/operation_csv/<filename>')
@is_logged_in
def download_operation_csv(filename):
    pathFile = 'C:/Projects/mobile/'+filename
    if os.path.exists(pathFile):
        os.remove(pathFile)
    myFile = open(filename, 'w',newline = '')
    with myFile:
        writer = csv.writer(myFile)
        writer.writerow(['Operation','Transactions','Amount','Fee','Type','Operator'])
        writer.writerows(op_transactions)
    pathFile = 'C:/Projects/mobile/'+filename
    attached_filename = filename
    return send_file(pathFile, mimetype = 'text/csv',attachment_filename=attached_filename,as_attachment=True)

#Download CSV Report For Transaction By Type
@app.route('/type_csv/<filename>')
@is_logged_in
def download_type_csv(filename):
    pathFile = 'C:/Projects/mobile/'+filename
    if os.path.exists(pathFile):
        os.remove(pathFile)
    myFile = open(filename, 'w',newline = '')
    with myFile:
        writer = csv.writer(myFile)
        writer.writerow(['Type','Transactions','Amount','Fee','Operator'])
        writer.writerows(type_transaction)
    pathFile = 'C:/Projects/mobile/'+filename
    attached_filename = filename
    return send_file(pathFile, mimetype = 'text/csv',attachment_filename=attached_filename,as_attachment=True)

#Download CSV Report For Transactions
@app.route('/transaction_csv/<filename>')
@is_logged_in
def download_transactions(filename):
    pathFile = 'C:/Projects/mobile/'+filename
    if os.path.exists(pathFile):
        os.remove(pathFile)
    myFile = open(filename, 'w',newline = '')
    with myFile:
        writer = csv.writer(myFile)
        writer.writerow(['Transaction ID','Transaction Date','sender','Recipient','Amount (TZS)','Operation'])
        writer.writerows(transactions)
    pathFile = 'C:/Projects/mobile/'+filename
    attached_filename = filename
    return send_file(pathFile, mimetype = 'text/csv',attachment_filename=attached_filename,as_attachment=True)

#ROUTE TO OPERATIONS PAGE
@app.route('/operations')
@is_logged_in
def operations():
    airtel_lookup = getAirtelLookup()

    lookup_operations = airtel_lookup
    if len(lookup_operations) > 0:
        total_rows = len(lookup_operations)
        return render_template('operations.html',lookup_operations = lookup_operations,total_rows=total_rows,operation_file=operation_file)
    else:
        msg = "There are no operations registered in the M3 System"
        return render_template('operations.html',msg=msg)

#ROUTE TO DOWNLOAD OPERATIONS
@app.route('/download_operations/<filename>/')
@is_logged_in
def download_operations(filename):
    pathFile = 'C:/Projects/mobile/'+filename
    if os.path.exists(pathFile):
        os.remove(pathFile)
    myFile = open(filename, 'w',newline = '')
    with myFile:
        writer = csv.writer(myFile)
        writer.writerow(['Name','Operator','Type','From','To'])
        writer.writerows(transactions)
    pathFile = 'C:/Projects/mobile/'+filename
    attached_filename = filename
    return send_file(pathFile, mimetype = 'text/csv',attachment_filename=attached_filename,as_attachment=True)


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(host = '192.168.5.186',port = 5000, debug=True)
