#!/bin/bash

# Bark TTS API test script for expressive speech
API_URL="http://localhost:5002/api/tts/bark"

# Array of test cases: (filename, text, emotion)
declare -a tests=(
  "bark_whisper.wav|This is a secret, please keep it quiet. [whisper]|neutral"
  "bark_singing.wav|Happy birthday to you, happy birthday to you! [singing]|neutral"
  "bark_laughter.wav|That was so funny! [laughs]|neutral"
  "bark_sad.wav|I'm sorry, I can't make it today.|sad"
  "bark_angry.wav|Why did you do that?!|angry"
  "bark_excited.wav|I can't believe we won!|happy"
  "bark_surprised.wav|Oh! I didn't see you there!|surprised"
  "bark_fearful.wav|Did you hear that noise in the dark?|fearful"
  "bark_story.wav|Once upon a time, in a land far away, there lived a wise old owl.|neutral"
  "bark_music.wav|Let's enjoy some music together. [music]|neutral"
)

echo "Testing Bark TTS expressive capabilities..."

for test in "${tests[@]}"; do
  IFS='|' read -r filename text emotion <<< "$test"
  echo "Generating: $filename (emotion: $emotion)"
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$text\", \"emotion\": \"$emotion\"}" \
    -o "$filename"
  if [ $? -eq 0 ]; then
    echo "Saved $filename"
  else
    echo "Failed to generate $filename"
  fi
done

echo "All Bark TTS test samples generated." 