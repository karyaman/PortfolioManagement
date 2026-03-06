from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table: MutualFund <-> Stock
mf_stock = db.Table(
    'mf_stock',
    db.Column('mf_id', db.Integer, db.ForeignKey('mutual_fund.id'), primary_key=True),
    db.Column('stock_id', db.Integer, db.ForeignKey('stock.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'user'

    portfolio = db.relationship(
        'Portfolio',
        backref='user',
        uselist=False,
        cascade='all, delete'
    )


class Portfolio(db.Model):
    __tablename__ = 'portfolio'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    mutual_funds = db.relationship(
        'MutualFund',
        backref='portfolio',
        cascade='all, delete'
    )


class MutualFund(db.Model):
    __tablename__ = 'mutual_fund'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))

    stocks = db.relationship(
        'Stock',
        secondary=mf_stock,
        backref=db.backref('mutual_funds', lazy='dynamic')
    )


class Stock(db.Model):
    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
