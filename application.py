#pk_b1dd9cac623148b8b7b49962402a7d07
#CREATE TABLE 'purchases' ('id' integer PRIMARY KEY NOT NULL, 'user_id' integer, 'symbol' text, 'share_price' real, 'num_shares' integer, 'total_cost' , 'timestamp' )
import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.globals.update(lookup = lookup)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    groups = db.execute("SELECT symbol, SUM(num_shares) AS sum FROM purchases WHERE user_id = ? GROUP BY symbol", session["user_id"])

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cashVal = float(cash[0]["cash"])

    tot = db.execute("SELECT total_cost FROM purchases WHERE user_id = ?", session["user_id"])

    userTot = 0

    for x in range(tot):
        userTot = userTot + int(tot[x]["total_cost"])

    return render_template("index.html", groups=groups, cashVal=cashVal, tot = userTot)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        currentTime = datetime.datetime.now()
        stock = request.form.get("stock")
        number = request.form.get("shares")
        bought = lookup(stock)
        price = bought["price"]
        if not bought:
            return apology("Invalid Stock Name")

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        userCash = cash[0]["cash"]

        total = float(bought["price"]*int(number))
        balance = userCash - total
        if balance < total:
            return apology("Your balance is too low")
        else:
            #update database
            purchase = db.execute("INSERT INTO purchases (user_id, symbol, share_price, num_shares, total_cost, timestamp) VALUES(?, ?, ?, ?, ?, ?)", session["user_id"], stock, price, number, total, currentTime)

            newBalance = db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])
            #update purchases table on finance database
            #update user_id, symbol, share price, quantity, total value, date/time
            return render_template("bought.html",name=bought["name"], stock=bought["symbol"], price=bought["price"], number = number, userCash = userCash, total = total, balance = balance)

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/quote", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        stock = request.form.get("stock")
        quoted = lookup(stock)
        if not quoted:
            return apology("Invalid Stock Name")
        return render_template("quoted.html",name=quoted["name"], stock=quoted["symbol"], price=quoted["price"])
    return render_template("quote.html")


    return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        hashed = generate_password_hash(request.form.get("password"))
        check = check_password_hash(hashed, request.form.get("confirm_password"))

        if check == True:
            register = db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", username, hashed)
            rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
            session["user_id"] = rows[0]["id"]
            return redirect("/")
        else:
            return apology("Passwords don't match")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
