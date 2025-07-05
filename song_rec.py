import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random

# Configure the page
st.set_page_config(
    page_title="🎵 AI Song Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBlp6DhofApS6lNBd1fLOznPI7gbYh8uik"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
@st.cache_resource
def initialize_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = initialize_model()

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .recommendation-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
    }
    
    .song-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 3px solid #764ba2;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stSelectbox > div > div {
        background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 10px;
    }
    
    .stSlider > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def get_song_recommendations(prompt, num_songs=10):
    """Get song recommendations from Gemini API"""
    try:
        full_prompt = f"""
        You are an expert music curator and recommendation system. Based on the following request, provide exactly {num_songs} song recommendations.
        
        Request: {prompt}
        
        Please provide your response in the following JSON format:
        {{
            "recommendations": [
                {{
                    "song_title": "Song Name",
                    "artist": "Artist Name",
                    "album": "Album Name",
                    "genre": "Genre",
                    "year": "Year",
                    "mood": "Mood/Vibe",
                    "reason": "Why this song fits the request",
                    "similarity_score": 0.95
                }}
            ]
        }}
        
        Make sure to include diverse but relevant songs. Each song should have a similarity score between 0.7 and 1.0.
        """
        
        response = model.generate_content(full_prompt)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response
            response_text = response.text
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text
            
            recommendations = json.loads(json_text)
            return recommendations
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response from text
            return parse_text_response(response.text, num_songs)
            
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return None

def parse_text_response(text, num_songs):
    """Parse text response and convert to structured format"""
    lines = text.split('\n')
    recommendations = []
    
    current_song = {}
    for line in lines:
        if '**' in line or any(keyword in line.lower() for keyword in ['song:', 'title:', 'artist:', 'album:']):
            if current_song and 'song_title' in current_song:
                recommendations.append(current_song)
                current_song = {}
            
            # Extract song information
            if 'song:' in line.lower() or 'title:' in line.lower():
                current_song['song_title'] = line.split(':')[-1].strip().replace('*', '')
            elif 'artist:' in line.lower():
                current_song['artist'] = line.split(':')[-1].strip().replace('*', '')
            elif 'album:' in line.lower():
                current_song['album'] = line.split(':')[-1].strip().replace('*', '')
            elif 'genre:' in line.lower():
                current_song['genre'] = line.split(':')[-1].strip().replace('*', '')
            elif 'year:' in line.lower():
                current_song['year'] = line.split(':')[-1].strip().replace('*', '')
            elif 'mood:' in line.lower():
                current_song['mood'] = line.split(':')[-1].strip().replace('*', '')
            elif 'reason:' in line.lower():
                current_song['reason'] = line.split(':')[-1].strip().replace('*', '')
    
    # Add the last song if exists
    if current_song and 'song_title' in current_song:
        recommendations.append(current_song)
    
    # Fill in missing fields and add similarity scores
    for i, rec in enumerate(recommendations):
        if 'artist' not in rec:
            rec['artist'] = 'Unknown Artist'
        if 'album' not in rec:
            rec['album'] = 'Unknown Album'
        if 'genre' not in rec:
            rec['genre'] = 'Various'
        if 'year' not in rec:
            rec['year'] = 'Unknown'
        if 'mood' not in rec:
            rec['mood'] = 'Various'
        if 'reason' not in rec:
            rec['reason'] = 'Recommended based on your preferences'
        rec['similarity_score'] = round(random.uniform(0.8, 0.98), 2)
    
    return {"recommendations": recommendations[:num_songs]}

