export interface TextToSpeechParams {
  text: string;
  speaker_id?: string;
  language_id?: string;
}

export async function textToSpeech(params: TextToSpeechParams): Promise<Blob> {
  try {
    const response = await fetch('http://localhost:5002/api/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: params.text,
        speaker_id: params.speaker_id || 'p225', // Default to p225 if not provided
        language_id: params.language_id || ''
      })
    });
    
    if (!response.ok) {
      throw new Error('Local TTS generation failed');
    }
    
    // Return the audio data as a Blob
    return await response.blob();
  } catch (error) {
    console.error('Error converting text to speech:', error);
    throw error;
  }
} 