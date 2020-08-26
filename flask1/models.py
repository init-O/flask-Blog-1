from flask1 import db, app
from itsdangerous import TimedJSONWebSignatureSerializer as serializer
from flask1 import login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(120), nullable=False, default='default.jpg')
    posts = db.relationship('Post', backref='admin', lazy=True)
    
    def get_request_token(self, expire_time=1800):
        s = serializer(app.config['SECRET_KEY'], expire_time)
        return s.dumps({'user_id' : self.id }).decode('utf-8')

    @staticmethod
    def verify_request_token(token):
        s = serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)    

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image}')"
        
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(30), nullable=False)
    information = db.Column(db.Text, nullable= False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Data('{self.name}' '{self.year}' '{self.title}' '{self.information}')"


