"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Playlist, Song, PlaylistSong, User
from forms import  PlaylistForm, RegisterForm, LoginForm, DeleteForm, SearchSongsForm
from spotify import spotify
import json
from api import CLIENT_ID, CLIENT_SECRET

my_spotify_client = spotify.Spotify(CLIENT_ID, CLIENT_SECRET)

def pick_from_list(keys,dict):
  return { your_key: dict[your_key] for your_key in keys }

def pick(dict,*keys):
  return pick_from_list(keys,dict)

def first(iterable, default = None, condition = lambda x: True):
    """
    Returns the first item in the `iterable` that
    satisfies the `condition`.

    If the condition is not given, returns the first item of
    the iterable.

    If the `default` argument is given and the iterable is empty,
    or if it has no items matching the condition, the `default` argument
    is returned if it matches the condition.

    The `default` argument being None is the same as it not being given.

    Raises `StopIteration` if no item satisfying the condition is found
    and default is not given or doesn't satisfy the condition.

    >>> first( (1,2,3), condition=lambda x: x % 2 == 0)
    2
    >>> first(range(3, 100))
    3
    >>> first( () )
    Traceback (most recent call last):
    ...
    StopIteration
    >>> first([], default=1)
    1
    >>> first([], default=1, condition=lambda x: x % 2 == 0)
    Traceback (most recent call last):
    ...
    StopIteration
    >>> first([1,3,5], default=1, condition=lambda x: x % 2 == 0)
    Traceback (most recent call last):
    ...
    StopIteration
    """

    try:
        return next(x for x in iterable if condition(x))
    except StopIteration:
        if default is not None and condition(default):
            return default
        else:
            raise


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///new_music"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123456"

connect_db(app)
# db.create_all()


toolbar = DebugToolbarExtension(app)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False



