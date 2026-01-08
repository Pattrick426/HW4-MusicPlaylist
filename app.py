import os
import base64
import streamlit as st

# ----------------------------
# Upload
# ----------------------------
UPLOAD_DIR = "uploads"

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file) -> str:
    """
    Save Streamlit uploaded file into uploads/ and return the saved path.
    If filename exists, auto add _1, _2, ...
    """
    ensure_upload_dir()
    filename = uploaded_file.name
    base, ext = os.path.splitext(filename)

    dest_path = os.path.join(UPLOAD_DIR, filename)
    i = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(UPLOAD_DIR, f"{base}_{i}{ext}")
        i += 1

    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return dest_path

def is_video(path: str) -> bool:
    return os.path.splitext(path.lower())[1] in [".mp4", ".mov", ".mkv", ".webm"]

def is_audio(path: str) -> bool:
    return os.path.splitext(path.lower())[1] in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]


# ----------------------------
# Song Class
# ----------------------------
class Song:
    def __init__(self, title, artist, audio_file):
        self.title = title
        self.artist = artist
        self.audio_file = audio_file  # path ที่เซฟไว้ใน uploads/
        self.next_song = None

    def __str__(self):
        return f"{self.title} by {self.artist}"


# ----------------------------
# MusicPlaylist Class
# ----------------------------
class MusicPlaylist:
    def __init__(self):
        self.head = None
        self.current_song = None
        self.length = 0

    def add_song(self, title, artist, audio_file):
        new_song = Song(title, artist, audio_file)
        if self.head is None:
            self.head = new_song
            self.current_song = new_song
        else:
            current = self.head
            while current.next_song:
                current = current.next_song
            current.next_song = new_song
        self.length += 1
        st.success(f"Added: {new_song}")

    def display_playlist(self):
        if self.head is None:
            return []

        playlist_songs = []
        current = self.head
        count = 1
        while current:
            # เพิ่มข้อมูลไฟล์ให้ดูง่าย
            ext = os.path.splitext(current.audio_file)[1]
            marker = "▶️ " if current == self.current_song else ""
            playlist_songs.append(f"{marker}{count}. {current.title} by {current.artist} ({ext})")
            current = current.next_song
            count += 1
        return playlist_songs

    def play_current_song(self):
        if not self.current_song:
            st.warning("Playlist is empty or no song is selected to play.")
            return

        st.info(f"Now playing: {self.current_song}")

        path = self.current_song.audio_file
        if not os.path.exists(path):
            st.error(f"File not found: {path}")
            return

        # เล่นตามชนิดไฟล์
        if is_video(path):
            with open(path, "rb") as f:
                st.video(f.read())
        elif is_audio(path):
            with open(path, "rb") as f:
                st.audio(f.read())
        else:
            st.warning("This file type is not supported for playback in this app.")
            st.write(f"File: {path}")

    def next_song(self):
        if self.current_song and self.current_song.next_song:
            self.current_song = self.current_song.next_song
        elif self.current_song and not self.current_song.next_song:
            st.warning("End of playlist. No next song.")
        else:
            st.warning("Playlist is empty.")

    def prev_song(self):
        if self.head is None or self.current_song is None:
            st.warning("Playlist is empty or no song is selected.")
            return
        if self.current_song == self.head:
            st.warning("Already at the beginning of the playlist.")
            return

        current = self.head
        while current.next_song != self.current_song:
            current = current.next_song
        self.current_song = current

    def get_length(self):
        return self.length

    def delete_song(self, title):
        if self.head is None:
            st.error(f"Cannot delete '{title}'. Playlist is empty.")
            return

        # ลบหัว
        if self.head.title == title:
            # ถ้ากำลังเล่นเพลงหัวอยู่ ให้เลื่อนไปเพลงถัดไป
            if self.current_song == self.head:
                self.current_song = self.head.next_song
            self.head = self.head.next_song
            self.length -= 1
            st.success(f"Deleted: {title}")
            if self.length == 0:
                self.current_song = None
            return

        current = self.head
        prev = None
        while current and current.title != title:
            prev = current
            current = current.next_song

        if current:
            if self.current_song == current:
                if current.next_song:
                    self.current_song = current.next_song
                elif prev:
                    self.current_song = prev
                else:
                    self.current_song = None

            prev.next_song = current.next_song
            self.length -= 1
            st.success(f"Deleted: {title}")
        else:
            st.error(f"Song '{title}' not found in the playlist.")


# ----------------------------
# Streamlit App Layout
# ----------------------------
st.title("🎶 Music / Video Playlist App (Linked List)")

# Init playlist in session state
if "playlist" not in st.session_state:
    st.session_state.playlist = MusicPlaylist()

# -------- Sidebar: Upload +
st.sidebar.header("Upload & Add (mp3 / wav / m4a / mp4)")
new_title = st.sidebar.text_input("Title")
new_artist = st.sidebar.text_input("Artist")
uploaded_file = st.sidebar.file_uploader(
    "Choose a file",
    type=["mp3", "wav", "m4a", "aac", "ogg", "mp4", "mov", "mkv", "webm"]
)

if st.sidebar.button("Add to Playlist"):
    if not new_title or not new_artist:
        st.sidebar.warning("Please enter both title and artist.")
    elif uploaded_file is None:
        st.sidebar.warning("Please choose a file to upload.")
    else:
        saved_path = save_uploaded_file(uploaded_file)
        st.session_state.playlist.add_song(new_title, new_artist, saved_path)

st.sidebar.markdown("--- 🎶")
st.sidebar.header("Delete Song")
delete_title = st.sidebar.text_input("Song Title to Delete")
if st.sidebar.button("Delete Song"):
    if delete_title:
        st.session_state.playlist.delete_song(delete_title)
    else:
        st.sidebar.warning("Please enter a song title to delete.")

# -------- Main: Playlist
st.header("Your Current Playlist")
playlist_content = st.session_state.playlist.display_playlist()
if playlist_content:
    for song_str in playlist_content:
        st.write(song_str)
else:
    st.write("Playlist is empty. Upload and add a file from the sidebar!")

# -------- Controls
("--- 🎶")
st.header("Playback Controls")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⏪ Previous"):
        st.session_state.playlist.prev_song()
        st.session_state.playlist.play_current_song()

with col2:
    if st.button("▶️ Play Current"):
        st.session_state.playlist.play_current_song()

with col3:
    if st.button("⏩ Next"):
        st.session_state.playlist.next_song()
        st.session_state.playlist.play_current_song()

st.markdown("--- 🎶")
st.write(f"Total items in playlist: {st.session_state.playlist.get_length()} item(s)")
