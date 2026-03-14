from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "atm_secure_68_key"

# การตั้งค่า MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/atm_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20))
    action_type = db.Column(db.String(50))
    amount = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()

def log_event(acc_num, action, amount=0.0):
    log = Transaction(account_number=acc_num, action_type=action, amount=amount)
    db.session.add(log)
    db.session.commit()

# --- Routes ---
@app.route('/')
def index():
    accounts = Account.query.all()
    total = db.session.query(db.func.sum(Account.balance)).scalar() or 0
    return render_template('index.html', accounts=accounts, total=total)

@app.route('/history')
def history():
    logs = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('history.html', logs=logs)

@app.route('/create', methods=['POST'])
def create():
    acc_num = request.form.get('account_number')
    name = request.form.get('username')
    try:
        bal = float(request.form.get('balance', 0))
    except: bal = 0

    if bal < 0:
        flash("ไม่สามารถสร้างบัญชีด้วยยอดเงินติดลบได้!", "danger")
    elif Account.query.filter_by(account_number=acc_num).first():
        flash("เลขบัญชีนี้มีอยู่แล้ว!", "danger")
    else:
        db.session.add(Account(account_number=acc_num, username=name, balance=bal))
        db.session.commit()
        log_event(acc_num, "เปิดบัญชีใหม่", bal)
        flash("สร้างบัญชีสำเร็จ", "success")
    return redirect(url_for('index'))

@app.route('/action', methods=['POST'])
def action():
    acc_num = request.form.get('account_number')
    act = request.form.get('action')
    try:
        amt = float(request.form.get('amount', 0))
    except:
        flash("กรุณากรอกตัวเลขจำนวนเงินที่ถูกต้อง", "danger")
        return redirect(url_for('index'))

    # ตรวจสอบยอดเงินห้ามติดลบหรือเป็นศูนย์
    if amt <= 0:
        flash(f"จำนวนเงิน {amt} ไม่ถูกต้อง (ต้องมากกว่า 0)", "danger")
        return redirect(url_for('index'))

    acc = Account.query.filter_by(account_number=acc_num).first()
    if not acc:
        flash("ไม่พบเลขบัญชี", "danger")
    elif act == 'deposit':
        acc.balance += amt
        log_event(acc_num, "ฝากเงิน", amt)
        flash(f"ฝากเงินจำนวน {amt:,.2f} บาท สำเร็จ", "success")
    elif act == 'withdraw':
        if acc.balance >= amt:
            acc.balance -= amt
            log_event(acc_num, "ถอนเงิน", amt)
            flash(f"ถอนเงินจำนวน {amt:,.2f} บาท สำเร็จ", "success")
        else:
            flash("ยอดเงินในบัญชีไม่พอ!", "warning")
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    acc = Account.query.get(id)
    if acc:
        log_event(acc.account_number, "ลบบัญชี")
        db.session.delete(acc)
        db.session.commit()
        flash("ลบบัญชีเรียบร้อย", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)