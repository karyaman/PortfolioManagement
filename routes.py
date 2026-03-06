from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, User, Portfolio, MutualFund, Stock


# ---------------- AUTH DECORATOR ---------------- #

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------- ROUTE REGISTRATION ---------------- #

def register_routes(app):

    # ---------------- AUTH ---------------- #

    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username, password=password).first()

            if not user:
                flash('Invalid credentials')
                return redirect(url_for('login'))

            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))

        return render_template('auth/login.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm = request.form['confirm']
            portfolio_name = request.form['portfolio']

            if password != confirm:
                flash('Passwords do not match')
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists')
                return redirect(url_for('register'))

            user = User(
                username=username,
                email=email,
                password=password,
                role='user'
            )
            db.session.add(user)
            db.session.commit()

            portfolio = Portfolio(
                name=portfolio_name,
                user_id=user.id
            )
            db.session.add(portfolio)
            db.session.commit()

            flash('Registration successful')
            return redirect(url_for('login'))

        return render_template('auth/register.html')


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # ---------------- ADMIN ---------------- #

    @app.route('/admin/dashboard')
    @login_required(role='admin')
    def admin_dashboard():
        users = User.query.filter_by(role='user').all()
        portfolios = Portfolio.query.all()
        mutual_funds = MutualFund.query.all()
        stocks = Stock.query.all()

        return render_template(
            'admin/admin_dashboard.html',
            users=users,
            portfolios=portfolios,
            mutual_funds=mutual_funds,
            stocks=stocks
        )


    @app.route('/admin/stocks/add', methods=['GET', 'POST'])
    @login_required(role='admin')
    def add_stock():
        if request.method == 'POST':
            name = request.form['name'].strip()
            price = float(request.form['price'])

            if Stock.query.filter_by(name=name).first():
                flash('Stock already exists')
                return redirect(url_for('add_stock'))

            stock = Stock(name=name, price=price)
            db.session.add(stock)
            db.session.commit()

            return redirect(url_for('admin_dashboard'))

        return render_template('admin/add_stock.html')


    @app.route('/admin/stocks/edit/<int:stock_id>', methods=['GET', 'POST'])
    @login_required(role='admin')
    def edit_stock(stock_id):
        stock = Stock.query.get_or_404(stock_id)

        if request.method == 'POST':
            stock.name = request.form['name'].strip()
            stock.price = float(request.form['price'])
            db.session.commit()
            return redirect(url_for('admin_dashboard'))

        return render_template('admin/edit_stock.html', stock=stock)


    @app.route('/admin/stocks/delete/<int:stock_id>')
    @login_required(role='admin')
    def delete_stock(stock_id):
        stock = Stock.query.get_or_404(stock_id)
        db.session.delete(stock)
        db.session.commit()
        flash('Stock deleted from all mutual funds')
        return redirect(url_for('admin_dashboard'))

    # ---------------- USER ---------------- #

    @app.route('/user/dashboard')
    @login_required(role='user')
    def user_dashboard():
        user = User.query.get_or_404(session['user_id'])
        portfolio = user.portfolio

        if not portfolio:
            return "Portfolio not found", 400

        return render_template('user/user_dashboard.html', portfolio=portfolio)


    @app.route('/portfolio/edit', methods=['GET', 'POST'])
    @login_required(role='user')
    def edit_portfolio():
        user = User.query.get_or_404(session['user_id'])
        portfolio = user.portfolio

        if request.method == 'POST':
            portfolio.name = request.form['name'].strip()
            db.session.commit()
            return redirect(url_for('user_dashboard'))

        return render_template('user/edit_portfolio.html', portfolio=portfolio)

    # ---------------- MUTUAL FUND ---------------- #

    @app.route('/mf/add', methods=['GET', 'POST'])
    @login_required(role='user')
    def add_mf():
        user = User.query.get_or_404(session['user_id'])
        portfolio = user.portfolio

        if request.method == 'POST':
            name = request.form['name'].strip()

            if not name:
                flash('MF name cannot be empty')
                return redirect(url_for('add_mf'))

            for mf in portfolio.mutual_funds:
                if mf.name == name:
                    flash('MF already exists')
                    return redirect(url_for('add_mf'))

            mf = MutualFund(name=name, portfolio_id=portfolio.id)
            db.session.add(mf)
            db.session.commit()
            return redirect(url_for('user_dashboard'))

        return render_template('user/add_mf.html')


    @app.route('/mf/delete/<int:mf_id>')
    @login_required(role='user')
    def delete_mf(mf_id):
        mf = MutualFund.query.get_or_404(mf_id)
        db.session.delete(mf)
        db.session.commit()
        return redirect(url_for('user_dashboard'))


    @app.route('/mf/<int:mf_id>')
    @login_required(role='user')
    def mf_dashboard(mf_id):
        mf = MutualFund.query.get_or_404(mf_id)
        return render_template('user/mf_dashboard.html', mf=mf)

    # ---------------- MF - STOCK ---------------- #

    @app.route('/mf/<int:mf_id>/stocks')
    @login_required(role='user')
    def stock_dashboard(mf_id):
        mf = MutualFund.query.get_or_404(mf_id)
        stocks = Stock.query.all()
        return render_template('user/stock_dashboard.html', stocks=stocks, mf=mf)


    @app.route('/mf/<int:mf_id>/stocks/add/<int:stock_id>')
    @login_required(role='user')
    def add_stock_to_mf(mf_id, stock_id):
        mf = MutualFund.query.get_or_404(mf_id)
        stock = Stock.query.get_or_404(stock_id)

        if stock in mf.stocks:
            flash('Stock already present')
            return redirect(url_for('stock_dashboard', mf_id=mf_id))

        mf.stocks.append(stock)
        db.session.commit()
        return redirect(url_for('mf_dashboard', mf_id=mf_id))


    @app.route('/mf/<int:mf_id>/stocks/remove/<int:stock_id>')
    @login_required(role='user')
    def remove_stock_from_mf(mf_id, stock_id):
        mf = MutualFund.query.get_or_404(mf_id)
        stock = Stock.query.get_or_404(stock_id)

        if stock in mf.stocks:
            mf.stocks.remove(stock)
            db.session.commit()

        return redirect(url_for('mf_dashboard', mf_id=mf_id))
