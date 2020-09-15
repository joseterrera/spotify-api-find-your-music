"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Playlist, Song, PlaylistSong, User
from forms import NewSongForPlaylistForm, SongForm, PlaylistForm, RegisterForm, LoginForm, DeleteForm, SearchSongsForm
from spotify import spotify
import json
from api import CLIENT_ID, CLIENT_SECRET

my_spotify_client = spotify.Spotify(CLIENT_ID, CLIENT_SECRET)

def pick_from_list(keys,dict):
  return { your_key: dict[your_key] for your_key in keys }

def pick(dict,*keys):
  return pick_from_list(keys,dict)

# def pick_in_map(*keys):
#   def pick(dict):
#     return pick_from_list(keys,dict)
#   return pick


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
# the toolbar is only enabled in debug mode:
# app.debug = True
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///new_music"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

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

        # on successful login, redirect to secret page
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


# end-login    


@app.route("/users/profile/<int:id>",  methods=["GET", "POST"])
def profile(id):
    """Example hidden page for logged-in users only."""


    if "user_id" not in session:
        flash("You must be logged in to view!")
        return redirect("/")

    else:
        id = session["user_id"]
        form = PlaylistForm()
        playlists = Playlist.query.filter_by(user_id=id).all()
        if form.validate_on_submit(): 
            name = form.name.data
            new_playlist = Playlist(name=name, user_id=session['user_id'])
            db.session.add(new_playlist)
            db.session.commit()
            playlists.append(new_playlist)
            return redirect(f"/users/profile/{id}")
        return render_template("users/profile.html", playlists=playlists, form=form)


@app.route("/logout")
def logout():
    """Logs user out and redirects to homepage."""

    session.pop("user_id")

    return redirect("/")




@app.route("/playlists/<int:playlist_id>")
def show_playlist(playlist_id):
    """Show detail on specific playlist."""

    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    playlist = Playlist.query.get_or_404(playlist_id)
    songs = PlaylistSong.query.filter_by(playlist_id=playlist_id)

    for b in songs:
        print('testing',b)


    return render_template("playlist/playlist.html", playlist=playlist)


# @app.route("/playlists/add", methods=["GET", "POST"])
# def add_playlist():
#     """Handle add-playlist form:

#     - if form not filled out or invalid: show form
#     - if valid: add playlist to SQLA and redirect to list-of-playlists
#     """
#     form = PlaylistForm()

#     if form.validate_on_submit():
#         name = form.name.data
#         description = form.description.data
#         new_playlist = Playlist(name=name, description=description)
#         db.session.add(new_playlist)
#         db.session.commit()
#         # flash(f"Added {name} at {description}")
#         return redirect("/profile")

#     return render_template("playlist/new_playlist.html", form=form)

    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK


##############################################################################
# Song routes


@app.route("/songs")
def show_all_songs():
    """Show list of songs."""

    songs = Song.query.all()
    return render_template("song/songs.html", songs=songs)


@app.route("/songs/<int:song_id>")
def show_song(song_id):
    """return a specific song"""

    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    song = Song.query.get_or_404(song_id)
    playlists = song.play_song


    return render_template("song/song.html", song=song, playlists=playlists)


def set_spotify_token(session):
    my_spotify_client.access_token = session['spotify_access_token']
    my_spotify_client.access_token_expires = session['spotify_access_token_expires']
    my_spotify_client.access_token_did_expire = session['spotify_access_token_did_expire']

@app.route("/songs/add", methods=["GET", "POST"])
def add_song():
    """Handle add-song form:

    - if form not filled out or invalid: show form
    - if valid: add playlist to SQLA and redirect to list-of-songs
    """
    # ADD THE NECESSARY CODE HERE FOR THIS ROUTE TO WORK
    form = SongForm()
    # songs = Song.query.all()

    if form.validate_on_submit():
        title = request.form['title']
        artist = request.form['artist']
        new_song = Song(title=title, artist=artist)
        db.session.add(new_song)
        db.session.commit()
        return redirect("/songs")

    set_spotify_token(session)
    # test = my_spotify_client.search('all you need is love','track')
    res = my_spotify_client.get_track('68BTFws92cRztMS1oQ7Ewj')
    # data = res.json()
    # print('***************data**************')
    # print('***************data**************')
    # print('***************data**************')
    dataj = json.dumps(res)


    return render_template("song/new_song.html", form=form, dataj=dataj)
    
    # return render_template("song/new_song.html", form=form,test=json.dumps(test))



# @app.route("/playlists/<int:playlist_id>/add-song", methods=["GET", "POST"])
# def add_song_to_playlist(playlist_id):
#     """Add a playlist and redirect to list."""
    
#     playlist = Playlist.query.get_or_404(playlist_id)
#     form = NewSongForPlaylistForm()

#     # Restrict form to songs not already on this playlist

#     curr_on_playlist = [s.id for s in playlist.songs]
#     form.song.choices = (db.session.query(Song.id, Song.title).filter(Song.id.notin_(curr_on_playlist)).all())

#     if form.validate_on_submit():

#         # This is one way you could do this ...
#         playlist_song = PlaylistSong(song_id=form.song.data, playlist_id=playlist_id)
#         db.session.add(playlist_song)

#         # Here's another way you could that is slightly more ORM-ish:
#         #
#         # song = Song.query.get(form.song.data)
#         # playlist.songs.append(song)

#         # Either way, you have to commit:
#         db.session.commit()

