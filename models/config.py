from models.models import db
import os

class CheckDataBase:
  """Initiate db"""
  def __init__(self, app):
    self.app = app
    self.app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'DATABASE_URL', 'sqlite:///controls.db'
        )
    self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(self.app)

    with self.app.app_context():
      db.create_all()