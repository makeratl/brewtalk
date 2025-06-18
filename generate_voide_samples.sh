#!/bin/bash

# Test voices
voices=("p225" "p228" "p230" "p262" "p270")

for voice in "${voices[@]}"; do
    echo "Generating sample for $voice..."
    curl -X POST http://localhost:5002/api/tts \
         -H "Content-Type: application/json" \
         -d "{\"text\": \"This is a voice test for speaker $voice\", \"speaker_id\": \"$voice\"}" \
         -o "${voice}_sample.wav"
done

echo "Voice samples generated:"
ls -l *_sample.wav