@app.route("/")
def homepage():
    """Show homepage with links to site areas."""
    return redirect("/register")
    # return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""
    # raise 'me'
    if "user_id" in session:
        return redirect(f"/users/profile/{session['user_id']}")

    form = RegisterForm()
    name = form.username.data
    pwd = form.password.data
    existing_user_count = User.query.filter_by(username=name).count()
    if existing_user_count > 0:
        flash("User already exists")
        return redirect('/login')

    if form.validate_on_submit():
        user = User.register(name, pwd)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        # on successful login, redirect to profile page
        return redirect(f"/users/profile/{user.id}")
    else:
        return render_template("/users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("users/login.html", form=form)
    # otherwise
    name = form.username.data
    pwd = form.password.data
    # authenticate will return a user or False
    user = User.authenticate(name, pwd)

    if not user:
        return render_template("users/login.html", form=form)
    # otherwise

    form.username.errors = ["Bad name/password"]
    my_spotify_client.perform_auth()
    session["spotify_access_token"] = my_spotify_client.access_token
    session["spotify_access_token_expires"] = my_spotify_client.access_token_expires
    session["spotify_access_token_did_expire"] = my_spotify_client.access_token_did_expire
    session["user_id"] = user.id  # keep logged in
    return redirect(f"/users/profile/{user.id}")



@app.route("/users/profile/<int:id>",  methods=["GET", "POST"])
def profile(id):
    """Example hidden page for logged-in users only."""

    if "user_id" not in session:
        flash("You must be logged in to view!")
        return redirect("/")

    else:
        id = session["user_id"]
        user = User.query.get_or_404(id)
        form = PlaylistForm()
        playlists = Playlist.query.filter_by(user_id=id).all()
        if form.validate_on_submit(): 
            name = form.name.data
            new_playlist = Playlist(name=name, user_id=session['user_id'])
            db.session.add(new_playlist)
            db.session.commit()
            playlists.append(new_playlist)
            return redirect(f"/users/profile/{id}")
        return render_template("users/profile.html", playlists=playlists, form=form, user=user)


@app.route("/logout")
def logout():
    """Logs user out and redirects to homepage."""
    session.pop("user_id")
    return redirect("/")




@app.route("/playlists/<int:playlist_id>", methods=['POST', 'GET'])
def show_playlist(playlist_id):
    """Show detail on specific playlist."""
    # if "user_id" not in session or playlist.user_id != session['user_id']:
    #     raise Unauthorized()
    playlist = Playlist.query.get_or_404(playlist_id)
    songs = PlaylistSong.query.filter_by(playlist_id=playlist_id)
    form = request.form
    if request.method == 'POST' and form['remove'] and form['song']:
        song_id = form['song']
        song_to_delete = PlaylistSong.query.get(song_id)
        db.session.delete(song_to_delete)
        db.session.commit()
    return render_template("playlist/playlist.html", playlist=playlist, songs=songs)



def set_spotify_token(session):
    my_spotify_client.access_token = session['spotify_access_token']
    my_spotify_client.access_token_expires = session['spotify_access_token_expires']
    my_spotify_client.access_token_did_expire = session['spotify_access_token_did_expire']

# @app.route("/songs/add", methods=["GET", "POST"])
# def add_song():
#     """Handle add-song form:

#     - if form not filled out or invalid: show form
#     - if valid: add playlist to SQLA and redirect to list-of-songs
#     """
#     form = SongForm()
#     # songs = Song.query.all()

#     if form.validate_on_submit():
#         title = request.form['title']
#         artist = request.form['artist']
#         new_song = Song(title=title, artist=artist)
#         db.session.add(new_song)
#         db.session.commit()
#         return redirect("/songs")

#     set_spotify_token(session)
#     # test = my_spotify_client.search('all you need is love','track')
#     res = my_spotify_client.get_track('68BTFws92cRztMS1oQ7Ewj')
#     dataj = json.dumps(res)


#     return render_template("song/new_song.html", form=form, dataj=dataj)
    


@app.route('/playlists/<int:playlist_id>/search', methods=["GET", "POST"])
def show_form(playlist_id):
    """Show form that searches new form, and show results"""
    playlist = Playlist.query.get(playlist_id)
    play_id  = playlist_id
    form = SearchSongsForm()
    resultsSong = []
    checkbox_form = request.form
    if 'form' in checkbox_form and checkbox_form['form'] == 'pick_songs':
        list_of_picked_songs = checkbox_form.getlist('track')
        # map each item in list of picked
        jsonvalues = [ json.loads(item) for item in  list_of_picked_songs ]

        for item in jsonvalues:
            title = item['title']
            spotify_id = item['spotify_id']
            album_name = item['album_name']
            album_image = item['album_image']
            artists = item['artists']
            print(title)
            new_songs = Song(title=title, spotify_id=spotify_id, album_name=album_name, album_image=album_image, artists=artists)
            db.session.add(new_songs)
            db.session.commit()

            playlist_song = PlaylistSong(song_id=new_songs.id, playlist_id=playlist_id)
            db.session.add(playlist_song)
            db.session.commit()
        return redirect(f'/playlists/{playlist_id}')

    if form.validate_on_submit(): 
        track_data = form.track.data
        api_call_track = my_spotify_client.search(track_data,'track')   

        for item in api_call_track['tracks']['items']:
            images = [ image['url'] for image in item['album']['images'] ]
            artists = [ artist['name'] for artist in item['artists'] ]
            urls = item['album']['external_urls']['spotify']
            resultsSong.append({
                'title' : item['name'],
                'spotify_id': item['id'],
                'album_name': item['album']['name'], 
                'album_image': first(images,''),
                'artists': ", ".join(artists),
                'url': urls
            })

    def serialize(obj):
        return json.dumps(obj)
    return render_template('song/search_new_songs.html', playlist=playlist, form=form, resultsSong=resultsSong, serialize=serialize)

@app.route("/playlists/<int:playlist_id>/update", methods=["GET", "POST"])
def update_playlist(playlist_id):
    """Show update form and process it."""

    playlist = Playlist.query.get(playlist_id)

    if "user_id" not in session or playlist.user_id != session['user_id']:
        raise Unauthorized()

    form = PlaylistForm(obj=playlist)

    if form.validate_on_submit():
        playlist.name = form.name.data
        db.session.commit()
        return redirect(f"/users/profile/{session['user_id']}")
    
    return render_template("/playlist/edit.html", form=form, playlist=playlist)



@app.route("/playlists/<int:playlist_id>/delete", methods=["POST"])
def delete_playlist(playlist_id):
    """Delete playlist."""

    playlist = Playlist.query.get(playlist_id)
    if "user_id" not in session or playlist.user_id != session['user_id']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(playlist)
        db.session.commit()

    return redirect(f"/users/profile/{session['user_id']}")
