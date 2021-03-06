from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """Site user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, 
                   primary_key=True, 
                   autoincrement=True)

    username = db.Column(db.Text, 
                         nullable=False, 
                         unique=True)

    password = db.Column(db.Text, 
                         nullable=False)

    # start_register
    @classmethod
    def register(cls, username, pwd):
        """Register user w/hashed password & return user."""

        hashed = bcrypt.generate_password_hash(pwd)
        # turn bytestring into normal (unicode utf8) string
        hashed_utf8 = hashed.decode("utf8")

        # return instance of user w/username and hashed pwd
        return cls(username=username, password=hashed_utf8)
    # end_register

    # start_authenticate
    @classmethod
    def authenticate(cls, username, pwd):
        """Validate that user exists & password is correct.

        Return user if valid; else return False.
        """

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            # return user instance
            return u
        else:
            return False
    # end_authenticate    

class Playlist(db.Model):
    """Playlist."""
    __tablename__= "playlists"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(100), nullable=False)
    
    play_song_xref = db.relationship('PlaylistSong', backref='playlists', passive_deletes=True)
    
    song = db.relationship('Song', secondary='playlist_song', backref='playlists', passive_deletes=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user =   db.relationship("User",  backref="playlists")

class Song(db.Model):
    """Song."""
    __tablename__= "songs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artists = db.Column(db.String(255), nullable=False)
    spotify_id = db.Column(db.String(255), nullable=False)
    album_name = db.Column(db.String(255), nullable=False)
    album_image = db.Column(db.String(255), nullable=False)
    play_song_xref = db.relationship('PlaylistSong', backref='songs', passive_deletes=True)

    play_song = db.relationship(
        'Playlist',
        secondary="playlist_song",
        cascade="all,delete",
        backref="songs",
    )

   


class PlaylistSong(db.Model):
    """Mapping of a playlist to a song."""
    __tablename__ = "playlist_song"
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', ondelete="CASCADE"))
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id', ondelete="CASCADE"))




