from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret_atm_key"

# --- การตั้งค่า MySQL ---
# ตัวอย่าง: user='root', password='', host='localhost', db='atm_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/atm_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model (เหมือนเดิมแต่ย้ายไปลง MySQL) ---
class Account(db.Model):
    __tablename__ = 'accounts' # กำหนดชื่อ table ใน MySQL
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)

# สร้าง Table ใน MySQL อัตโนมัติ
with app.app_context():
    db.create_all()



@app.route('/')
def index():
    all_accounts = Account.query.all() # นี่คือ List
    total_system_balance = db.session.query(db.func.sum(Account.balance)).scalar() or 0
    return render_template('index.html', accounts=all_accounts, total_system_balance=total_system_balance)

@app.route('/create', methods=['POST'])
def create_account():
    acc_num = request.form.get('account_number')
    user = request.form.get('username')
    initial_balance = float(request.form.get('balance', 0))

    if Account.query.filter_by(account_number=acc_num).first():
        flash(f"Error: เลขบัญชี {acc_num} ซ้ำ!", "danger")
    else:
        new_acc = Account(account_number=acc_num, username=user, balance=initial_balance)
        db.session.add(new_acc)
        db.session.commit()
        flash("สร้างบัญชีใน MySQL สำเร็จ!", "success")
    return redirect(url_for('index'))

@app.route('/transaction', methods=['POST'])
def transaction():
    acc_num = request.form.get('account_number')
    amount = float(request.form.get('amount', 0))
    action = request.form.get('action')

    account = Account.query.filter_by(account_number=acc_num).first()
    if not account:
        flash("ไม่พบเลขบัญชี!", "danger")
        return redirect(url_for('index'))

    if action == 'deposit':
        account.balance += amount
        flash(f"ฝากเงิน {amount:,.2f} บาท เรียบร้อย", "success")
    elif action == 'withdraw':
        if account.balance >= amount:
            account.balance -= amount
            flash(f"ถอนเงิน {amount:,.2f} บาท เรียบร้อย", "success")
        else:
            flash("ยอดเงินไม่พอ!", "warning")
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_account(id):
    acc = Account.query.get_or_404(id)
    db.session.delete(acc)
    db.session.commit()
    flash("ลบบัญชีออกจากฐานข้อมูลแล้ว", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)