def display_recommendations(recommendations):
    """Display recommendations in a beautiful format"""
    if not recommendations or 'recommendations' not in recommendations:
        st.error("No recommendations found.")
        return
    
    songs = recommendations['recommendations']
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎵 Total Songs</h3>
            <h2>{len(songs)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_score = sum(song.get('similarity_score', 0.8) for song in songs) / len(songs)
        st.markdown(f"""
        <div class="metric-card">
            <h3>⭐ Avg Match</h3>
            <h2>{avg_score:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        genres = list(set(song.get('genre', 'Various') for song in songs))
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎼 Genres</h3>
            <h2>{len(genres)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        moods = list(set(song.get('mood', 'Various') for song in songs))
        st.markdown(f"""
        <div class="metric-card">
            <h3>😊 Moods</h3>
            <h2>{len(moods)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Display individual songs
    st.markdown("### 🎵 Your Personalized Recommendations")
    
    for i, song in enumerate(songs, 1):
        similarity = song.get('similarity_score', 0.8)
        
        # Create progress bar for similarity
        progress_color = "🟢" if similarity > 0.9 else "🟡" if similarity > 0.8 else "🔴"
        
        st.markdown(f"""
        <div class="song-item">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>🎵 {song.get('song_title', 'Unknown Song')}</h4>
                    <p><strong>🎤 Artist:</strong> {song.get('artist', 'Unknown')}</p>
                    <p><strong>💿 Album:</strong> {song.get('album', 'Unknown')}</p>
                    <p><strong>🎼 Genre:</strong> {song.get('genre', 'Various')} | <strong>📅 Year:</strong> {song.get('year', 'Unknown')}</p>
                    <p><strong>😊 Mood:</strong> {song.get('mood', 'Various')}</p>
                    <p><strong>💡 Why recommended:</strong> {song.get('reason', 'Based on your preferences')}</p>
                </div>
                <div style="text-align: right;">
                    <h3>{progress_color}</h3>
                    <p><strong>Match: {similarity:.1%}</strong></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Create visualization
    create_recommendation_charts(songs)

def create_recommendation_charts(songs):
    """Create beautiful charts for recommendations"""
    if not songs:
        return
    
    # Genre distribution
    genre_counts = {}
    mood_counts = {}
    
    for song in songs:
        genre = song.get('genre', 'Various')
        mood = song.get('mood', 'Various')
        
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        if genre_counts:
            fig_genre = px.pie(
                values=list(genre_counts.values()),
                names=list(genre_counts.keys()),
                title="🎼 Genre Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_genre.update_layout(
                title_font_size=20,
                font=dict(size=12),
                showlegend=True
            )
            st.plotly_chart(fig_genre, use_container_width=True)
    
    with col2:
        if mood_counts:
            fig_mood = px.bar(
                x=list(mood_counts.keys()),
                y=list(mood_counts.values()),
                title="😊 Mood Distribution",
                color=list(mood_counts.values()),
                color_continuous_scale="viridis"
            )
            fig_mood.update_layout(
                title_font_size=20,
                font=dict(size=12),
                xaxis_title="Mood",
                yaxis_title="Number of Songs"
            )
            st.plotly_chart(fig_mood, use_container_width=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎵 AI-Powered Song Recommender</h1>
        <p>Discover your next favorite song with AI-powered recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-info">
            <h3>🎵 Welcome to AI Song Recommender!</h3>
            <p>Get personalized music recommendations powered by Google's Gemini AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendation mode selection
        st.markdown("### 🎵 Choose Recommendation Mode")
        mode = st.selectbox(
            "Select your preferred recommendation style:",
            ["🎼 Genre Based", "😊 Mood Based", "👤 Artist Similar", "🎯 Custom Preferences"],
            index=0
        )
        
        # Number of recommendations
        num_songs = st.slider("Number of songs", 5, 20, 10)
        
        st.markdown("---")
        st.markdown("### 🎵 Quick Stats")
        st.info("AI-powered recommendations using Google Gemini")
        st.success("Real-time music discovery")
        st.warning("Personalized just for you!")
    
    # Main content area
    if mode == "🎼 Genre Based":
        st.markdown("### 🎼 Genre-Based Recommendations")
        
        col1, col2 = st.columns(2)
        with col1:
            primary_genre = st.selectbox(
                "Primary Genre",
                ["Pop", "Rock", "Hip-Hop", "R&B", "Country", "Electronic", "Jazz", "Classical", "Indie", "Alternative"]
            )
        
        with col2:
            secondary_genre = st.selectbox(
                "Secondary Genre (Optional)",
                ["None", "Pop", "Rock", "Hip-Hop", "R&B", "Country", "Electronic", "Jazz", "Classical", "Indie", "Alternative"]
            )
        
        decade = st.selectbox(
            "Preferred Decade",
            ["Any", "2020s", "2010s", "2000s", "1990s", "1980s", "1970s", "1960s", "Earlier"]
        )
        
        if st.button("🎵 Get Genre Recommendations", type="primary"):
            prompt = f"Recommend songs in the {primary_genre} genre"
            if secondary_genre != "None":
                prompt += f" with influences from {secondary_genre}"
            if decade != "Any":
                prompt += f" from the {decade}"
            
            with st.spinner("🎵 Discovering amazing songs for you..."):
                recommendations = get_song_recommendations(prompt, num_songs)
                if recommendations:
                    display_recommendations(recommendations)
    
    elif mode == "😊 Mood Based":
        st.markdown("### 😊 Mood-Based Recommendations")
        
        col1, col2 = st.columns(2)
        with col1:
            mood = st.selectbox(
                "Current Mood",
                ["Happy", "Sad", "Energetic", "Calm", "Romantic", "Motivational", "Nostalgic", "Chill", "Party", "Relaxed"]
            )
        
        with col2:
            activity = st.selectbox(
                "Activity",
                ["Just Listening", "Working", "Exercising", "Studying", "Driving", "Cooking", "Sleeping", "Dancing", "Reading"]
            )
        
        energy_level = st.slider("Energy Level", 1, 10, 5)
        
        if st.button("😊 Get Mood Recommendations", type="primary"):
            prompt = f"Recommend songs for someone feeling {mood.lower()} while {activity.lower()} with energy level {energy_level}/10"
            
            with st.spinner("😊 Finding the perfect mood music..."):
                recommendations = get_song_recommendations(prompt, num_songs)
                if recommendations:
                    display_recommendations(recommendations)
    
    elif mode == "👤 Artist Similar":
        st.markdown("### 👤 Artist Similarity Recommendations")
        
        favorite_artists = st.text_input(
            "Enter your favorite artists (comma-separated)",
            placeholder="e.g., Taylor Swift, Ed Sheeran, Billie Eilish"
        )
        
        similarity_type = st.selectbox(
            "Similarity Type",
            ["Vocal Style", "Musical Style", "Genre", "Era", "Popularity", "Lyrics Theme"]
        )
        
        if st.button("👤 Get Similar Artist Recommendations", type="primary") and favorite_artists:
            prompt = f"Recommend songs by artists similar to {favorite_artists} in terms of {similarity_type.lower()}"
            
            with st.spinner("👤 Finding artists you'll love..."):
                recommendations = get_song_recommendations(prompt, num_songs)
                if recommendations:
                    display_recommendations(recommendations)
    
    elif mode == "🎯 Custom Preferences":
        st.markdown("### 🎯 Custom Preferences")
        
        custom_prompt = st.text_area(
            "Describe what you're looking for",
            placeholder="e.g., 'Songs with powerful vocals and emotional lyrics that make you feel empowered'",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox(
                "Language Preference",
                ["Any", "English", "Spanish", "French", "Japanese", "Korean", "Hindi", "Other"]
            )
        
        with col2:
            tempo = st.selectbox(
                "Tempo Preference",
                ["Any", "Slow", "Medium", "Fast", "Very Fast"]
            )
        
        if st.button("🎯 Get Custom Recommendations", type="primary") and custom_prompt:
            prompt = custom_prompt
            if language != "Any":
                prompt += f" in {language}"
            if tempo != "Any":
                prompt += f" with {tempo.lower()} tempo"
            
            with st.spinner("🎯 Crafting personalized recommendations..."):
                recommendations = get_song_recommendations(prompt, num_songs)
                if recommendations:
                    display_recommendations(recommendations)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎵 Made with ❤️ using Streamlit and Google Gemini AI</p>
        <p>Discover new music • Find your vibe • Expand your playlist</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
