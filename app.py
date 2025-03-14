from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'  # SQLite 資料庫
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # 設置安全密鑰
db = SQLAlchemy(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# 定義使用者模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # submitter（承辦人）、signer（簽收）、verifier（核銷）、manager（主管）、accountant（會計）
    records = db.relationship('BudgetRecord', backref='user', lazy=True)  # 關聯預算記錄

# 定義預算記錄模型
class BudgetRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    submitter = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 關聯承辦人
    receipt_received = db.Column(db.Boolean, default=False)
    receipt_verified = db.Column(db.Boolean, default=False)
    manager_approved = db.Column(db.Boolean, default=False)
    accountant_approved = db.Column(db.Boolean, default=False)

# 加載使用者的回調函數
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 手動初始化資料庫
with app.app_context():
    db.create_all()

# 首頁（顯示記錄）
@app.route('/')
@login_required
def index():
    if current_user.role == 'submitter':
        records = BudgetRecord.query.filter_by(user_id=current_user.id).all()
    else:
        records = BudgetRecord.query.all()
    return render_template('index.html', records=records)

# 新增記錄
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        month = int(request.form['month'])
        day = int(request.form['day'])
        purpose = request.form['purpose']
        amount = float(request.form['amount'])

        # 計算個人餘額
        total_spent = db.session.query(db.func.sum(BudgetRecord.amount)).filter_by(user_id=current_user.id).scalar() or 0
        balance = 48000 - (total_spent + amount)

        # 新增記錄
        new_record = BudgetRecord(
            month=month,
            day=day,
            purpose=purpose,
            amount=amount,
            balance=balance,
            submitter=current_user.email,
            user_id=current_user.id
        )
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

# 更新憑證簽收狀態
@app.route('/update_receipt_received/<int:id>', methods=['POST'])
@login_required
def update_receipt_received(id):
    if current_user.role == 'signer':
        record = BudgetRecord.query.get_or_404(id)
        record.receipt_received = True
        db.session.commit()
    return redirect(url_for('index'))

# 更新憑證核銷狀態
@app.route('/update_receipt_verified/<int:id>', methods=['POST'])
@login_required
def update_receipt_verified(id):
    if current_user.role == 'verifier':
        record = BudgetRecord.query.get_or_404(id)
        record.receipt_verified = True
        db.session.commit()
    return redirect(url_for('index'))

# 審批記錄
@app.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve_record(id):
    record = BudgetRecord.query.get_or_404(id)
    if 'manager_approve' in request.form and current_user.role == 'manager':
        record.manager_approved = True
    if 'accountant_approve' in request.form and current_user.role == 'accountant':
        record.accountant_approved = True
    db.session.commit()
    return redirect(url_for('index'))

# 導出 Excel 報表
@app.route('/export')
@login_required
def export_records():
    records = BudgetRecord.query.all()
    data = [{
        '月': record.month,
        '日': record.day,
        '用途': record.purpose,
        '支付數': record.amount,
        '餘額': record.balance,
        '承辦人': record.submitter,
        '憑證簽收': '✅' if record.receipt_received else '❌',
        '憑證核銷': '✅' if record.receipt_verified else '❌',
        '主管審批': '✅' if record.manager_approved else '❌',
        '會計審批': '✅' if record.accountant_approved else '❌'
    } for record in records]
    df = pd.DataFrame(data)
    df.to_excel('budget_records.xlsx', index=False)
    return send_file('budget_records.xlsx', as_attachment=True)

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        return '登入失敗：使用者不存在'
    return render_template('login.html')

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 創建測試使用者（測試用）
@app.route('/create_users')
def create_users():
    users = [
        User(email='A1@gmail.com', role='submitter'),
        User(email='A2@gmail.com', role='submitter'),
        User(email='jufuchen0803@gmail.com', role='signer'),  # 憑證簽收
        User(email='publicfuchen@gmail.com', role='verifier'),  # 憑證核銷
        User(email='manager@gmail.com', role='manager'),
        User(email='accountant@gmail.com', role='accountant'),
    ]
    for user in users:
        db.session.add(user)
    db.session.commit()
    return '使用者已創建'

if __name__ == '__main__':
    app.run(debug=True)