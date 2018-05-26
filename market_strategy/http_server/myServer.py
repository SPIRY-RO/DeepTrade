from flask import Flask
from flask import request

flask_app = Flask(__name__)

@flask_app.route('/', methods=['GET', 'POST'])
def home():
    return '<h1>Home</h1>'

@flask_app.route('/sell_all', methods=['GET'])
def sell_all():
    message=flask_app.strategy_bean.sell_all()
    return message

@flask_app.route('/change_eth', methods=['GET', 'POST'])
def change_eth_left():
    amount=request.args.get("amount")
    message=flask_app.strategy_bean.change_eth_left(amount)
    return message

@flask_app.route('/change_game', methods=['GET', 'POST'])
def change_game():
    message=flask_app.strategy_bean.change_game()
    return message

#flask_app.run(host='0.0.0.0',port=5000,debug=True)