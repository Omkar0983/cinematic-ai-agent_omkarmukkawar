import openai
from typing import Optional
from models.schemas import VideoPlan, Scene, AudioAnalysis
import librosa
import numpy as np
from enum import Enum

class Mood(Enum):
    CINEMATIC = "cinematic"
    DRAMATIC = "dramatic"
    EMOTIONAL = "emotional"
    ENERGETIC = "energetic"
    CALM = "calm"

class AIOrchestrator:
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or "your-openai-key")
        
    async def generate_cinematic_plan(
        self,
        description: str,
        mood: str = "cinematic",
        audio_path: Optional[str] = None
    ) -> VideoPlan:
        """Generate comprehensive cinematic plan"""
        
        # Analyze audio if provided
        audio_analysis = None
        if audio_path:
            audio_analysis = await self._analyze_audio(audio_path)
        
        # Generate plan using AI
        prompt = self._build_prompt(description, mood, audio_analysis)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional cinematic director and video editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        plan_content = response.choices[0].message.content
        
        # Parse AI response into structured plan
        plan = self._parse_ai_response(plan_content, audio_analysis)
        
        return plan
    
    async def _analyze_audio(self, audio_path: str) -> AudioAnalysis:
        """Analyze audio file for beats, tempo, and mood"""
        y, sr = librosa.load(audio_path)
        
        # Extract features
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beats_times = librosa.frames_to_time(beats, sr=sr)
        
        # Analyze mood from audio features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        
        mood = self._detect_audio_mood(y, sr)
        
        return AudioAnalysis(
            tempo=float(tempo),
            beats=beats_times.tolist(),
            mood=mood,
            duration=librosa.get_duration(y=y, sr=sr)
        )
    
    def _detect_audio_mood(self, y, sr) -> str:
        """Simple audio mood detection"""
        # Implement mood detection logic
        # This is a simplified version
        energy = np.mean(librosa.feature.rms(y=y))
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        if tempo > 120 and energy > 0.1:
            return "energetic"
        elif tempo < 80 and energy < 0.05:
            return "calm"
        else:
            return "emotional"
    
    def _build_prompt(self, description: str, mood: str, audio_analysis: Optional[AudioAnalysis]) -> str:
        """Build AI prompt for cinematic planning"""
        prompt = f"""
        Create a cinematic video plan based on:
        
        DESCRIPTION: {description}
        MOOD: {mood}
        
        Requirements:
        1. Aspect Ratio: 16:9
        2. Include cinematic effects: slow motion, depth of field, light flares, film grain
        3. Dynamic camera movements
        4. Smooth transitions
        5. Color grading appropriate for mood
        
        """
        
        if audio_analysis:
            prompt += f"""
            AUDIO ANALYSIS:
            - Tempo: {audio_analysis.tempo} BPM
            - Mood: {audio_analysis.mood}
            - Duration: {audio_analysis.duration}s
            - Sync video transitions with audio beats
            
            """
        
        prompt += """
        Output format (JSON):
        {
            "title": "Video Title",
            "total_duration": 60,
            "mood": "cinematic",
            "color_palette": ["#color1", "#color2"],
            "scenes": [
                {
                    "scene_number": 1,
                    "duration": 8,
                    "description": "Scene description",
                    "camera_movement": "slow push-in",
                    "visual_style": "wide shot, golden hour",
                    "effects": ["light flare", "film grain"],
                    "transition": "fade from black"
                }
            ],
            "cinematic_effects": {
                "color_grading": "teal and orange",
                "film_grain": "subtle",
                "lens_flares": true,
                "slow_motion": ["scene_3", "scene_5"]
            }
        }
        """
        
        return prompt
    
    def _parse_ai_response(self, response: str, audio_analysis: Optional[AudioAnalysis]) -> VideoPlan:
        """Parse AI response into VideoPlan object"""
        # Extract JSON from response
        import re
        import json
        
        # Find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group())
        else:
            # Fallback to basic structure
            plan_data = {
                "title": "Cinematic Video",
                "total_duration": 60,
                "mood": "cinematic",
                "scenes": []
            }
        
        return VideoPlan(**plan_data)