#         return redirect(f"/playlists/{playlist_id}")

#     return render_template("song/add_song_to_playlist.html", playlist=playlist, form=form)


@app.route('/playlists/<int:playlist_id>/search', methods=["GET", "POST"])
def show_form(playlist_id):
    """Show form that searches new form, and show results"""
    playlist = Playlist.query.get(playlist_id)
    play_id  = playlist_id
    form = SearchSongsForm()
    resultsSong = []

    if form.validate_on_submit(): 
        # raise ('fu')
        track = form.track.data
        api_call_track = my_spotify_client.search(track,'track')   

        for item in api_call_track['tracks']['items']:
            images = [ image['url'] for image in item['album']['images'] ]
            artists = [ artist['name'] for artist in item['artists'] ]
            urls = item['album']['external_urls']['spotify']
            resultsSong.append({
                **pick(item,'name','id'),
                'album_name': item['album']['name'], 
                'album_image': first(images,''),
                'artists': artists,
                'url': urls
            })
        # raise('fu')
        # return redirect(f"/playlists/{play_id}/search")
        # return redirect('/playlists/<int:playlist_id>/search')

#     dataj = json.dumps(api_call_track)
#     print('dataj')
#     # print(dataj)
#     print(resultsSong)


        # new_playlist = Playlist(name=name, user_id=session['user_id'])
        # db.session.add(new_playlist)
        # db.session.commit()
        # playlists.append(new_playlist)



    return render_template('song/search_new_songs.html', playlist=playlist, form=form, resultsSong=resultsSong)


# @app.route('/playlists/<int:playlist_id>/search', methods=['GET'])
# def show_results(playlist_id):   
    # """Show form that searches new form, and show results"""
    # playlist = Playlist.query.get(playlist_id)
    # # form = PlaylistForm()
    # form = PlaylistForm(obj=playlist)
    # if form.validate_on_submit():
    #      return 'this'
    # else:
    #     return 'that'
    # raise ('fu')

    # resultsSong = []
    # if form.validate_on_submit():
    #     track = request.form['track']

    #     track = request.args.get['track']
    #     # print('here@@@@@@@@@')
    #     # print('track', track)
    #     api_call_track = my_spotify_client.search(track,'track')

    #     for item in api_call_track['tracks']['items']:
    #         images = [ image['url'] for image in item['album']['images'] ]
    #         artists = [ artist['name'] for artist in item['artists'] ]
    #         urls = item['album']['external_urls']['spotify']
    #         resultsSong.append({
    #             **pick(item,'name','id'),
    #             'album_name': item['album']['name'], 
    #             'album_image': first(images,''),
    #             'artists': artists,
    #             'url': urls
    #         })

    #     dataj = json.dumps(api_call_track)
    # print('dataj')
    # print(dataj)
    # print(resultsSong)

    # return render_template('song/search_new_songs.html', playlist=playlist, resultsSong=resultsSong)




# @app.route('/playlists/<int:playlist_id>/search', methods=["GET"])
# def search_new_songs(playlist_id):
    # """Show page that searches new songs"""

    # playlist = Playlist.query.get(playlist_id)
    # playlist = Playlist.query.get(playlist_id)
    # req = request.args
    # track = request.args['track']
    # print('here@@@@@@@@@')
    # print('track', track)
    # api_call_track = my_spotify_client.search(track,'track')
    # resultsSong = []

    # for item in api_call_track['tracks']['items']:
    #     images = [ image['url'] for image in item['album']['images'] ]
    #     artists = [ artist['name'] for artist in item['artists'] ]
    #     urls = item['album']['external_urls']['spotify']
    #     resultsSong.append({
    #         **pick(item,'name','id'),
    #         'album_name': item['album']['name'], 
    #         'album_image': first(images,''),
    #         'artists': artists,
    #         'url': urls
    #     })

    # dataj = json.dumps(api_call_track)
    # print('dataj')
    # print(dataj)
    # print(resultsSong)
    
    # return render_template('song/search_new_songs.html', playlist=playlist)


# @app.route('/playlists/<int:playlist_id>/see-songs-results', methods=["GET", "POST"])
# def see_songs_results(playlist_id):
#     playlist = Playlist.query.get(playlist_id)
#     # req = request.args
#     track = request.args['track']
#     # print('here@@@@@@@@@')
#     # print('track', track)
#     api_call_track = my_spotify_client.search(track,'track')
#     resultsSong = []

#     for item in api_call_track['tracks']['items']:
#         images = [ image['url'] for image in item['album']['images'] ]
#         artists = [ artist['name'] for artist in item['artists'] ]
#         urls = item['album']['external_urls']['spotify']
#         resultsSong.append({
#             **pick(item,'name','id'),
#             'album_name': item['album']['name'], 
#             'album_image': first(images,''),
#             'artists': artists,
#             'url': urls
#         })

#     dataj = json.dumps(api_call_track)
#     print('dataj')
#     # print(dataj)
#     print(resultsSong)

#     return render_template('song/see_songs_results.html', playlist=playlist, resultsSong=resultsSong)


# @app.route('/playlists/<int:playlist_id>/see-artists-results', methods=["GET", "POST"])
# def see_artists_results(playlist_id):
#     playlist = Playlist.query.get(playlist_id)
#     return render_template('song/see_artists_results.html', playlist=playlist)


@app.route("/playlists/<int:playlist_id>/update", methods=["GET", "POST"])
def update_playlist(playlist_id):
    """Show update-feedback form and process it."""

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
