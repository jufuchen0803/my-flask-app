from app import app, db, User

# 設置應用程式上下文
with app.app_context():
    # 創建使用者
    users = [
        User(email='jufuchen0803@gmail.com', role='signer'),  # 憑證簽收
        User(email='publicfuchen0803@gmail.com', role='manager'),  # 主管審批
        User(email='jufuchen0805@gmail.com', role='accountant')  # 會計審批
    ]

    # 將使用者加入資料庫
    for user in users:
        db.session.add(user)
    db.session.commit()

    print("使用者已創建")